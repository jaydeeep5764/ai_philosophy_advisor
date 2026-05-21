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
