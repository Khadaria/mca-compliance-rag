# CompliCS — Step-by-Step Free Deployment Guide

**Stack after deployment:**
- 🟢 Frontend → Vercel (free forever)
- 🟢 Backend → Render (free, ~30s cold start after idle)
- 🟢 LLM → Groq API **or** Gemini API (both free)
- 🟢 Embeddings → sentence-transformers `all-MiniLM-L6-v2` (runs in-process, no Ollama)
- 🟢 Vector DB → ChromaDB committed to git (read-only, built once locally)

**Total cost: $0/month**

---

## Why We Can't Use Ollama on Free Cloud Hosts

Ollama works by running a **background server** on `http://localhost:11434`. When you run the backend on Render, only one process runs (your `uvicorn` server). There is no Ollama process running alongside it. Any call to `OllamaEmbeddings` or `ChatOllama` will fail with a connection error.

`sentence-transformers` solves this because it loads the model **directly inside Python** — no separate server needed. The `all-MiniLM-L6-v2` model is ~80 MB and works fine on CPU with 512 MB RAM.

---

## Part 0 — Prerequisites (Do This First)

Before making any changes, make sure:
- [ ] Your repo is on GitHub at `github.com/Khadaria/mca-compliance-rag`
- [ ] You are on the `main` branch
- [ ] Python 3.10+ is installed locally
- [ ] Node.js 18+ is installed locally
- [ ] Ollama is installed locally (needed to rebuild the vector DB one last time)

Check your branch:
```bash
git checkout main
git status
```

---

## Part 1 — Get Your Free API Key

### Option A: Groq (Recommended — faster, higher limits)

