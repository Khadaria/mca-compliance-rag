import argparse
import time

from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import NotFoundException

from rag_compliance.config import (
    DATA_PATH,
    PINECONE_API_KEY,
    PINECONE_CLOUD,
    PINECONE_DIMENSION,
    PINECONE_INDEX,
    PINECONE_NAMESPACE,
    PINECONE_REGION,
)
from rag_compliance.embeddings.embedder import get_embedding_function
from rag_compliance.ingestion.loader import load_and_filter_documents
from rag_compliance.ingestion.chunker import split_documents
# from rag_compliance.ingestion.metadata import enrich_chunks_with_metadata  # Skipped: too slow on CPU (9408 chunks × ~5s each = 13+ hrs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()

    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY is not set.")

    if args.reset:
        print("Clearing Pinecone namespace")
        clear_database()

    documents = load_and_filter_documents(DATA_PATH)
    chunks = split_documents(documents)
    
    # Metadata extraction skipped — runs once per chunk via LLM (too slow on CPU)
    # To re-enable: uncomment the import above and the two lines below
    # print("Enriching chunks with LLM Metadata...")
    # chunks = enrich_chunks_with_metadata(chunks)

    add_to_pinecone(chunks)


def ensure_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing_indexes = {item["name"] for item in pc.list_indexes()}

    if PINECONE_INDEX not in existing_indexes:
        print(f"Creating Pinecone index '{PINECONE_INDEX}'...")
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=PINECONE_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )

    timeout_seconds = 180
    started_at = time.time()

    while True:
        description = pc.describe_index(PINECONE_INDEX)
        status = getattr(description, "status", {}) or {}
        if isinstance(status, dict):
            ready = bool(status.get("ready"))
            state = status.get("state", "unknown")
        else:
            ready = bool(getattr(status, "ready", False))
            state = getattr(status, "state", "unknown")

        if ready:
            print(f"Pinecone index '{PINECONE_INDEX}' is ready.")
            break

        elapsed = int(time.time() - started_at)
        print(
            f"Waiting for Pinecone index to become ready... "
            f"state={state}, elapsed={elapsed}s"
        )

        if elapsed >= timeout_seconds:
            raise TimeoutError(
                f"Pinecone index '{PINECONE_INDEX}' did not report ready within "
                f"{timeout_seconds} seconds. Last known state: {state}"
            )

        time.sleep(2)

    return pc.Index(PINECONE_INDEX)


def add_to_pinecone(chunks: list):
    index = ensure_index()
    vector_store = PineconeVectorStore(
        index=index,
        embedding=get_embedding_function(),
        namespace=PINECONE_NAMESPACE,
        text_key="text",
    )

    chunks_with_ids = calculate_chunk_ids(chunks)

    if chunks_with_ids:
        print(f"Adding documents to Pinecone: {len(chunks_with_ids)}")
        batch_size = 100
        for i in range(0, len(chunks_with_ids), batch_size):
            batch_chunks = chunks_with_ids[i:i + batch_size]
            batch_ids = [chunk.metadata["id"] for chunk in batch_chunks]
            print(f"Adding batch {i // batch_size + 1}...")
            vector_store.add_documents(batch_chunks, ids=batch_ids)
    else:
        print("No documents found to add")


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
    index = ensure_index()
    try:
        index.delete(delete_all=True, namespace=PINECONE_NAMESPACE)
    except NotFoundException:
        print(f"Namespace '{PINECONE_NAMESPACE}' does not exist yet. Skipping clear.")


if __name__ == "__main__":
    main()
