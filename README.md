# CompliCS

CompliCS is a Retrieval-Augmented Generation (RAG) assistant for Indian corporate compliance. It answers questions against a curated corpus covering the Companies Act, LLP Act, related rules, and filing forms.

The current stack is:
- `frontend/`: React + Vite UI
- `backend/`: FastAPI API
- LLM: Groq
- embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- vector store: Chroma persisted at `backend/chroma`
- retrieval: hybrid Chroma + BM25 with Flashrank reranking

This project is for educational use and does not constitute legal advice.

## Repository Layout

```text
mca-compliance-rag/
├─ backend/
│  ├─ server.py
│  ├─ populate_database.py
│  ├─ requirements.txt
│  ├─ chroma/
│  ├─ corpus_raw_v1/
│  └─ rag_compliance/
├─ frontend/
│  ├─ src/
│  ├─ public/
│  └─ package.json
├─ .env.example
├─ DEPLOYMENT_GUIDE.md
├─ PROJECT_CONTEXT.md
└─ render.yaml
```

## Local Development

### 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Set environment variables:

```powershell
$env:GROQ_API_KEY="your_key"
$env:GROQ_MODEL="llama-3.3-70b-versatile"
$env:EMBEDDING_MODEL="all-MiniLM-L6-v2"
```

Start the API:

```powershell
python server.py
```

Health check:

```text
http://localhost:8000/health
```

### 2. Frontend

```powershell
cd frontend
npm install
$env:VITE_API_URL="http://localhost:8000"
npm run dev
```

Open:

```text
http://localhost:5173
```

## Rebuild the Vector Store

If you change the embedding model or corpus, rebuild Chroma:

```powershell
cd backend
$env:EMBEDDING_MODEL="all-MiniLM-L6-v2"
python populate_database.py --reset
```

Important:
- if your current `backend/chroma` was built with Ollama embeddings, rebuild it before deploying
- the deployed app must use the same embedding model that was used to build the stored vectors

## Deployment

Use this no-Docker route:
- frontend on Vercel
- backend on Render
- Groq API for generation

The full step-by-step walkthrough is in [DEPLOYMENT_GUIDE.md](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/DEPLOYMENT_GUIDE.md).

## Environment Variables

Backend:
- `GROQ_API_KEY`
- `GROQ_MODEL`
- `EMBEDDING_MODEL`

Frontend:
- `VITE_API_URL`

See [.env.example](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/.env.example) for a starter template.
