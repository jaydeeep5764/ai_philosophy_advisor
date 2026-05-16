from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agents.philosopher_profiles import PhilosopherProfile
from ingest import CHROMA_PATH, COLLECTION_NAME
from utils.llm import generate_embedding


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
        for chunk in _query_for_philosopher(collection, question, profile.name, per_philosopher_limit):
            if chunk.source_id not in seen_ids:
                selected_chunks.append(chunk)
                seen_ids.add(chunk.source_id)

    selected_chunks = selected_chunks[:max_chunks]
    sources = tuple(dict.fromkeys(chunk.citation for chunk in selected_chunks))
    context_blocks = [
        (
            f"[Citation: {chunk.citation} | Theme: {chunk.theme} | ID: {chunk.source_id}]\n"
            f"{chunk.text}"
        )
        for chunk in selected_chunks
    ]
    return RetrievedContext(text="\n\n".join(context_blocks), sources=sources)
