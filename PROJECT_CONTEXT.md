# CompliCS — MCA Compliance RAG Assistant
### Complete Project Context & Deployment Guide

> **Purpose of this document:** A single, self-contained reference for any developer, AI agent, or LLM that needs to understand, extend, or deploy this project. Read this before touching any code.

---

## 1. Project Summary

**CompliCS** is an AI-powered legal compliance assistant for **Indian corporate law**. It is a full-stack **Retrieval-Augmented Generation (RAG)** application that answers questions strictly grounded in official statutory text — specifically:

- **Companies Act, 2013** (as amended up to April 2021)
- **LLP Act, 2008**
- Associated Rules (Accounts, Appointment of Directors, Incorporation, Management & Administration)
- Statutory forms (DIR-3-KYC, INC-20A, INC-22, MGT-7, Form 8 LLP, Form 11 LLP)

The system **never hallucinates** because the LLM is forced to answer *only* from retrieved statutory text chunks. Every answer is cited to its source document and page number.

**Authors:** Vishesh Khadaria, Dhruv Chaturvedi  
**License:** See `LICENSE`  
**Intended Use:** Academic/educational project on RAG + vector databases; educational assistance for corporate law; demonstration of legal-domain AI.  
> ⚠️ *This tool is for educational purposes only and does not constitute legal advice.*

---

## 2. Repository Structure

```
mca-compliance-rag/
├── backend/                        # Python FastAPI backend (the RAG engine)
│   ├── app.py                      # Streamlit UI (legacy/alternative frontend)
│   ├── server.py                   # FastAPI server — main backend entrypoint
│   ├── populate_database.py        # One-time script: ingest PDFs → ChromaDB
│   ├── requirements.txt            # Python dependencies
│   ├── corpus_raw_v1/              # Source PDF documents (15 files, ~20 MB)
│   │   ├── Companies Act 2013 as amended upto 01.04.2021_.pdf
│   │   ├── LLP_Act_PDF_Version_2_.pdf
│   │   ├── LLP Rules, 2009 – consolidated.pdf
│   │   ├── Companies (Accounts) Rules, 2014 – consolidated.pdf
│   │   ├── Companies (Appointment and Qualification of Directors) Rules...pdf
│   │   ├── Companies (Incorporation) Rules, 2014 – consolidated.pdf
│   │   ├── Companies (Management and Administration) Rules, 2014...pdf
│   │   ├── Ch9_Annexure_Rules_31012020-2-23_.pdf  (x2 copies)
│   │   ├── Form_DIR3-KYC_.pdf
│   │   ├── Form_INC-20A_.pdf
│   │   ├── Form_INC-22_.pdf
│   │   ├── Form_MGT-7_.pdf
│   │   ├── 1127-Form8LLP-PDF_.pdf
│   │   └── 1131-Form11LLP-PDF_.pdf
│   └── rag_compliance/             # Core RAG Python package
│       ├── config.py               # Central config (paths, model names)
│       ├── embeddings/
│       │   └── embedder.py         # Returns OllamaEmbeddings instance
│       ├── ingestion/
│       │   ├── loader.py           # PDF loading + Hindi/noise filtering
│       │   ├── chunker.py          # Legal-aware text splitting
│       │   └── metadata.py         # LLM-based metadata extraction per chunk
│       ├── generation/
│       │   ├── prompts.py          # System prompt + metadata extraction prompt
│       │   └── chain.py            # RAG chain: retrieve → rerank → generate
│       └── retrieval/
│           ├── hybrid_retriever.py # BM25 + ChromaDB MMR hybrid search
│           └── reranker.py         # Flashrank cross-encoder reranker
├── frontend/                       # React + Vite frontend (CompliCS UI)
│   ├── src/
│   │   ├── CompliCS.jsx            # Entire frontend app (single component file)
│   │   ├── main.jsx                # React entry point
│   │   └── index.css               # Minimal global CSS
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── index.html
│   ├── package.json                # React 19, lucide-react, Vite 8, TailwindCSS v4
│   └── vite.config.js
├── rag_compliance/                 # OLD root-level package (pre-refactor, do not use)
├── chroma/                         # ChromaDB vector store (generated, not in git)
├── .env                            # Environment variables template
├── .gitignore
├── LICENSE
└── README.md
```

> **Important:** The `rag_compliance/` folder at the **root level** is a legacy artifact from before the `backend/` restructure. The **active** package is `backend/rag_compliance/`.