1. Go to **https://console.groq.com**
2. Sign up with Google or GitHub
3. Go to **"API Keys"** in the left sidebar
4. Click **"Create API Key"** → give it a name like `complics-deployment`
5. Copy the key — it looks like `gsk_xxxxxxxxxxxxxxxxxxxx`
6. Save it somewhere safe (you'll need it in Part 4)

### Option B: Google Gemini

1. Go to **https://aistudio.google.com**
2. Sign in with Google
3. Click **"Get API key"** in the top-right
4. Click **"Create API key"** → select a project or create one
5. Copy the key — it looks like `AIzaSyxxxxxxxxxxxxxxx`
6. Save it somewhere safe

---

## Part 2 — Code Changes (Local)

Open your project in VS Code. You will make changes to **5 files**.

### 2.1 — Update `backend/requirements.txt`

Open `backend/requirements.txt` and replace the entire contents with:

```
# AI & LLM Framework
langchain
langchain-core
langchain-community
langchain-chroma
langchain-ollama

# LLM Providers (cloud, free tier)
langchain-groq
langchain-google-genai

# Embeddings (runs locally in-process, no Ollama server needed)
langchain-huggingface
sentence-transformers

# Vector Database
chromadb

# Retrieval Enhancements
rank-bm25
flashrank

# Document Processing
pypdf

# User Interface
streamlit
fastapi
uvicorn
```

---

### 2.2 — Update `backend/rag_compliance/config.py`

Open `backend/rag_compliance/config.py` and replace everything with:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_PATH = str(BASE_DIR / "chroma")
DATA_PATH = str(BASE_DIR / "corpus_raw_v1")

# LLM Provider: "groq", "gemini", or "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# Groq settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Ollama settings (local only)
LLM_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Embedding: "sentence_transformers" or "ollama"
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
```

---

### 2.3 — Update `backend/rag_compliance/embeddings/embedder.py`

Open `backend/rag_compliance/embeddings/embedder.py` and replace everything with:

```python
import os
from rag_compliance.config import EMBEDDING_PROVIDER, EMBEDDING_MODEL


def get_embedding_function():
    provider = EMBEDDING_PROVIDER

    if provider == "sentence_transformers":
        from langchain_huggingface import HuggingFaceEmbeddings
        # all-MiniLM-L6-v2 is ~80 MB, runs on CPU, no server needed
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    else:
        # Default: Ollama (for local development only)
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model=EMBEDDING_MODEL)
```

---

### 2.4 — Update `backend/rag_compliance/generation/chain.py`

Open `backend/rag_compliance/generation/chain.py` and replace everything with:

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from rag_compliance.config import (
    LLM_PROVIDER, LLM_MODEL,
    GROQ_API_KEY, GROQ_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL
)
from rag_compliance.generation.prompts import PROMPT_TEMPLATE
from rag_compliance.retrieval.hybrid_retriever import get_hybrid_retriever
from rag_compliance.retrieval.reranker import ComponentReranker


def get_llm():
    """Return the LLM based on LLM_PROVIDER environment variable."""
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=0.1
        )
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.1
        )
    else:
        # Default: Ollama (local development)
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(model=LLM_MODEL)


# Initialize once at module load (important for performance)
llm = get_llm()
hybrid_retriever = get_hybrid_retriever()
reranker = ComponentReranker()


def create_conversational_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", PROMPT_TEMPLATE),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "Context:\n{context}\n\nQuestion:\n{question}")
    ])
    chain = prompt | llm
    return chain


def process_query_with_rag(query: str, session_id: str, get_session_history_func):
    """
    1. Retrieve documents via hybrid search
    2. Rerank with Flashrank
    3. Generate response with context
    """

    # 1. Retrieve
    if hasattr(hybrid_retriever, "get_relevant_documents"):
        raw_docs = hybrid_retriever.get_relevant_documents(query)
    else:
        raw_docs = hybrid_retriever.invoke(query)

    # 2. Rerank
    reranked_docs = reranker.rerank(query, raw_docs, top_k=5)

    # 3. Build context string
    context = "\n\n---\n\n".join([doc.page_content for doc in reranked_docs])

    # 4. Extract sources for citation
    sources = []
    seen = set()
    for doc in reranked_docs:
        source_name = doc.metadata.get("source", "Unknown Document")
        act = doc.metadata.get("act", "Unknown Act")
        section = doc.metadata.get("section", "Unknown Section")

        if act != "Unknown Act" and section != "Unknown Section":
            label = f"{source_name} (Extracted: {act}, {section})"
        else:
            label = source_name

        if "/" in label or "\\" in label:
            label = label.replace("\\", "/").split("/")[-1]

        key = (label, doc.metadata.get("page", 1))
        if key not in seen:
            snippet = doc.page_content.strip()
            if len(snippet) > 200:
                snippet = snippet[:197] + "..."

            sources.append({
                "doc": label,
                "page": doc.metadata.get("page", 1),
                "text": snippet
            })
            seen.add(key)

    # 5. Build conversational chain
    chain = create_conversational_chain()

    conversational_chain = RunnableWithMessageHistory(
        chain,
        get_session_history_func,
        input_messages_key="question",
        history_messages_key="chat_history",
    )

    # 6. Stream response
    stream = conversational_chain.stream(
        {"question": query, "context": context},
        config={"configurable": {"session_id": session_id}}
    )

    return stream, sources
```

---

### 2.5 — Update `backend/rag_compliance/ingestion/metadata.py`

Open `backend/rag_compliance/ingestion/metadata.py` and replace everything with:

