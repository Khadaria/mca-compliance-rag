from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import traceback
import re

from langchain_community.chat_message_histories import ChatMessageHistory
from rag_compliance.generation.chain import process_query_with_rag

app = FastAPI(title="CompliCS API", description="MCA Compliance RAG API")

# Allow CORS so the React frontend can communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


# In-memory session histories keyed by session_id
session_store: dict[str, ChatMessageHistory] = {}


def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]


# Phrases that indicate the LLM declined to answer (out-of-scope / not in context)
_DECLINE_PHRASES = [
    "not available in the provided statutory context",
    "not available in the provided context",
    "does not relate to indian corporate law",
    "outside the scope",
    "outside my scope",
    "beyond my scope",
    "not within my area",
    "i am unable to answer",
    "i cannot answer",
    "i'm unable to answer",
    "not related to",
    "does not pertain to",
    "i specialize in indian corporate law",
    "i am an ai-powered legal compliance",
    "as complics, i",
]


def _is_out_of_scope(response_text: str) -> bool:
    """Check if the LLM response indicates the question was out of scope."""
    lower = response_text.lower()
    return any(phrase in lower for phrase in _DECLINE_PHRASES)


def _clean_llm_output(text: str) -> str:
    """Remove code fences, control tokens, and other LLM artifacts from the response."""
    # Remove fenced code blocks (multiline)
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove stray triple backticks
    text = text.replace('```', '')
    # Remove Mistral control tokens: [control_XX], [TOOL_RESULTS], [INST], [/INST], etc.
    text = re.sub(r'\[control_\d+\]', '', text)
    text = re.sub(r'\[/?TOOL_RESULTS\]', '', text)
    text = re.sub(r'\[/?INST\]', '', text)
    text = re.sub(r'\[/?AVAILABLE_TOOLS\]', '', text)
    # Remove any remaining bracketed internal tokens (e.g. [SYS], [/SYS])
    text = re.sub(r'\[/?[A-Z_]{2,}\]', '', text)
    # Clean up excessive whitespace left behind
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _is_garbage_response(text: str) -> bool:
    """Check if the response is mostly garbage (control tokens, empty after cleaning)."""
    # Strip all whitespace and check if there's meaningful content
    stripped = re.sub(r'\s+', '', text)
    return len(stripped) < 20


@app.post("/query")
def query_rag(request: QueryRequest):
    try:
        stream, sources = process_query_with_rag(
            query=request.question,
            session_id="default",
            get_session_history_func=get_session_history
        )

        # Convert stream → final text
        response_text = ""
        for chunk in stream:
            if hasattr(chunk, "content"):
                response_text += chunk.content
            else:
                response_text += str(chunk)

        # Post-process: strip code fences, control tokens, and other LLM artifacts
        response_text = _clean_llm_output(response_text)

        # If the response is garbage after cleaning, return a retry message
        if _is_garbage_response(response_text):
            print(f"[Server] Garbage response detected after cleaning — asking user to retry")
            response_text = "I apologize, but I encountered an issue generating a response. Please try asking your question again."
            sources = []

        # Suppress sources if the response is out-of-scope or a greeting
        if _is_out_of_scope(response_text) or not sources:
            print(f"[Server] Out-of-scope or no relevant sources detected — suppressing citations")
            sources = []

        return {
            "answer": response_text,
            "sources": sources
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "answer": f"⚠️ Server Error: {str(e)}",
            "sources": []
        }


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    print("🚀 Starting CompliCS Backend Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)