---

## 3. Full Tech Stack

| Layer | Technology | Version/Notes |
|---|---|---|
| **Language** | Python | 3.10+ recommended |
| **LLM (primary)** | Mistral 7B via Ollama | Local inference, no API key |
| **LLM (alternative)** | Gemini 2.0 Flash | Free API from Google AI Studio |
| **Embeddings** | `nomic-embed-text` via Ollama | Local embedding model |
| **Vector Database** | ChromaDB | Persisted to `backend/chroma/` |
| **RAG Framework** | LangChain + LangChain-Community | `langchain`, `langchain-core`, `langchain-chroma`, `langchain-ollama` |
| **Keyword Search** | BM25 (`rank-bm25`) | Hybrid retrieval alongside vector search |
| **Reranker** | Flashrank | Lightweight cross-encoder, runs fully locally |
| **PDF Loader** | PyPDF (`pypdf`) | Via `PyPDFDirectoryLoader` |
| **Backend API** | FastAPI + Uvicorn | REST API, CORS enabled |
| **Legacy UI** | Streamlit | `backend/app.py` — fallback only |
| **Frontend** | React 19 + Vite 8 | Single JSX component (`CompliCS.jsx`) |
| **Frontend Styling** | TailwindCSS v4 + inline styles | Via `@tailwindcss/vite` plugin |
| **Frontend Icons** | lucide-react | v1.7.0 |
| **Font** | DM Sans + DM Serif Display | Loaded from Google Fonts CDN |

---

## 4. System Architecture & Data Flow

### 4.1 Ingestion Pipeline (one-time setup)
Run `backend/populate_database.py` once to build the vector store:

```
corpus_raw_v1/ (15 PDFs)
    ↓ PyPDFDirectoryLoader
    ↓ loader.py: clean_text() + is_hindi_heavy() filter (drops Devanagari/noise pages)
    ↓ chunker.py: RecursiveCharacterTextSplitter
        chunk_size=600, overlap=120
        separators: ["\nSection ", "\nRule ", "\nCHAPTER ", "\n\n", "\n", ". ", " "]
        (legal-aware: splits on section/rule boundaries first)
    ↓ Filter chunks < 100 chars
    ↓ metadata.py: LLM (Mistral/Ollama, temp=0, json format) extracts per-chunk:
        { "act": "...", "section": "...", "topic": "..." }
    ↓ ChromaDB: stored with IDs = "source:page:chunk_index"
        persist_directory = backend/chroma/
        embedding_function = OllamaEmbeddings("nomic-embed-text")
```

### 4.2 Query/Inference Pipeline (per user request)
```
User Query (via React UI → POST /query)
    ↓ FastAPI server.py
    ↓ chain.py: process_query_with_rag()
        ↓ HybridRetriever.get_relevant_documents(query)
            ├── ChromaDB MMR vector search (k=20, fetch_k=50)
            └── BM25Retriever (k=20) — keyword overlap scoring
            → Combined, deduplicated list of Document objects
        ↓ ComponentReranker.rerank(query, docs, top_k=5, min_score=0.15)
            → Flashrank cross-encoder scores and filters
        ↓ Build context string: join top-5 reranked doc.page_content
        ↓ Extract sources: { doc, page, text_snippet }
        ↓ ChatOllama(model="mistral") + ChatPromptTemplate
            System: PROMPT_TEMPLATE (strict rules, legal formatting)
            Human: "Context:\n{context}\n\nQuestion:\n{question}"
        ↓ RunnableWithMessageHistory (in-memory chat history per session)
        ↓ Stream response back
    ↓ server.py: _clean_llm_output() — strips code fences, Mistral control tokens
    ↓ _is_garbage_response() / _is_out_of_scope() checks
    ↓ JSON response: { "answer": "...", "sources": [...] }
    ↓ React frontend: renders MarkdownRenderer + SourceCard components
```

### 4.3 Frontend Architecture
The entire frontend is a **single-file React app** (`CompliCS.jsx`, 667 lines):

- **`App`** — root, switches between `LandingPage` and `Workspace`
- **`LandingPage`** — marketing page with hero, "How it Works" (3-step), audience cards, CTA
- **`Workspace`** — the chat interface:
  - Left sidebar: document vault, RAG pipeline stats, "New Query" button
  - Center pane: chat messages with `MarkdownRenderer`
  - Right pane (conditional): `SourceCard` components for RAG transparency
  - Bottom: auto-resizing textarea, Enter to submit