```python
import json
from langchain_core.prompts import PromptTemplate
from rag_compliance.config import LLM_PROVIDER, GROQ_API_KEY, GROQ_MODEL, GEMINI_API_KEY, GEMINI_MODEL, LLM_MODEL
from rag_compliance.generation.prompts import METADATA_EXTRACTION_PROMPT


def get_metadata_llm():
    """Return a zero-temperature LLM for structured metadata extraction."""
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, temperature=0)
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY, temperature=0)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=LLM_MODEL, temperature=0, format="json")


def extract_metadata_for_chunk(text: str, chain) -> dict:
    try:
        response = chain.invoke({"text": text[:500]})
        content = response.content.strip()

        # Strip markdown code fences if present (Groq/Gemini may add them)
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        try:
            data = json.loads(content)
        except Exception:
            return {"act": "Unknown", "section": "Unknown", "topic": "Unknown"}

        return data

    except Exception:
        return {"act": "Unknown", "section": "Unknown", "topic": "Unknown"}


def enrich_chunks_with_metadata(chunks: list) -> list:
    print("Initializing LLM for metadata extraction...")
    llm = get_metadata_llm()
    prompt = PromptTemplate.from_template(METADATA_EXTRACTION_PROMPT)
    chain = prompt | llm

    print(f"Extracting metadata for {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks):
        if i % 50 == 0:
            print(f"Processed {i}/{len(chunks)} chunks...")

        metadata = extract_metadata_for_chunk(chunk.page_content, chain)

        if isinstance(metadata, dict):
            for key, val in metadata.items():
                chunk.metadata[key] = str(val)

        if "source" not in chunk.metadata:
            chunk.metadata["source"] = "Unknown Source"

    print("Metadata extraction completed.")
    return chunks
```

---

### 2.6 — Update `frontend/src/CompliCS.jsx` (1 line change)

Open `frontend/src/CompliCS.jsx` and find **line 35**:

```jsx
const API_URL = "http://localhost:8000";
```

Change it to:

```jsx
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

That's it — one line. This lets Vercel inject your Render backend URL at build time.

---

## Part 3 — Rebuild the ChromaDB Vector Store

> **Why rebuild?** You're switching from `nomic-embed-text` (768-dimensional vectors) to `all-MiniLM-L6-v2` (384-dimensional vectors). The dimensions don't match — old vectors in ChromaDB will not work with the new model. You must wipe and rebuild.

This step requires Ollama running locally (for metadata extraction with Mistral). After this, Ollama is no longer needed.

### Step 1 — Install new dependencies locally

```bash
cd backend
pip install langchain-huggingface sentence-transformers langchain-groq langchain-google-genai
```

### Step 2 — Set environment variables for the rebuild

**On Windows (PowerShell):**
```powershell
$env:LLM_PROVIDER = "ollama"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "all-MiniLM-L6-v2"
```

> We keep `LLM_PROVIDER=ollama` for the rebuild because metadata extraction calls the LLM many times (once per chunk) — using Groq/Gemini free tier here would hit rate limits. Ollama runs locally with no limits.

### Step 3 — Make sure Ollama is running

```bash
ollama serve
# In a separate terminal, verify:
ollama list
# Should show: mistral, nomic-embed-text
```

### Step 4 — Wipe and rebuild the database

```bash
cd backend
python populate_database.py --reset
```

This will:
1. Delete `backend/chroma/` (the old vectors)
2. Load all 15 PDFs from `corpus_raw_v1/`
3. Filter Hindi/noise pages
4. Chunk with legal-aware splitter
5. Extract metadata with Mistral (via Ollama locally)
6. Embed with `all-MiniLM-L6-v2` (sentence-transformers, no Ollama needed)
7. Save to `backend/chroma/`

**⏱ Expected time: 20–45 minutes** (metadata extraction is the slow step)

### Step 5 — Verify it worked

```bash
# Quick test — start the backend with Groq
$env:LLM_PROVIDER = "groq"
$env:GROQ_API_KEY = "gsk_your_key_here"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
cd backend
python server.py
```

Open another terminal:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is Section 164 of the Companies Act?\"}"
```

You should get a proper legal answer with sources.

---

## Part 4 — Commit Everything to Git

### Step 1 — Check what needs to be committed

```bash
cd c:\Users\khada\OneDrive\Documents\GitHub\mca-compliance-rag
git status
```

