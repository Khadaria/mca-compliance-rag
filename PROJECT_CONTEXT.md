# Project Context

This document describes the current implementation only.

## What The App Does

CompliCS is a legal-domain RAG assistant for Indian corporate compliance. It retrieves relevant statutory text from a curated corpus and uses Groq to generate answers grounded in those passages.

## Active Stack

- backend: FastAPI
- frontend: React + Vite
- LLM: Groq
- embeddings: HuggingFace sentence-transformers
- vector DB: Chroma
- lexical retrieval: BM25
- reranker: Flashrank

## Backend Files

- [backend/server.py](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/backend/server.py)
  FastAPI entrypoint with `/query` and `/health`
- [backend/populate_database.py](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/backend/populate_database.py)
  one-time indexing script for the PDF corpus
- [backend/rag_compliance/config.py](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/backend/rag_compliance/config.py)
  runtime paths and model settings
- [backend/rag_compliance/embeddings/embedder.py](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/backend/rag_compliance/embeddings/embedder.py)
  sentence-transformers embedder
- [backend/rag_compliance/retrieval/hybrid_retriever.py](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/backend/rag_compliance/retrieval/hybrid_retriever.py)
  Chroma + BM25 retrieval
- [backend/rag_compliance/retrieval/reranker.py](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/backend/rag_compliance/retrieval/reranker.py)
  Flashrank reranking
- [backend/rag_compliance/generation/chain.py](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/backend/rag_compliance/generation/chain.py)
  retrieval to grounded generation flow

## Frontend Files

- [frontend/src/CompliCS.jsx](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/frontend/src/CompliCS.jsx)
  main UI
- [frontend/src/main.jsx](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/frontend/src/main.jsx)
  app bootstrap
- [frontend/src/index.css](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/frontend/src/index.css)
  base styling

## Runtime Flow

1. User submits a question from the frontend.
2. Frontend posts to `POST /query`.
3. Backend retrieves Chroma matches and BM25 matches.
4. Results are deduplicated and reranked.
5. Top passages are injected into the Groq prompt.
6. Backend returns the answer and source snippets.
7. Frontend renders the answer and the supporting sources.

## Important Constraints

- `backend/chroma` must match the configured embedding model.
- `GROQ_API_KEY` must be present in the backend environment.
- chat history is in-memory only and resets on backend restart.
- this repo no longer uses Ollama or Streamlit.

## Deployment Target

Recommended no-Docker deployment:
- Vercel for `frontend/`
- Render for `backend/`

Full walkthrough:
- [DEPLOYMENT_GUIDE.md](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/DEPLOYMENT_GUIDE.md)