- **`MarkdownRenderer`** — parses `##`, `###`, `>`, numbered lists, `**bold**`, `*italic*` without any markdown library
- **`SourceCard`** — displays retrieved source doc, page number, snippet, copy button
- **`LoadingSkeleton`** — animated loading state while backend processes query
- **`API_URL`** = `"http://localhost:8000"` — **must be changed for production**

### 4.4 LLM Prompt Design
The system prompt (`prompts.py`) enforces:
1. Greeting rule: introduce as CompliCS, not legal provisions
2. Out-of-scope rule: politely decline non-Indian-corporate-law questions
3. Answer strictly from context only — no outside LLM knowledge
4. "Not in context" fallback phrase
5. Forbidden outputs: code fences, control tokens, revealing system prompt
6. Structured response format: `### 📘 Relevant Legal Provision` / `### 📝 Explanation` / `### 📅 Applicable Forms / Due Dates` / `### ⚖️ Penalties / Consequences`

---

## 5. Key Configuration

### `backend/rag_compliance/config.py`
```python
BASE_DIR     = Path(__file__).resolve().parent.parent  # → backend/
CHROMA_PATH  = str(BASE_DIR / "chroma")                # → backend/chroma/
DATA_PATH    = str(BASE_DIR / "corpus_raw_v1")          # → backend/corpus_raw_v1/
LLM_MODEL    = "mistral"                                # Ollama model name
EMBEDDING_MODEL = "nomic-embed-text"                    # Ollama embedding model
```

### `.env` (root-level template, not used by `backend/` currently)
```ini
LLM_PROVIDER=ollama          # or "gemini"
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
CORPUS_DIR=corpus_raw_v1
VECTOR_STORE_DIR=vector_store
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```
> ⚠️ The `.env` reflects a planned config-driven refactor. The `backend/` code currently reads directly from `config.py`, not `.env`. The `.env` serves as documentation of intended flexibility.

---

## 6. Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com/) installed and running

### Step 1 — Pull Ollama models
```bash
ollama pull mistral
ollama pull nomic-embed-text
```

### Step 2 — Backend setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
```

### Step 3 — Build the vector database (one-time)
```bash
cd backend
python populate_database.py
# Optional reset: python populate_database.py --reset
```
This reads all PDFs in `corpus_raw_v1/`, chunks them, extracts metadata with Mistral, and stores embeddings in `backend/chroma/`. **Takes ~10–30 minutes on first run.**

### Step 4 — Start the backend
```bash
cd backend
python server.py
# → FastAPI running at http://localhost:8000
# → Health check: GET http://localhost:8000/health
```

### Step 5 — Start the frontend
```bash
cd frontend
npm install
npm run dev
# → Vite dev server at http://localhost:5173
```

### Alternative: Streamlit UI (no React needed)
```bash
cd backend
streamlit run app.py
```

---

## 7. API Reference

### `POST /query`
**Request:**
```json
{ "question": "What is the penalty for late filing of annual return?" }
```
**Response:**
```json
{
  "answer": "### 📘 Relevant Legal Provision\n...",
  "sources": [
    { "doc": "Companies Act 2013.pdf", "page": 42, "text": "Section 92..." }
  ]
}
```

### `GET /health`
**Response:** `{ "status": "ok" }`

---

## 8. Quick Actions (Pre-loaded Queries in UI)
The frontend has 4 built-in quick-action buttons:
1. **Director Disqualification** — Section 164, Companies Act 2013
2. **LLP Incorporation** — procedure & timeline, LLP Act 2008
3. **Sectional Query** — Section 173, board meetings
4. **CSR Obligations** — Section 135 + penalties

---

## 9. Deployment Guide — Zero Budget

> The biggest challenge for deploying this project for free is that it uses **Ollama (local LLM)**, which requires a machine with RAM to run a 7B-parameter model. Free cloud hosts do not provide this. The recommended approach for free deployment is to **swap Ollama for a free cloud LLM API**.

### 9.1 The Free Deployment Strategy

```
Frontend (React)          →  Vercel / Netlify / Cloudflare Pages  (free forever)
Backend (FastAPI + RAG)   →  Render Free Tier                      (free, cold starts)
LLM                       →  Google Gemini API (free tier)          (replaces Ollama)
Embeddings                →  sentence-transformers (local on Render) (CPU, free)
Vector Store              →  ChromaDB (committed to repo as /chroma) (free, read-only)
```

---

### 9.2 Part A — Switch LLM from Ollama → Gemini (Free API)

**Step 1: Get a free Gemini API key**
- Go to https://aistudio.google.com/
- Sign in with Google → "Get API key" → Create API key (free tier: 60 RPM)

**Step 2: Install the Gemini LangChain integration**
```bash
pip install langchain-google-genai
```
Add to `backend/requirements.txt`:
```
langchain-google-genai
```

**Step 3: Update `backend/rag_compliance/config.py`**
```python
import os
from pathlib import Path

