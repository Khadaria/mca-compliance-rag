"""
One-off comparison runner (not part of the app). Runs a fixed set of test
queries through the real /query handler logic in server.py -- same
generation prompt, same post-processing -- against whichever Chroma store
CHROMA_PATH_OVERRIDE points at, and writes the answers+sources to a JSON
file so two separate process runs (old store vs chroma_v2) can be diffed.

Usage:
    CHROMA_PATH_OVERRIDE=chroma_v2 python scripts/compare_stores.py chroma_v2 > /tmp/v2.json
    python scripts/compare_stores.py old > /tmp/old.json
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

QUERIES = [
    "What are the requirements for a company to have a Board of Directors under Section 149?",
    "Who is disqualified from being appointed as a director under Section 164?",
    "What is the right of a person other than a retiring director to stand for directorship under Section 160?",
    "What documents are required for incorporation of a company under the Companies (Incorporation) Rules, 2014?",
    "What are the qualifications required for an independent director under the Companies (Appointment and Qualification of Directors) Rules, 2014?",
    "What is the penalty for a limited liability partnership that fails to file its annual return under the LLP Act?",
    "When should Form DIR-3 KYC be filed?",
    "What is the maximum number of directors a company can appoint without a special resolution?",
]


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    out_path = sys.argv[2]
    from server import query_rag, QueryRequest  # noqa: E402  (import after sys.path/env setup)

    results = []
    for q in QUERIES:
        print(f"[{label}] running: {q}", file=sys.stderr)
        resp = query_rag(QueryRequest(question=q))
        results.append({"query": q, "answer": resp["answer"], "sources": resp["sources"]})

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"label": label, "results": results}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
