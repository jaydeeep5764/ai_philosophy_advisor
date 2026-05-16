from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from agents.philosopher_profiles import PhilosopherProfile


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"
TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z-]{2,}")
STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "also",
    "and",
    "are",
    "because",
    "before",
    "between",
    "but",
    "can",
    "could",
    "does",
    "for",
    "from",
    "have",
    "how",
    "into",
    "just",
    "more",
    "not",
    "one",
    "only",
    "our",
    "should",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "through",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "you",
    "your",
}


@dataclass(frozen=True)
class KnowledgeDocument:
    source_id: str
    title: str
    tradition: str
    school: str
    tags: tuple[str, ...]
    content: str


@dataclass(frozen=True)
class KnowledgeChunk:
    source_id: str
    title: str
    tradition: str
    school: str
    tags: tuple[str, ...]
    heading: str
    content: str


@dataclass(frozen=True)
class RetrievedContext:
    text: str
    sources: tuple[str, ...]

    @property
    def has_context(self) -> bool:
        return bool(self.text.strip())


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_PATTERN.findall(text)
        if token.lower() not in STOPWORDS
    }


def _parse_metadata(lines: list[str]) -> tuple[str, str, tuple[str, ...], list[str]]:
    metadata: dict[str, str] = {}
    content_start = 0
    for index, line in enumerate(lines):
        if not line.strip():
            content_start = index + 1
            break
        if ":" not in line:
            content_start = index
            break
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()

    tags = tuple(tag.strip() for tag in metadata.get("tags", "").split(",") if tag.strip())
    return (
        metadata.get("tradition", ""),
        metadata.get("school", ""),
        tags,
        lines[content_start:],
    )


def _load_document(path: Path) -> KnowledgeDocument:
    raw = path.read_text(encoding="utf-8").strip()
    lines = raw.splitlines()
    title = path.stem.replace("_", " ").title()
    if lines and lines[0].startswith("# "):
        title = lines[0].removeprefix("# ").strip()
        lines = lines[1:]

    tradition, school, tags, body_lines = _parse_metadata(lines)
    return KnowledgeDocument(
        source_id=path.name,
        title=title,
        tradition=tradition,
        school=school,
        tags=tags,
        content="\n".join(body_lines).strip(),
    )


def _chunk_document(document: KnowledgeDocument) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    current_heading = "Overview"
    current_lines: list[str] = []

    def flush() -> None:
        content = "\n".join(current_lines).strip()
        if content:
            chunks.append(
                KnowledgeChunk(
                    source_id=document.source_id,
                    title=document.title,
                    tradition=document.tradition,
                    school=document.school,
                    tags=document.tags,
                    heading=current_heading,
                    content=content,
                )
            )

    for line in document.content.splitlines():
        if line.startswith("## "):
            flush()
            current_heading = line.removeprefix("## ").strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()
    return chunks


@lru_cache(maxsize=1)
def load_knowledge_chunks() -> tuple[KnowledgeChunk, ...]:
    if not KNOWLEDGE_DIR.exists():
        return ()

    chunks: list[KnowledgeChunk] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        chunks.extend(_chunk_document(_load_document(path)))
    return tuple(chunks)


def _profile_terms(profile: PhilosopherProfile) -> set[str]:
    text = " ".join(
        (
            profile.name,
            profile.tradition,
            profile.school,
            profile.era,
            profile.region,
            " ".join(profile.source_tags),
            profile.core_worldview,
        )
    )
    return _tokens(text)


def retrieve_context(
    question: str,
    profiles: list[PhilosopherProfile],
    max_chunks: int = 4,
) -> RetrievedContext:
    query_terms = _tokens(question)
    profile_terms = set().union(*(_profile_terms(profile) for profile in profiles))
    scored_chunks: list[tuple[int, KnowledgeChunk]] = []

    for chunk in load_knowledge_chunks():
        chunk_text = " ".join(
            (
                chunk.title,
                chunk.tradition,
                chunk.school,
                " ".join(chunk.tags),
                chunk.heading,
                chunk.content,
            )
        )
        chunk_terms = _tokens(chunk_text)
        query_overlap = len(query_terms & chunk_terms)
        profile_overlap = len(profile_terms & chunk_terms)
        tag_overlap = len(profile_terms & _tokens(" ".join(chunk.tags)))
        score = (query_overlap * 3) + (profile_overlap * 2) + (tag_overlap * 4)
        if score > 0:
            scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    selected = [chunk for _, chunk in scored_chunks[:max_chunks]]
    sources = tuple(dict.fromkeys(f"{chunk.title} ({chunk.source_id})" for chunk in selected))
    context_blocks = [
        (
            f"[Source: {chunk.title} | {chunk.source_id} | {chunk.school}]\n"
            f"Section: {chunk.heading}\n"
            f"{chunk.content}"
        )
        for chunk in selected
    ]
    return RetrievedContext(text="\n\n".join(context_blocks), sources=sources)
