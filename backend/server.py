from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import traceback

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