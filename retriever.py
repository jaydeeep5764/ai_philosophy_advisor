from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from agents.philosopher_profiles import PhilosopherProfile
from ingest import CHROMA_PATH, COLLECTION_NAME
from utils.llm import generate_embedding


LEXICAL_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "too",
    "what",
    "when",
    "with",
}


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    philosopher: str
    book: str
    section: str
    theme: str
    source_id: str

    @property
    def citation(self) -> str:
        return f"{self.book}, {self.section}"


@dataclass(frozen=True)
class RetrievedContext:
    text: str
    sources: tuple[str, ...]

    @property
    def has_context(self) -> bool:
        return bool(self.text.strip())


def _empty_context() -> RetrievedContext:
    return RetrievedContext(text="", sources=())


def _get_collection():
    try:
        import chromadb
    except ImportError:
        return None

    if not Path(CHROMA_PATH).exists():
        return None

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return None

    try:
        if collection.count() == 0:
            return None
    except Exception:
        return None

    return collection


def _query_for_philosopher(
    collection,
    question: str,
    philosopher_name: str,
    max_chunks: int,
) -> list[RetrievedChunk]:
    query_embedding = generate_embedding(question, task_type="retrieval_query")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=max_chunks,
        where={"philosopher": philosopher_name},
        include=["documents", "metadatas"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    chunks: list[RetrievedChunk] = []
    for document, metadata in zip(documents, metadatas):
        chunks.append(
            RetrievedChunk(
                text=document,
                philosopher=str(metadata.get("philosopher", philosopher_name)),
                book=str(metadata.get("book", "")),
                section=str(metadata.get("section", "")),
                theme=str(metadata.get("theme", "")),
                source_id=str(metadata.get("source_id", "")),
            )
        )
    return chunks


def _all_chunks_for_philosopher(collection, philosopher_name: str) -> list[RetrievedChunk]:
    results = collection.get(
        where={"philosopher": philosopher_name},
        include=["documents", "metadatas"],
    )
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    return [
        RetrievedChunk(
            text=document,
            philosopher=str(metadata.get("philosopher", philosopher_name)),
            book=str(metadata.get("book", "")),
            section=str(metadata.get("section", "")),
            theme=str(metadata.get("theme", "")),
            source_id=str(metadata.get("source_id", "")),
        )
        for document, metadata in zip(documents, metadatas)
    ]


def _lexical_terms(text: str) -> set[str]:
    terms = {
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9_'-]*", text.casefold())
        if term not in LEXICAL_STOPWORDS
    }
    expanded = set(terms)
    for term in terms:
        if term.endswith("s") and len(term) > 3:
            expanded.add(term[:-1])
    return expanded


def _lexical_score(question: str, chunk: RetrievedChunk) -> int:
    query_terms = _lexical_terms(question)
    if not query_terms:
        return 0

    theme_terms = _lexical_terms(chunk.theme)
    text_terms = _lexical_terms(chunk.text)
    theme_matches = len(query_terms & theme_terms)
    text_matches = len(query_terms & text_terms)
    return theme_matches * 4 + text_matches


def _hybrid_chunks_for_philosopher(
    collection,
    question: str,
    philosopher_name: str,
    max_chunks: int,
) -> list[RetrievedChunk]:
    semantic_chunks = _query_for_philosopher(
        collection,
        question,
        philosopher_name,
        max(max_chunks * 3, max_chunks),
    )
    lexical_chunks = sorted(
        _all_chunks_for_philosopher(collection, philosopher_name),
        key=lambda chunk: (_lexical_score(question, chunk), chunk.theme),
        reverse=True,
    )

    ranked: list[RetrievedChunk] = []
    seen_ids: set[str] = set()
    for chunk in lexical_chunks:
        if _lexical_score(question, chunk) <= 0:
            break
        if chunk.source_id not in seen_ids:
            ranked.append(chunk)
            seen_ids.add(chunk.source_id)
        if len(ranked) >= max_chunks:
            break

    min_semantic_slots = max(1, max_chunks // 3)
    semantic_limit = max_chunks if len(ranked) < min_semantic_slots else len(ranked)
    for chunk in semantic_chunks:
        if chunk.source_id not in seen_ids:
            ranked.append(chunk)
            seen_ids.add(chunk.source_id)
        if len(ranked) >= semantic_limit:
            break

    return ranked


def retrieve_context(
    question: str,
    profiles: list[PhilosopherProfile],
    max_chunks: int = 4,
) -> RetrievedContext:
    collection = _get_collection()
    if collection is None:
        return _empty_context()

    selected_chunks: list[RetrievedChunk] = []
    seen_ids: set[str] = set()
    per_philosopher_limit = max(1, max_chunks // max(1, len(profiles)))

    for profile in profiles:
        for chunk in _hybrid_chunks_for_philosopher(
            collection,
            question,
            profile.name,
            per_philosopher_limit,
        ):
            if chunk.source_id not in seen_ids:
                selected_chunks.append(chunk)
                seen_ids.add(chunk.source_id)

    selected_chunks = selected_chunks[:max_chunks]
    sources = tuple(dict.fromkeys(chunk.citation for chunk in selected_chunks))
    context_blocks = [
        (
            f"Retrieved passage theme: {chunk.theme}\n"
            f"{chunk.text}"
        )
        for chunk in selected_chunks
    ]
    return RetrievedContext(text="\n\n".join(context_blocks), sources=sources)
