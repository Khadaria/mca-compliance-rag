from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import your existing generation function
from rag_compliance.generation.chain import process_query_with_rag
app = FastAPI(title="CompliCS API", description="MCA Compliance RAG API")

# Allow CORS so the React frontend can communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend URL (e.g., "http://localhost:3000")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request data structure
from fastapi import FastAPI
from pydantic import BaseModel

from rag_compliance.generation.chain import process_query_with_rag

app = FastAPI()

class QueryRequest(BaseModel):
    question: str


# Dummy session history (needed for your chain)
def get_session_history(session_id: str):
    return []


@app.post("/query")
def query_rag(request: QueryRequest):
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

if __name__ == "__main__":
    print("🚀 Starting CompliCS Backend Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)