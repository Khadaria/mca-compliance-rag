from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from rag_compliance.config import LLM_MODEL
from rag_compliance.generation.prompts import PROMPT_TEMPLATE
from rag_compliance.retrieval.hybrid_retriever import get_hybrid_retriever
from rag_compliance.retrieval.reranker import ComponentReranker

# Initialize once (important for performance)
llm = ChatOllama(model=LLM_MODEL)
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
    1. Retrieve documents
    2. Rerank documents
    3. Generate response with context
    """

    # ✅ Retrieval (fixed)
    if hasattr(hybrid_retriever, "get_relevant_documents"):
        raw_docs = hybrid_retriever.get_relevant_documents(query)
    else:
        # fallback (if only vector retriever returned)
        raw_docs = hybrid_retriever.invoke(query)

    # 2. Reranking
    reranked_docs = reranker.rerank(query, raw_docs, top_k=5)

    # Build context
    context = "\n\n---\n\n".join([doc.page_content for doc in reranked_docs])

    # Extract sources
    sources = []
    for doc in reranked_docs:
        source_name = doc.metadata.get("source", "Unknown Document")
        act = doc.metadata.get("act", "Unknown Act")
        section = doc.metadata.get("section", "Unknown Section")

        if act != "Unknown Act" and section != "Unknown Section":
            label = f"{source_name} (Extracted: {act}, {section})"
        else:
            label = source_name

        sources.append(label)

    sources = list(set(sources))

    # Conversational chain
    chain = create_conversational_chain()

    conversational_chain = RunnableWithMessageHistory(
        chain,
        get_session_history_func,
        input_messages_key="question",
        history_messages_key="chat_history",
    )

    # Stream response
    stream = conversational_chain.stream(
        {"question": query, "context": context},
        config={"configurable": {"session_id": session_id}}
    )

    return stream, sources