You should see changes in:
- `backend/requirements.txt`
- `backend/rag_compliance/config.py`
- `backend/rag_compliance/embeddings/embedder.py`
- `backend/rag_compliance/generation/chain.py`
- `backend/rag_compliance/ingestion/metadata.py`
- `frontend/src/CompliCS.jsx`
- `backend/chroma/` (new files — the rebuilt vector store)

### Step 2 — Check if `chroma/` is in .gitignore

```bash
cat .gitignore
```

If you see a line with `chroma` or `chroma/`, remove it so git tracks the folder.

```bash
# Open .gitignore and delete or comment out the line:
# chroma/
```

### Step 3 — Stage and commit

```bash
git add backend/requirements.txt
git add backend/rag_compliance/config.py
git add backend/rag_compliance/embeddings/embedder.py
git add backend/rag_compliance/generation/chain.py
git add backend/rag_compliance/ingestion/metadata.py
git add frontend/src/CompliCS.jsx
git add backend/chroma/
git add .gitignore

git commit -m "feat: migrate to Groq + sentence-transformers for free cloud deployment

- Switch LLM to Groq (llama-3.3-70b-versatile) with Gemini fallback
- Switch embeddings to sentence-transformers all-MiniLM-L6-v2 (no Ollama server)
- Rebuild ChromaDB with new embedding model
- Add VITE_API_URL env var support to frontend
- Update config.py to read all settings from env vars"

git push origin main
```

> ⚠️ If `backend/chroma/` is large (>100 MB total), GitHub may reject the push. Check the size:
> ```bash
> du -sh backend/chroma/
> ```
> If any single file is >100 MB, you need Git LFS:
> ```bash
> git lfs install
> git lfs track "backend/chroma/**"
> git add .gitattributes
> git commit -m "chore: track chroma with git lfs"
> ```

---

## Part 5 — Deploy Backend on Render

### Step 1 — Create a Render account

1. Go to **https://render.com**
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (makes connecting your repo easy)

### Step 2 — Create a new Web Service

1. In the Render dashboard, click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"**
3. Find and select `Khadaria/mca-compliance-rag`
4. Click **"Connect"**

### Step 3 — Configure the service

Fill in the settings exactly as shown:

| Field | Value |
|---|---|
| **Name** | `complics-backend` |
| **Region** | Singapore (closest to India) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

### Step 4 — Add environment variables

Scroll down to **"Environment Variables"** section. Click **"Add Environment Variable"** for each:

**If using Groq:**

| Key | Value |
|---|---|
| `LLM_PROVIDER` | `groq` |
| `GROQ_API_KEY` | `gsk_your_actual_key_here` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `EMBEDDING_PROVIDER` | `sentence_transformers` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` |

**If using Gemini instead:**

| Key | Value |
|---|---|
| `LLM_PROVIDER` | `gemini` |
| `GEMINI_API_KEY` | `AIzaSy_your_actual_key_here` |
| `GEMINI_MODEL` | `gemini-2.0-flash` |
| `EMBEDDING_PROVIDER` | `sentence_transformers` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` |

### Step 5 — Deploy

Click **"Create Web Service"**.

Render will:
1. Clone your repo
2. Run `pip install -r requirements.txt` (takes ~3–5 minutes — sentence-transformers downloads the model)
3. Start `uvicorn server:app`

Watch the build logs. When you see:
```
INFO:     Uvicorn running on http://0.0.0.0:XXXXX
```
it's live.

### Step 6 — Test the backend

Your backend URL will be something like:
`https://complics-backend.onrender.com`

Test it:
```
https://complics-backend.onrender.com/health
```
Should return: `{"status":"ok"}`

> **Note:** The first startup takes ~2–3 minutes because `sentence-transformers` downloads the model file (~80 MB). Subsequent cold starts will be 30–60 seconds.

---

## Part 6 — Deploy Frontend on Vercel

### Step 1 — Create a Vercel account

