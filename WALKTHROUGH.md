# MCA Compliance RAG — Setup & Walkthrough

A **production-grade RAG pipeline** for Indian corporate compliance, implemented as a modular Python package.

## Project Structure

```
mca-compliance-rag/
├── corpus_raw_v1/              # 15 PDFs (acts, rules, forms)
├── rag_compliance/
│   ├── __init__.py
│   ├── config.py               # Pydantic BaseSettings, env-driven
│   ├── main.py                 # FastAPI app + CLI entrypoint
│   ├── ingestion/
│   │   ├── parser.py           # PyMuPDF PDF extraction
│   │   ├── chunker.py          # Regex structural + fixed-size splitting
│   │   └── metadata_extractor.py  # Filename + content metadata inference
│   ├── embeddings/
│   │   ├── embedder.py         # SentenceTransformer (all-MiniLM-L6-v2)
│   │   └── vector_store.py     # FAISS IndexFlatIP + JSON metadata sidecar
│   ├── retrieval/
│   │   ├── retriever.py        # Full retrieval orchestrator
│   │   ├── reranker.py         # Pass-through stub (Phase 2)
│   │   └── filters.py          # MetadataFilter dataclass + matching
│   ├── generation/
│   │   ├── prompt_builder.py   # Strict grounding system prompt
│   │   └── generator.py        # Gemini free tier + Ollama backends
│   └── evaluation/
│       └── evaluator.py        # Retrieval/response quality metrics
├── requirements.txt
└── .env.example
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy env template
cp .env.example .env
```

Then choose your LLM provider:

#### Option A: Ollama (Recommended — Fully Local, No API Key)

```bash
# Install Ollama from https://ollama.ai
# Pull a model:
ollama pull mistral

# In .env, set:
# LLM_PROVIDER=ollama
```

#### Option B: Gemini Free Tier

```bash
# Get a free API key from https://aistudio.google.com
# In .env, set:
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your-key-here
```

> **Note:** The Gemini free tier has daily quota limits. If you hit a `429 RESOURCE_EXHAUSTED` error, switch to Ollama or wait for the daily quota to reset.

### 3. Ingest the Corpus

```bash
python -m rag_compliance.main ingest
```

This parses all PDFs in `corpus_raw_v1/`, chunks them, generates embeddings, and builds the FAISS vector store.

### 4. Run a Sample Query

```bash
python -m rag_compliance.main
```

### 5. Start the API Server

```bash
python -m rag_compliance.main serve
# Then: POST http://localhost:8000/query
#   Body: {"query": "What is the penalty for late filing of annual return?"}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check + vector store size |
| `POST` | `/query` | RAG query → structured compliance answer |
| `POST` | `/ingest` | Trigger corpus ingestion pipeline |

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | Gemini free tier / Ollama | Zero cost — free API key or fully local |
| Embeddings | `all-MiniLM-L6-v2` | Free, local, 384-dim, good quality |
| Vector store | FAISS `IndexFlatIP` | Zero infra, file-based persistence |
| Similarity | Cosine (via inner product on L2-normed) | Standard for semantic search |
| Chunking | Regex structural → fixed-size fallback | Preserves section boundaries |

## Legal Guardrails

- System prompt enforces **answer only from retrieved context**
- **Cites section numbers** from retrieved chunks
- Returns structured fallback when context is insufficient
- Low temperature (0.1) for factual accuracy

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `429 RESOURCE_EXHAUSTED` from Gemini | Switch to Ollama (`LLM_PROVIDER=ollama` in `.env`) or wait for daily quota reset |
| `Cannot connect to Ollama` | Run `ollama serve` in a separate terminal |
| `Model not found` in Ollama | Run `ollama pull mistral` first |
| Empty vector store | Run `python -m rag_compliance.main ingest` to build it |
