from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agents.philosopher_profiles import PHILOSOPHER_PROFILES


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DATA_GLOB = "*.json"
CHROMA_PATH = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "philosophy_council_sources"
REQUIRED_FIELDS = {"id", "philosopher", "book", "section", "theme", "text"}
CHANAKYA_FIELDS = {"id", "section", "subsection", "title", "principle", "elaboration", "source"}
DOSSIER_LIST_FIELDS = (
    "core_philosophy",
    "famous_quotes",
    "life_events",
    "key_relationships",
    "key_dialogues",
    "views_on_specific_topics",
)


def _normalise_name(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _philosopher_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for profile in PHILOSOPHER_PROFILES.values():
        aliases[_normalise_name(profile.name)] = profile.name
        aliases[_normalise_name(profile.full_name)] = profile.name
    return aliases


def canonical_philosopher_name(raw_name: str) -> str:
    aliases = _philosopher_aliases()
    return aliases.get(_normalise_name(raw_name), raw_name.strip())


def _source_id_prefix(philosopher_name: str) -> str:
    return "".join(
        character.lower() if character.isalnum() else "_"
        for character in canonical_philosopher_name(philosopher_name)
    ).strip("_")


def _join_list(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value or "")


def _record(
    *,
    source_id: str,
    philosopher: str,
    book: str,
    section: str,
    theme: str,
    text: str,
    path: Path,
) -> dict[str, Any]:
    return {
        "id": source_id,
        "philosopher": canonical_philosopher_name(philosopher),
        "book": book,
        "section": section,
        "theme": theme,
        "text": text,
        "source_file": path.name,
    }


def _normalise_dossier(data: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    philosopher = canonical_philosopher_name(str(data.get("philosopher", "")).strip())
    if not philosopher:
        raise ValueError(f"{path} dossier is missing the top-level 'philosopher' field.")

    prefix = _source_id_prefix(philosopher)
    book = f"{philosopher} Knowledge Dossier"
    records: list[dict[str, Any]] = [
        _record(
            source_id=f"{prefix}_overview",
            philosopher=philosopher,
            book=book,
            section="Overview",
            theme="Identity and school",
            text=(
                f"Philosopher: {data.get('philosopher', philosopher)}\n"
                f"Also known as: {_join_list(data.get('also_known_as'))}\n"
                f"Born: {data.get('born', '')}\n"
                f"Died: {data.get('died', '')}\n"
                f"Era: {data.get('era', '')}\n"
                f"School: {data.get('school', '')}\n"
                f"Note: {data.get('note', '')}"
            ),
            path=path,
        )
    ]

    for item in data.get("core_philosophy", []):
        records.append(
            _record(
                source_id=f"{prefix}_{item['id']}",
                philosopher=philosopher,
                book=book,
                section="Core philosophy",
                theme=str(item.get("topic", "")),
                text=(
                    f"Topic: {item.get('topic', '')}\n"
                    f"Source: {item.get('source', '')}\n"
                    f"Content: {item.get('content', '')}\n"
                    f"Keywords: {_join_list(item.get('keywords'))}"
                ),
                path=path,
            )
        )

    for item in data.get("famous_quotes", []):
        records.append(
            _record(
                source_id=f"{prefix}_{item['id']}",
                philosopher=philosopher,
                book=book,
                section="Famous quote",
                theme=_join_list(item.get("themes")) or "Quote",
                text=(
                    f"Quote: \"{item.get('quote', '')}\"\n"
                    f"Speaker: {item.get('speaker', '')}\n"
                    f"Source: {item.get('source', '')}\n"
                    f"Quote status: {item.get('quote_status', '')}\n"
                    f"Context: {item.get('context', '')}\n"
                    f"Themes: {_join_list(item.get('themes'))}"
                ),
                path=path,
            )
        )

    for item in data.get("life_events", []):
        records.append(
            _record(
                source_id=f"{prefix}_{item['id']}",
                philosopher=philosopher,
                book=book,
                section=str(item.get("period", "Life event")),
                theme=str(item.get("event", "")),
                text=(
                    f"Event: {item.get('event', '')}\n"
                    f"Period: {item.get('period', '')}\n"
                    f"Content: {item.get('content', '')}\n"
                    f"Significance: {item.get('significance', '')}\n"
                    f"Keywords: {_join_list(item.get('keywords'))}"
                ),
                path=path,
            )
        )

    speaking_style = data.get("speaking_style")
    if isinstance(speaking_style, dict):
        records.append(
            _record(
                source_id=f"{prefix}_speaking_style",
                philosopher=philosopher,
                book=book,
                section="Speaking style",
                theme="Voice and method",
                text=(
                    f"Tone: {speaking_style.get('tone', '')}\n"
                    f"Method: {speaking_style.get('method', '')}\n"
                    f"RAG voice warning: {speaking_style.get('rag_voice_warning', '')}\n"
                    f"Never does: {_join_list(speaking_style.get('never_does'))}\n"
                    f"Signature moves: {_join_list(speaking_style.get('signature_moves'))}\n"
                    f"Difficult personal questions: {speaking_style.get('on_difficult_personal_questions', '')}"
                ),
                path=path,
            )
        )

    for item in data.get("key_relationships", []):
        person = str(item.get("person", ""))
        records.append(
            _record(
                source_id=f"{prefix}_relationship_{_source_id_prefix(person)}",
                philosopher=philosopher,
                book=book,
                section="Key relationship",
                theme=person,
                text=(
                    f"Person: {person}\n"
                    f"Relation: {item.get('relation', '')}\n"
                    f"Note: {item.get('note', '')}"
                ),
                path=path,
            )
        )

    for item in data.get("key_dialogues", []):
        title = str(item.get("title", "Dialogue"))
        records.append(
            _record(
                source_id=f"{prefix}_{item['id']}",
                philosopher=philosopher,
                book=book,
                section="Key dialogue",
                theme=title,
                text=(
                    f"Title: {title}\n"
                    f"Topic: {item.get('topic', '')}\n"
                    f"Key ideas: {_join_list(item.get('key_ideas'))}\n"
                    f"Famous line: {item.get('famous_line', '')}\n"
                    f"Famous line speaker: {item.get('famous_line_speaker', '')}\n"
                    f"Famous line status: {item.get('famous_line_status', '')}\n"
                    f"Summary line: {item.get('summary_line', '')}"
                ),
                path=path,
            )
        )

    for index, item in enumerate(data.get("views_on_specific_topics", []), start=1):
        topic = str(item.get("topic", "Specific topic"))
        records.append(
            _record(
                source_id=f"{prefix}_topic_{index:03d}_{_source_id_prefix(topic)}",
                philosopher=philosopher,
                book=book,
                section="View on specific topic",
                theme=topic,
                text=(
                    f"Topic: {topic}\n"
                    f"View: {item.get('view', '')}"
                ),
                path=path,
            )
        )

    return records


def _normalise_source_record(record: dict[str, Any], path: Path) -> dict[str, Any]:
    if REQUIRED_FIELDS <= set(record):
        normalised = dict(record)
    elif CHANAKYA_FIELDS <= set(record):
        tags = record.get("tags", [])
        tag_text = ", ".join(str(tag) for tag in tags) if isinstance(tags, list) else str(tags)
        normalised = {
            "id": record["id"],
            "philosopher": "Chanakya",
            "book": "Arthashastra",
            "section": record["source"],
            "theme": record["title"],
            "text": (
                f"Section: {record['section']}\n"
                f"Subsection: {record['subsection']}\n"
                f"Title: {record['title']}\n"
                f"Principle: {record['principle']}\n"
                f"Elaboration: {record['elaboration']}\n"
                f"Risk: {record.get('risk', '')}\n"
                f"Application: {record.get('application', '')}\n"
                f"Tags: {tag_text}"
            ),
        }
    else:
        missing = REQUIRED_FIELDS - set(record)
        raise ValueError(f"Record {record.get('id', '<missing id>')} in {path} is missing: {sorted(missing)}")

    normalised["philosopher"] = canonical_philosopher_name(str(normalised["philosopher"]))
    normalised["source_file"] = path.name
    return normalised


def load_records_from_file(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if isinstance(records, dict):
        if any(field in records for field in DOSSIER_LIST_FIELDS):
            return _normalise_dossier(records, path)
        raise ValueError(f"{path} must contain a JSON list of source records or a supported philosopher dossier.")

    if not isinstance(records, list):
        raise ValueError(f"{path} must contain a JSON list of source records.")

    return [_normalise_source_record(record, path) for record in records]


def load_records(data_dir: Path = DATA_DIR) -> list[dict[str, Any]]:
    paths = sorted(data_dir.glob(DATA_GLOB))
    if not paths:
        raise FileNotFoundError(f"No {DATA_GLOB} files found in {data_dir}.")

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in paths:
        file_records = load_records_from_file(path)
        for record in file_records:
            record_id = str(record["id"])
            if record_id in seen_ids:
                raise ValueError(f"Duplicate source id '{record_id}' found while reading {path}.")
            seen_ids.add(record_id)
            records.append(record)

    return records


def build_document(record: dict[str, Any]) -> str:
    return (
        f"Philosopher: {record['philosopher']}\n"
        f"Book: {record['book']}\n"
        f"Section: {record['section']}\n"
        f"Theme: {record['theme']}\n"
        f"Text: {record['text']}"
    )


def get_collection(reset: bool = False):
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def ingest(reset: bool = False) -> int:
    from utils.llm import generate_embedding

    records = load_records()
    collection = get_collection(reset=reset)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    embeddings: list[list[float]] = []

    for record in records:
        document = build_document(record)
        ids.append(record["id"])
        documents.append(document)
        metadatas.append(
            {
                "philosopher": record["philosopher"],
                "book": record["book"],
                "section": record["section"],
                "theme": record["theme"],
                "source_id": record["id"],
                "source_file": record["source_file"],
            }
        )
        embeddings.append(generate_embedding(document, task_type="retrieval_document"))

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    return len(ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed and store Philosophy Council source chunks in ChromaDB.")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the Chroma collection.")
    args = parser.parse_args()

    count = ingest(reset=args.reset)
    print(f"Ingested {count} chunks into Chroma collection '{COLLECTION_NAME}' at {CHROMA_PATH}.")


if __name__ == "__main__":
    main()
