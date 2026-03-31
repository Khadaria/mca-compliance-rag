import argparse
import os
import shutil

from langchain_chroma import Chroma

from rag_compliance.config import CHROMA_PATH, DATA_PATH
from rag_compliance.embeddings.embedder import get_embedding_function
from rag_compliance.ingestion.loader import load_and_filter_documents
from rag_compliance.ingestion.chunker import split_documents
from rag_compliance.ingestion.metadata import enrich_chunks_with_metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()

    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    documents = load_and_filter_documents(DATA_PATH)
    chunks = split_documents(documents)
    
    print("Enriching chunks with LLM Metadata...")
    chunks = enrich_chunks_with_metadata(chunks)
    
    add_to_chroma(chunks)


def add_to_chroma(chunks: list):
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function()
    )

    chunks_with_ids = calculate_chunk_ids(chunks)
    
    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    new_chunks = [
        chunk for chunk in chunks_with_ids
        if chunk.metadata["id"] not in existing_ids
    ]

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        BATCH_SIZE = 100
        for i in range(0, len(new_chunks), BATCH_SIZE):
            batch_chunks = new_chunks[i:i+BATCH_SIZE]
            batch_ids = [chunk.metadata["id"] for chunk in batch_chunks]
            print(f"Adding batch {i // BATCH_SIZE + 1}...")
            db.add_documents(batch_chunks, ids=batch_ids)
    else:
        print("✅ No new documents to add")


def calculate_chunk_ids(chunks):
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()