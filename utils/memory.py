from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


MAX_MEMORY_ITEMS = 8
MAX_RESPONSE_PREVIEW_CHARS = 700


@dataclass(frozen=True)
class MemoryEntry:
    mode: str
    question: str
    philosophers: tuple[str, ...]
    answer_preview: str
    created_at: str


def create_memory_entry(
    mode: str,
    question: str,
    philosophers: list[str] | tuple[str, ...],
    answer: str,
) -> dict[str, object]:
    return {
        "mode": mode,
        "question": question.strip(),
        "philosophers": tuple(philosophers),
        "answer_preview": _preview(answer),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def append_memory_entry(history: list[dict[str, object]], entry: dict[str, object]) -> list[dict[str, object]]:
    updated = [*history, entry]
    return updated[-MAX_MEMORY_ITEMS:]


def build_memory_context(history: list[dict[str, object]]) -> str:
    if not history:
        return "No prior conversation memory in this session."

    lines = ["Prior session memory. Use only when relevant to the user's current question:"]
    for index, entry in enumerate(history[-MAX_MEMORY_ITEMS:], start=1):
        philosophers = ", ".join(entry.get("philosophers", ()))
        lines.append(
            "\n".join(
                (
                    f"{index}. Mode: {entry.get('mode', '')}",
                    f"Question: {entry.get('question', '')}",
                    f"Philosophers: {philosophers}",
                    f"Previous answer gist: {entry.get('answer_preview', '')}",
                )
            )
        )
    return "\n\n".join(lines)


def _preview(answer: str) -> str:
    compact = " ".join(answer.split())
    if len(compact) <= MAX_RESPONSE_PREVIEW_CHARS:
        return compact
    return compact[:MAX_RESPONSE_PREVIEW_CHARS].rstrip() + "..."
