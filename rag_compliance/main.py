"""
Main application module for MCA Compliance RAG system.

Provides:
- FastAPI server with POST /query, POST /ingest, GET /health endpoints
- CLI entrypoint for corpus ingestion and sample query testing
- Complete pipeline orchestration: ingest → embed → store → retrieve → generate
"""

import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rag_compliance.config import get_settings, setup_logging
from rag_compliance.embeddings.embedder import Embedder
from rag_compliance.embeddings.vector_store import VectorStore
from rag_compliance.generation.generator import Generator
from rag_compliance.generation.prompt_builder import PromptBuilder
from rag_compliance.ingestion.chunker import DocumentChunker
from rag_compliance.ingestion.metadata_extractor import MetadataExtractor
from rag_compliance.ingestion.parser import PDFParser
from rag_compliance.retrieval.filters import MetadataFilter
from rag_compliance.retrieval.retriever import Retriever

logger = logging.getLogger("rag_compliance.main")


# ── Global pipeline components (initialized at startup) ───────────────
_embedder: Optional[Embedder] = None
_vector_store: Optional[VectorStore] = None
_retriever: Optional[Retriever] = None
_generator: Optional[Generator] = None


def _init_pipeline() -> None:
    """Initialize all pipeline components."""
    global _embedder, _vector_store, _retriever, _generator

    logger.info("Initializing RAG pipeline components...")

    _embedder = Embedder()
    _vector_store = VectorStore(_embedder)

    # Try to load existing vector store
    if _vector_store.load():
        logger.info("Loaded existing vector store (%d vectors)", _vector_store.size)
    else:
        logger.info("No existing vector store found — run /ingest first")

    _retriever = Retriever(_vector_store, _embedder)
    _generator = Generator(PromptBuilder())

    logger.info("RAG pipeline initialized successfully")


# ── Ingestion Pipeline ────────────────────────────────────────────────

def ingest_corpus(corpus_dir: str | None = None) -> dict[str, Any]:
    """Run the full ingestion pipeline on the corpus directory.

    1. Parse all PDFs
    2. Chunk each document
    3. Extract metadata
    4. Generate embeddings
    5. Store in FAISS

    Args:
        corpus_dir: Path to corpus directory. Defaults to config value.

    Returns:
        Summary dict with ingestion statistics.
    """
    global _vector_store

    settings = get_settings()
    corpus_path = Path(corpus_dir or settings.corpus_dir)

    logger.info("=" * 60)
    logger.info("STARTING CORPUS INGESTION: %s", corpus_path)
    logger.info("=" * 60)

    # Step 1: Parse PDFs
    parser = PDFParser()
    documents = parser.parse_directory(corpus_path)

    if not documents:
        logger.error("No documents parsed from %s", corpus_path)
        return {"status": "error", "message": "No documents found"}

    # Step 2: Chunk documents
    chunker = DocumentChunker()
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk(doc)
        all_chunks.extend(chunks)

    logger.info("Total chunks: %d from %d documents", len(all_chunks), len(documents))

    # Step 3: Extract metadata
    extractor = MetadataExtractor()
    all_metadata = extractor.extract_batch(all_chunks)

    # Step 4: Prepare texts and metadata for vector store
    texts = [chunk.text for chunk in all_chunks]
    metadata_dicts = [m.to_dict() for m in all_metadata]

    # Step 5: Clear existing store and add new data
    if _vector_store is None:
        _embedder_local = Embedder()
        _vector_store = VectorStore(_embedder_local)

    _vector_store.clear()
    added = _vector_store.add_texts(texts, metadata_dicts)

    # Step 6: Persist to disk
    _vector_store.save()

    # Re-initialize retriever with updated store
    global _retriever, _generator
    if _retriever is not None:
        _retriever = Retriever(_vector_store, _embedder or Embedder())

    summary = {
        "status": "success",
        "documents_parsed": len(documents),
        "total_chunks": len(all_chunks),
        "vectors_stored": added,
        "corpus_dir": str(corpus_path),
        "documents": [
            {
                "filename": doc.filename,
                "pages": doc.total_pages,
                "pages_with_text": len(doc.pages),
            }
            for doc in documents
        ],
    }

    logger.info("=" * 60)
    logger.info("INGESTION COMPLETE: %d chunks from %d documents", added, len(documents))
    logger.info("=" * 60)

    return summary


# ── API Request/Response Models ───────────────────────────────────────

class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""

    query: str = Field(..., min_length=3, description="Compliance question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    filters: Optional[dict[str, str]] = Field(
        default=None,
        description="Metadata filters (act, section, rule, form, topic, entity_type, source_type)",
    )