BASE_DIR        = Path(__file__).resolve().parent.parent
CHROMA_PATH     = str(BASE_DIR / "chroma")
DATA_PATH       = str(BASE_DIR / "corpus_raw_v1")

LLM_PROVIDER    = os.getenv("LLM_PROVIDER", "gemini")   # "gemini" or "ollama"
LLM_MODEL       = os.getenv("OLLAMA_MODEL", "mistral")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
```

**Step 4: Update `backend/rag_compliance/generation/chain.py`**
Replace the `ChatOllama` import block at the top with:
```python
import os
from rag_compliance.config import LLM_PROVIDER, LLM_MODEL, GEMINI_MODEL, GEMINI_API_KEY

def get_llm():
    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.1
        )
    else:
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(model=LLM_MODEL)

llm = get_llm()
```

**Step 5: Update `backend/rag_compliance/embeddings/embedder.py`**
Replace Ollama embeddings with sentence-transformers (runs on CPU, no Ollama needed):
```python
import os
from rag_compliance.config import EMBEDDING_MODEL

def get_embedding_function():
    provider = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model="nomic-embed-text")
    else:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
```
Add to `requirements.txt`:
```
langchain-huggingface
sentence-transformers
```

> ⚠️ **IMPORTANT:** After changing the embedding model, you MUST **rebuild the ChromaDB** with the new model. The vector dimensions will not match if you mix models. Run `python populate_database.py --reset` locally, then commit the new `chroma/` folder.

**Step 6: Update metadata extraction in `backend/rag_compliance/ingestion/metadata.py`**
```python
from rag_compliance.config import LLM_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL

def get_metadata_llm():
    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0
        )
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model="mistral", temperature=0, format="json")
```

---

### 9.3 Part B — Commit the ChromaDB to Git

The `chroma/` directory is your pre-built vector store. For free deployment on Render, you need to commit it to your repository so the backend can read it at runtime.

> ⚠️ **Note:** Render's free tier has **no persistent disk**. The `/chroma` folder must be part of the deployed code (i.e., committed to git), making it **read-only** at runtime. This is fine for a demo — the database is built once locally and shipped with the code.

1. Remove `chroma/` from `.gitignore` (if present)
2. Rebuild with sentence-transformers locally:
   ```bash
   cd backend
   EMBEDDING_PROVIDER=sentence_transformers python populate_database.py --reset
   ```
3. Commit the `chroma/` folder:
   ```bash
   git add backend/chroma/
   git commit -m "feat: add pre-built ChromaDB vector store for deployment"
   git push
   ```

> The `chroma/` folder is typically 50–200 MB. This is within GitHub's file size limits if individual files are under 100 MB. Use `git lfs` if any single file exceeds 100 MB.

---

### 9.4 Part C — Deploy Backend on Render (Free)

**Render Free Tier specs:** 1 vCPU, 512 MB RAM, sleeps after 15 min inactivity (30–60s cold start on first request).

1. Go to https://render.com → Sign up with GitHub
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo (`mca-compliance-rag`)
4. Configure the service:

| Setting | Value |
|---|---|
| **Name** | `complics-backend` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

5. Add **Environment Variables** in the Render dashboard:

| Key | Value |
|---|---|
| `LLM_PROVIDER` | `gemini` |
| `GEMINI_API_KEY` | `your-api-key-from-aistudio` |
| `GEMINI_MODEL` | `gemini-2.0-flash` |
| `EMBEDDING_PROVIDER` | `sentence_transformers` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` |

6. Click **"Create Web Service"** → Render will build and deploy automatically.
7. Your backend URL will be: `https://complics-backend.onrender.com`

---

### 9.5 Part D — Deploy Frontend on Vercel (Free)