1. Go to **https://vercel.com**
2. Click **"Sign Up"** → choose **"Continue with GitHub"**

### Step 2 — Import your project

1. In the Vercel dashboard, click **"Add New..."** → **"Project"**
2. Find `Khadaria/mca-compliance-rag` in the list
3. Click **"Import"**

### Step 3 — Configure the project

Vercel will auto-detect but you need to set the root directory:

| Field | Value |
|---|---|
| **Root Directory** | `frontend` |
| **Framework Preset** | Vite (auto-detected) |
| **Build Command** | `npm run build` (auto-filled) |
| **Output Directory** | `dist` (auto-filled) |

### Step 4 — Add environment variable

Click **"Environment Variables"** and add:

| Name | Value |
|---|---|
| `VITE_API_URL` | `https://complics-backend.onrender.com` |

> Replace `complics-backend` with your actual Render service name from Step 5.

### Step 5 — Deploy

Click **"Deploy"**.

Vercel will:
1. Run `npm install`
2. Run `npm run build`
3. Deploy to CDN

In ~2 minutes you'll get a URL like:
`https://complics-xxxxxxx.vercel.app`

### Step 6 — Test the full application

1. Open your Vercel URL
2. Click "Enter Workspace"
3. Try a query: *"What is the penalty for a director who fails to disclose interest?"*
4. You should see an answer + legal sources panel

---

## Part 7 — Set Up a Custom Domain (Optional, Free)

Vercel gives you a free subdomain. If you want `complics.vercel.app` instead of `complics-xxxxxxx.vercel.app`:

1. Vercel Dashboard → Your project → **"Settings"** → **"Domains"**
2. Type `complics` → it becomes `complics.vercel.app` if available

---

## Troubleshooting

### Backend crashes on startup ("Connection refused" or "Model not found")
- Make sure all 5 env vars are set in Render
- Check Render logs: Dashboard → complics-backend → "Logs"

### Frontend shows "Could not reach the CompliCS backend server"
- Check that `VITE_API_URL` is set correctly in Vercel (must be `https://..., not `http://`)
- Check the Render backend health endpoint directly in a browser
- Wait for cold start (~60s on first request after idle)

### "dimension mismatch" error from ChromaDB
- This means the committed `chroma/` was built with `nomic-embed-text` (768-dim) but the code now uses `all-MiniLM-L6-v2` (384-dim)
- Fix: rebuild locally with `EMBEDDING_PROVIDER=sentence_transformers python populate_database.py --reset` and re-commit

### Render build fails with "ModuleNotFoundError"
- Make sure `backend/requirements.txt` has all new packages (`langchain-groq`, `langchain-huggingface`, `sentence-transformers`)
- Check that the Root Directory in Render is set to `backend`

### Groq rate limit hit ("429 Too Many Requests")
- Free tier: 30 RPM, 14,400/day for `llama-3.3-70b-versatile`
- Switch to `llama3-8b-8192` for lighter usage (same key, just change `GROQ_MODEL`)
- Or switch `LLM_PROVIDER` to `gemini` as a backup

---

## Summary Checklist

```
[ ] Part 0: On main branch, prerequisites ready
[ ] Part 1: Got Groq or Gemini API key
[ ] Part 2: Updated 5 files (requirements.txt, config.py, embedder.py, chain.py, metadata.py, CompliCS.jsx)
[ ] Part 3: Rebuilt ChromaDB with sentence-transformers
[ ] Part 3: Tested locally with Groq/Gemini
[ ] Part 4: Committed all changes + chroma/ to git, pushed to main
[ ] Part 5: Created Render Web Service with correct settings + env vars
[ ] Part 5: Verified /health endpoint is live
[ ] Part 6: Created Vercel project with VITE_API_URL set
[ ] Part 6: Tested end-to-end chat in deployed frontend
```

---

*Total estimated time: 1.5–2 hours (most of it is the ChromaDB rebuild in Part 3)*
