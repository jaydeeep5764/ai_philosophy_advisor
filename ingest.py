from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import chromadb

from utils.llm import generate_embedding


ROOT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT_DIR / "data" / "marcus_aurelius_meditations.json"
CHROMA_PATH = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "philosophy_council_sources"


def load_records(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError(f"{path} must contain a JSON list of source records.")

    required_fields = {"id", "philosopher", "book", "section", "theme", "text"}
    for record in records:
        missing = required_fields - set(record)
        if missing:
            raise ValueError(f"Record {record.get('id', '<missing id>')} is missing: {sorted(missing)}")
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