1. Go to https://vercel.com → Sign up with GitHub
2. Click **"Add New Project"** → Import `mca-compliance-rag`
3. Configure:

| Setting | Value |
|---|---|
| **Root Directory** | `frontend` |
| **Framework Preset** | `Vite` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

4. Add **Environment Variable** (critical — points frontend to Render backend):

| Key | Value |
|---|---|
| `VITE_API_URL` | `https://complics-backend.onrender.com` |

5. **Update `CompliCS.jsx`** — change the hardcoded API URL:
   ```jsx
   // Line 35 in CompliCS.jsx — change from:
   const API_URL = "http://localhost:8000";
   // to:
   const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
   ```

6. Click **"Deploy"** → Your frontend URL: `https://complics.vercel.app`

---

### 9.6 Alternative: Deploy Both on a Single Free Service

If you want a simpler single-service deployment, you can use the **legacy Streamlit app** (`backend/app.py`) and deploy it on **Streamlit Community Cloud** (100% free):

1. Go to https://share.streamlit.io → Sign in with GitHub
2. Click **"New app"**
3. Configure:
   - **Repository:** `Khadaria/mca-compliance-rag`
   - **Branch:** `main`
   - **Main file path:** `backend/app.py`
4. Add secrets (equivalent of `.env`):
   ```toml
   # In Streamlit → "Advanced settings" → "Secrets"
   LLM_PROVIDER = "gemini"
   GEMINI_API_KEY = "your-key"
   GEMINI_MODEL = "gemini-2.0-flash"
   EMBEDDING_PROVIDER = "sentence_transformers"
   ```
5. Streamlit Cloud automatically installs from `requirements.txt` if it's in the same directory or root.

> **Limitation:** Streamlit Cloud has 1 GB RAM. Running `sentence-transformers` + ChromaDB may be tight. Test carefully.

---

### 9.7 Free Deployment Cost Summary

| Component | Service | Cost |
|---|---|---|
| Frontend (React) | Vercel Free | **$0/month** |
| Backend (FastAPI) | Render Free | **$0/month** |
| LLM | Google Gemini 2.0 Flash Free | **$0** (60 RPM limit) |
| Embeddings | sentence-transformers on Render | **$0** (CPU) |
| Vector Store | ChromaDB in-repo | **$0** |
| **Total** | | **$0/month** |

---

## 10. Known Issues & Gotchas

| Issue | Details |
|---|---|
| **Render cold starts** | Free tier sleeps after 15 min. First request after idle takes 30–60s. Add a loading message in the UI to warn users. |
| **512 MB RAM on Render** | `sentence-transformers` + `flashrank` + `chromadb` together may approach the limit. If OOM errors occur, consider using a lighter embedding model or disabling Flashrank reranking on the free tier. |
| **ChromaDB in git** | Pre-built vector store committed to git is a pragmatic workaround. If you update the corpus, you must rebuild locally and re-commit. |
| **Gemini rate limits** | Free tier: 60 requests/minute, 1,500 requests/day. For demo purposes this is fine. |
| **Mistral control tokens** | The backend already handles stripping `[INST]`, `[control_N]`, `[TOOL_RESULTS]` etc. from Mistral output in `server.py:_clean_llm_output()`. This is Mistral-specific; Gemini does not produce these. |
| **Hindi pages filtered** | `loader.py:is_hindi_heavy()` drops pages where >10% of characters are Devanagari. This is intentional as Hindi text degrades retrieval quality. |
| **Chunk size vs accuracy** | Current `chunk_size=600` is tuned for legal docs. Smaller chunks improve precision; larger chunks improve recall. Do not change without re-indexing. |
| **Session memory** | Chat history is in-memory in `server.py:session_store`. It resets on server restart. This is expected behavior for the current architecture. |
| **Legacy root-level `rag_compliance/`** | The `rag_compliance/` folder at the project root is from before the refactor. It does NOT have ingestion or config modules. Do not import from it. |
| **`chroma/` at root vs `backend/chroma/`** | There is a `chroma/` folder at the root (likely from the old app.py). The backend reads from `backend/chroma/`. Make sure you point `CHROMA_PATH` correctly. |

---

## 11. Extending the Project

### Add a new document to the corpus
1. Place the PDF in `backend/corpus_raw_v1/`
2. Run `python backend/populate_database.py` (without `--reset` to add incrementally)
3. If deploying: rebuild and re-commit `backend/chroma/`

