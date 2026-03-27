# 📚 MCA Compliance RAG Assistant

An AI-powered legal compliance assistant built using a Retrieval-Augmented Generation (RAG) pipeline, designed to answer questions about Indian corporate law — specifically the **Companies Act 2013** and the **LLP Act 2008**.

---

## 🧠 Overview

**CompliCS** is a conversational RAG system that retrieves relevant statutory provisions from a curated corpus of MCA (Ministry of Corporate Affairs) documents and generates accurate, context-grounded answers using a local LLM via Ollama.

Key capabilities:
- **Hybrid Retrieval**: Combines semantic vector search (ChromaDB + MMR) with keyword-based BM25 retrieval for high-recall, precise document matching.
- **LLM-assisted Reranking**: Uses FlashRank to reorder retrieved chunks by actual relevance to the user query.
- **LLM Metadata Extraction**: Extracts act names and section references from document chunks at ingestion time to enrich citations.
- **Conversational Memory**: Maintains multi-turn chat history using LangChain's `RunnableWithMessageHistory`.
- **Hindi Filtering**: Skips pages containing non-Latin script during document loading to ensure clean ingestion.
- **Streamlit UI**: A simple, interactive chat interface with expandable source references.

---

## 🗂️ Project Structure

```
mca-compliance-rag/
├── app.py                      # Streamlit chat application entry point
├── populate_database.py        # Ingestion script: load → chunk → enrich → store
├── requirements.txt
├── corpus_raw_v1/              # Source PDF documents (MCA statutes)
├── chroma/                     # Persisted ChromaDB vector store
└── rag_compliance/             # Core modular RAG package
    ├── config.py               # Central config (paths, model names)
    ├── embeddings/
    │   └── embedder.py         # Embedding function (Ollama)
    ├── ingestion/
    │   ├── loader.py           # PDF loading + Hindi script filtering
    │   ├── chunker.py          # Recursive character text splitting
    │   └── metadata.py         # LLM-assisted metadata enrichment
    ├── retrieval/
    │   ├── hybrid_retriever.py # BM25 + Vector MMR hybrid retriever
    │   └── reranker.py         # FlashRank-based cross-encoder reranker
    └── generation/
        ├── prompts.py          # System prompt template
        └── chain.py            # RAG chain: retrieve → rerank → generate
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running locally

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Pull the Required Ollama Model

```bash
ollama pull llama3.2
```
> The model name can be configured in `rag_compliance/config.py`.

### Populate the Vector Database

Place your PDF documents in the `corpus_raw_v1/` directory, then run:

```bash
python populate_database.py
```

To reset and rebuild the database from scratch:

```bash
python populate_database.py --reset
```

### Run the App

```bash
streamlit run app.py
```

---

## 🔍 How It Works

```
User Query
    │
    ▼
Hybrid Retriever
  ├── Vector Store (ChromaDB + MMR, k=20)
  └── BM25 Retriever (keyword match, k=20)
    │
    ▼
Merged & Deduplicated Document Pool
    │
    ▼
FlashRank Reranker (top_k=5)
    │
    ▼
LLM (Ollama) + Chat History
    │
    ▼
Streamed Answer + Source Citations
```

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| LLM Framework | LangChain, LangChain-Community, LangChain-Core |
| LLM Inference | Ollama (local) |
| Vector Store | ChromaDB |
| Embeddings | Ollama Embeddings |
| Keyword Retrieval | BM25 (rank-bm25) |
| Reranking | FlashRank |
| Document Parsing | PyPDF |
| UI | Streamlit |

---

## 📄 License

[MIT](LICENSE)
