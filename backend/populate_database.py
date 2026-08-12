import argparse
import os
import shutil

from langchain_chroma import Chroma

from rag_compliance.config import CHROMA_PATH, CHROMA_V2_PATH, DATA_PATH
from rag_compliance.embeddings.embedder import get_embedding_function
from rag_compliance.ingestion.loader import load_and_filter_documents
from rag_compliance.ingestion.chunker import split_documents
from rag_compliance.ingestion.legal_parser import parse_legal_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the target database.")
    parser.add_argument(
        "--target",
        choices=["v2", "prod"],
        default="v2",
        help="Which Chroma store to write to. Defaults to 'v2' (backend/chroma_v2), "
             "a separate store for verification before it is manually promoted to "
             "production. Use 'prod' only after chroma_v2 has been verified.",
    )
    args = parser.parse_args()

    target_path = CHROMA_V2_PATH if args.target == "v2" else CHROMA_PATH

    if args.reset:
        print(f"Clearing database at {target_path}")
        clear_database(target_path)

    pages_by_file = load_and_filter_documents(DATA_PATH)
    chunks = []

    for source_path, pages in pages_by_file.items():
        parsed = parse_legal_pdf(pages, source_path)
        if parsed:
            print(f"[legal_parser] {os.path.basename(source_path)}: {len(parsed)} chunks")
            chunks.extend(parsed)
        else:
            print(f"[fallback splitter] {os.path.basename(source_path)}: "
                  f"0 structural matches, using plain splitter")
            chunks.extend(split_documents(pages))

    print(f"Total chunks: {len(chunks)}")

    add_to_chroma(chunks, target_path)


def add_to_chroma(chunks: list, chroma_path: str):
    db = Chroma(
        persist_directory=chroma_path,
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
        print(f"Adding new documents: {len(new_chunks)}")
        BATCH_SIZE = 100
        for i in range(0, len(new_chunks), BATCH_SIZE):
            batch_chunks = new_chunks[i:i+BATCH_SIZE]
            batch_ids = [chunk.metadata["id"] for chunk in batch_chunks]
            print(f"Adding batch {i // BATCH_SIZE + 1}...")
            db.add_documents(batch_chunks, ids=batch_ids)
    else:
        print("No new documents to add")


def calculate_chunk_ids(chunks):
    """
    Structurally-parsed chunks (have a "section" in metadata that came from
    legal_parser) get an id keyed by source/section/subsection, which stays
    stable across re-runs even if page numbers shift slightly on
    re-extraction. Fallback/forms chunks (no section metadata) keep the
    original page-bound id scheme since they're still one-chunk-per-page-run.
    """
    last_page_id = None
    current_chunk_index = 0
    section_counts = {}

    for chunk in chunks:
        source = chunk.metadata.get("source")

        if "section" in chunk.metadata:
            section = chunk.metadata.get("section") or "na"
            subsection = chunk.metadata.get("subsection") or "na"
            key = f"{source}:{section}:{subsection}"
            section_counts[key] = section_counts.get(key, 0) + 1
            chunk_id = f"{key}:{section_counts[key] - 1}"
        else:
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


def clear_database(chroma_path: str):
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)


if __name__ == "__main__":
    main()