### Switch to a different LLM (e.g., Groq, Together AI)
Both are compatible with LangChain:
```python
# Groq (free tier available at console.groq.com)
from langchain_groq import ChatGroq
llm = ChatGroq(model="llama3-8b-8192", groq_api_key=os.getenv("GROQ_API_KEY"))

# Together AI
from langchain_together import ChatTogether
llm = ChatTogether(model="meta-llama/Llama-3-8b-chat-hf", together_api_key=...)
```

### Add streaming to the frontend
Currently the frontend waits for the full response. To add token streaming:
1. Change the backend to use `StreamingResponse` from FastAPI
2. Update `CompliCS.jsx` to use `fetch` with streaming reader

### Add persistent chat history (PostgreSQL)
Replace the in-memory `session_store` dict with:
```python
from langchain_community.chat_message_histories import PostgresChatMessageHistory
# Use Supabase free tier for PostgreSQL
```

---

## 12. Environment Variable Reference

| Variable | Used By | Description | Default |
|---|---|---|---|
| `LLM_PROVIDER` | `config.py` | `"gemini"` or `"ollama"` | `"ollama"` |
| `GEMINI_API_KEY` | `chain.py`, `metadata.py` | Google AI Studio API key | — |
| `GEMINI_MODEL` | `chain.py` | e.g. `"gemini-2.0-flash"` | `"gemini-2.0-flash"` |
| `OLLAMA_BASE_URL` | `chain.py` (when Ollama) | Local Ollama server | `http://localhost:11434` |
| `OLLAMA_MODEL` | `config.py` | e.g. `"mistral"`, `"gemma3:4b"` | `"mistral"` |
| `EMBEDDING_PROVIDER` | `embedder.py` | `"ollama"` or `"sentence_transformers"` | `"ollama"` |
| `EMBEDDING_MODEL` | `embedder.py` | Model name for embeddings | `"nomic-embed-text"` |
| `VITE_API_URL` | `CompliCS.jsx` | Backend URL for production | `http://localhost:8000` |

---

## 13. Dependency List

### Python (backend/requirements.txt)
```
langchain
langchain-core
langchain-community
langchain-chroma
langchain-ollama
langchain-google-genai      # add for Gemini
langchain-huggingface       # add for sentence-transformers
chromadb
rank-bm25
flashrank
pypdf
sentence-transformers       # add for cloud deployment
fastapi
uvicorn
streamlit
```

### JavaScript (frontend/package.json)
```json
"dependencies": {
  "lucide-react": "^1.7.0",
  "react": "^19.2.4",
  "react-dom": "^19.2.4"
},
"devDependencies": {
  "@tailwindcss/vite": "^4.2.2",
  "@vitejs/plugin-react": "^6.0.1",
  "vite": "^8.0.1"
}
```

---

## 14. Git Branch Structure (as observed)

| Branch | Description |
|---|---|
| `main` | Production-ready code with `backend/` + `frontend/` structure |
| `feature/rag-modularity-upgrade` | WIP branch with modularity improvements (stashed) |

---

## 15. Document Corpus Details

| File | Content | Size |
|---|---|---|
| Companies Act 2013 (amended 01.04.2021) | Full act, ~500 pages | 3 MB |
| LLP Act 2008 | Full LLP Act | 0.2 MB |
| LLP Rules, 2009 | Consolidated rules | 5.6 MB |
| Companies (Accounts) Rules, 2014 | Consolidated | 1.3 MB |
| Companies (Appointment of Directors) Rules | Consolidated | 1.4 MB |
| Companies (Incorporation) Rules, 2014 | Consolidated | 6.2 MB |
| Companies (Management & Administration) Rules | Consolidated | 2.1 MB |
| Ch9 Annexure Rules (x2) | Chapter 9 annexures | 1.3 MB each |
| Form DIR-3-KYC | Director KYC form | 0.35 MB |
| Form INC-20A | Declaration of commencement | 1.2 MB |
| Form INC-22 | Notice of situation of office | 1.5 MB |
| Form MGT-7 | Annual return form | 0.73 MB |
| Form 8 LLP | Statement of Account | 0.56 MB |
| Form 11 LLP | Annual return form for LLP | 0.29 MB |

All documents are publicly available from the Ministry of Corporate Affairs (MCA) website.

---

*Last updated: April 2026 | Generated from full repository analysis*
