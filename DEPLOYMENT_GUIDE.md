# Deployment Guide

This guide matches the current repository state.

Target deployment:
- frontend: Vercel
- backend: Render web service
- LLM: Groq
- embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- vector store: Pinecone

No Docker is required.

## Architecture You Are Deploying

The frontend is a Vite app that calls:
- `POST /query`
- `GET /health`

The backend is a FastAPI app that:
- connects to a Pinecone index
- retrieves with hybrid search
- reranks with Flashrank
- sends grounded prompts to Groq

## Before You Deploy

You need:
- a GitHub repo with this project pushed
- a Groq API key
- a Pinecone API key
- a Pinecone index populated with embeddings built using `all-MiniLM-L6-v2`

## Step 1. Get a Groq API Key

1. Go to `https://console.groq.com`
2. Create an API key
3. Save it for Render

## Step 2. Build the Pinecone Index

From the repo root:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:EMBEDDING_MODEL="all-MiniLM-L6-v2"
$env:PINECONE_API_KEY="your_pinecone_key"
$env:PINECONE_INDEX="complics-index"
$env:PINECONE_NAMESPACE="default"
$env:PINECONE_CLOUD="aws"
$env:PINECONE_REGION="us-east-1"
python populate_database.py --reset
```

What this does:
- clears the configured Pinecone namespace
- loads the PDFs in `backend/corpus_raw_v1`
- chunks them
- embeds with `all-MiniLM-L6-v2`
- stores the new vectors in Pinecone

## Step 3. Commit the Deployment Files

Make sure these are committed:
- backend code
- frontend code
- `render.yaml`
- updated docs

Check:

```powershell
git status
```

Commit and push:

```powershell
git add .
git commit -m "Prepare Groq-based no-Docker deployment"
git push origin main
```

## Step 4. Deploy the Backend on Render

### Option A: Use `render.yaml`

This repo includes [render.yaml](c:/Users/khada/OneDrive/Documents/GitHub/mca-compliance-rag/render.yaml). On Render:

1. Go to `https://render.com`
2. Click `New +`
3. Choose `Blueprint`
4. Connect your GitHub repo
5. Render will read `render.yaml`

Then add your Groq and Pinecone keys in the service environment settings.

### Option B: Create a Web Service Manually

Use these settings:
- Name: `complics-backend`
- Runtime: `Python 3`
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

Environment variables:
- `GROQ_API_KEY=your_actual_key`
- `GROQ_MODEL=llama-3.3-70b-versatile`
- `EMBEDDING_MODEL=all-MiniLM-L6-v2`
- `PINECONE_API_KEY=your_actual_key`
- `PINECONE_INDEX=complics-index`
- `PINECONE_NAMESPACE=default`
- `PINECONE_CLOUD=aws`
- `PINECONE_REGION=us-east-1`
- `PINECONE_DIMENSION=384`

After deploy, test:

```text
https://your-render-service.onrender.com/health
```

Expected response:

```json
{"status":"ok"}
```

## Step 5. Deploy the Frontend on Vercel

1. Go to `https://vercel.com`
2. Import the GitHub repo
3. Set the root directory to `frontend`
4. Keep the detected Vite build settings

Add this environment variable:
- `VITE_API_URL=https://your-render-service.onrender.com`

Deploy the project.

## Step 6. Test End-to-End

After both services are live:
1. Open the Vercel URL
2. Ask a compliance question
3. Confirm:
- you get an answer
- sources appear in the right pane
- no connection error is shown

## Common Problems

### 1. Pinecone dimension mismatch

Cause:
- the Pinecone index was created with a different embedding dimension or embedding model

Fix:
- recreate or repopulate the Pinecone index with `all-MiniLM-L6-v2`
- redeploy

### 2. Backend crashes on startup

Check:
- `GROQ_API_KEY` is set
- `PINECONE_API_KEY` is set
- `PINECONE_INDEX` exists and contains vectors
- `requirements.txt` installed cleanly

### 3. Frontend cannot reach backend

Check:
- `VITE_API_URL` points to the Render URL
- backend `/health` works
- Render service is awake

### 4. First request is slow

This is expected on free Render:
- cold starts can add delay
- the embedding model may download on first boot if not cached

## Exact Deployment Checklist

- Pinecone index exists and is populated
- `GROQ_API_KEY` ready
- `PINECONE_API_KEY` ready
- code pushed to GitHub
- Render backend deployed
- backend `/health` returns `{"status":"ok"}`
- Vercel frontend deployed
- `VITE_API_URL` points to the Render backend
- end-to-end query works
