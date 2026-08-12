"""
Verification aid for the legal_parser rewrite -- not part of the ingestion
pipeline. Inspects chunks in a Chroma store directly (by section/rule
number) and exercises the hybrid retriever's RRF fusion, so chunk quality
can be checked before chroma_v2 is promoted to production.

Usage (from backend/):
    python scripts/inspect_retrieval.py --section 149
    python scripts/inspect_retrieval.py --query "penalty for non-appointment of independent director"
    python scripts/inspect_retrieval.py --section 149 --chroma-path chroma_v2
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_chroma import Chroma

from rag_compliance.config import CHROMA_V2_PATH
from rag_compliance.embeddings.embedder import get_embedding_function


def inspect_section(chroma_path: str, section: str):
    """Matches bare section numbers (e.g. "160") as well as sub-section-split
    keys (e.g. "160(1)", "160(2)") produced when a section was too large to
    keep as one chunk."""
    db = Chroma(persist_directory=chroma_path, embedding_function=get_embedding_function())
    result = db.get()
    pairs = [
        (m, d) for m, d in zip(result.get("metadatas", []), result.get("documents", []))
        if str(m.get("section", "")) == section or str(m.get("section", "")).startswith(f"{section}(")
    ]
    docs = [d for _, d in pairs]
    metas = [m for m, _ in pairs]

    if not docs:
        print(f"No chunks found with section == '{section}' (or '{section}(N)')")
        return

    print(f"Found {len(docs)} chunk(s) for section '{section}':\n")
    for i, (text, meta) in enumerate(zip(docs, metas)):
        print(f"--- chunk {i + 1} ---")
        print(f"metadata: {meta}")
        print(f"text:\n{text}\n")


def inspect_query(chroma_path: str, query: str):
    os.environ["CHROMA_PATH_OVERRIDE"] = chroma_path
    from rag_compliance.retrieval.hybrid_retriever import get_hybrid_retriever

    retriever = get_hybrid_retriever()
    docs = retriever.get_relevant_documents(query) if hasattr(retriever, "get_relevant_documents") else retriever.invoke(query)

    print(f"Top {min(10, len(docs))} fused results for query: {query!r}\n")
    for i, doc in enumerate(docs[:10]):
        meta = doc.metadata
        print(f"--- result {i + 1} ---")
        print(f"section={meta.get('section')} subsection={meta.get('subsection')} "
              f"act={meta.get('act')} page={meta.get('page')}")
        print(f"text: {doc.page_content[:200]}...\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", help="Bare section/rule number to look up, e.g. 149")
    parser.add_argument("--query", help="Natural-language query to run through the hybrid retriever")
    parser.add_argument("--chroma-path", default=CHROMA_V2_PATH, help="Chroma store to inspect (defaults to chroma_v2)")
    args = parser.parse_args()

    if args.section:
        inspect_section(args.chroma_path, args.section)
    if args.query:
        inspect_query(args.chroma_path, args.query)
    if not args.section and not args.query:
        parser.print_help()