class QueryResponse(BaseModel):
    """Response body for the /query endpoint."""

    answer: str
    statutory_basis: list[str] = []
    forms_involved: list[str] = []
    penalty: Optional[str] = None
    notes: Optional[str] = None
    sources: list[dict[str, Any]] = []
    query: str = ""


class IngestResponse(BaseModel):
    """Response body for the /ingest endpoint."""

    status: str
    documents_parsed: int = 0
    total_chunks: int = 0
    vectors_stored: int = 0
    corpus_dir: str = ""
    documents: list[dict[str, Any]] = []
    message: str = ""


# ── FastAPI Application ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize pipeline on startup, cleanup on shutdown."""
    setup_logging()
    _init_pipeline()
    yield
    logger.info("Shutting down RAG pipeline")


app = FastAPI(
    title="MCA Compliance RAG API",
    description=(
        "Production-grade Retrieval-Augmented Generation system for Indian "
        "corporate compliance — Companies Act 2013, LLP Act 2008, MCA Forms."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vector_store_size": _vector_store.size if _vector_store else 0,
        "llm_provider": get_settings().llm_provider,
    }


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Process a compliance query through the RAG pipeline.

    1. Retrieve relevant chunks from the vector store
    2. Build a grounded prompt with retrieved context
    3. Generate a structured compliance answer

    Returns structured JSON with answer, statutory basis, forms, penalty, notes.
    """
    if _retriever is None or _generator is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    if _vector_store and _vector_store.size == 0:
        raise HTTPException(
            status_code=503,
            detail="Vector store is empty. Run POST /ingest first.",
        )

    logger.info("Query received: '%s'", request.query)

    # Build metadata filter
    filters = None
    if request.filters:
        filters = MetadataFilter(
            act=request.filters.get("act"),
            section=request.filters.get("section"),
            rule=request.filters.get("rule"),
            form=request.filters.get("form"),
            topic=request.filters.get("topic"),
            entity_type=request.filters.get("entity_type"),
            source_type=request.filters.get("source_type"),
        )

    # Retrieve context
    context = _retriever.retrieve_with_context(
        query=request.query,
        top_k=request.top_k,
        filters=filters,
    )

    # Generate response
    response = _generator.generate(request.query, context)

    return QueryResponse(
        answer=response.get("answer", ""),
        statutory_basis=response.get("statutory_basis", []),
        forms_involved=response.get("forms_involved", []),
        penalty=response.get("penalty"),
        notes=response.get("notes"),
        sources=context.get("sources", []),
        query=request.query,
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint() -> IngestResponse:
    """Trigger corpus ingestion pipeline.

    Parses all PDFs in the corpus directory, chunks them,
    extracts metadata, generates embeddings, and stores in FAISS.
    """
    logger.info("Ingestion triggered via API")

    try:
        result = ingest_corpus()
        return IngestResponse(**result)
    except Exception as e:
        logger.error("Ingestion failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


# ── CLI Entrypoint ────────────────────────────────────────────────────

def run_sample_query() -> None:
    """Run a sample compliance query for testing."""
    setup_logging()
    _init_pipeline()

    if _vector_store is None or _vector_store.size == 0:
        print("\n⚠️  Vector store is empty. Running ingestion first...")
        result = ingest_corpus()
        print(f"✅ Ingestion complete: {result['total_chunks']} chunks from {result['documents_parsed']} documents\n")

        # Re-initialize pipeline with populated store
        _init_pipeline()

    sample_query = "What is the penalty for late filing of annual return?"

    print(f"\n{'='*60}")
    print(f"SAMPLE QUERY: {sample_query}")
    print(f"{'='*60}\n")

    if _retriever is None or _generator is None:
        print("❌ Pipeline not initialized")
        return

    # Retrieve
    context = _retriever.retrieve_with_context(sample_query, top_k=5)
    print(f"📚 Retrieved {context['num_results']} relevant chunks\n")

    for i, ctx in enumerate(context["contexts"][:3], 1):
        print(f"  [{i}] Source: {ctx['source']} (score: {ctx['score']:.4f})")
        print(f"      {ctx['text'][:150]}...\n")

    # Generate
    response = _generator.generate(sample_query, context)

    print(f"\n{'─'*60}")
    print("🧠 ANSWER:")
    print(f"{'─'*60}")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        # CLI: python -m rag_compliance.main ingest
        setup_logging()
        _init_pipeline()
        result = ingest_corpus()
        print(json.dumps(result, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "serve":
        # CLI: python -m rag_compliance.main serve
        import uvicorn
        uvicorn.run(
            "rag_compliance.main:app",
            host=get_settings().api_host,
            port=get_settings().api_port,
            reload=True,
        )
    else:
        # Default: run sample query
        run_sample_query()
