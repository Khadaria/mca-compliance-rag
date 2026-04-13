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