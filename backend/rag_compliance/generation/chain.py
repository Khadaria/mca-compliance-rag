from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from rag_compliance.config import GROQ_API_KEY, GROQ_MODEL
from rag_compliance.generation.prompts import PROMPT_TEMPLATE
from rag_compliance.retrieval.hybrid_retriever import get_hybrid_retriever
from rag_compliance.retrieval.reranker import ComponentReranker


def get_llm():
    """Return the Groq chat model used in production."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set.")

    from langchain_groq import ChatGroq

    return ChatGroq(
        model=GROQ_MODEL,
        groq_api_key=GROQ_API_KEY,
        temperature=0.1,
    )


llm = None
hybrid_retriever = None
reranker = None


def get_runtime_components():
    """Initialize heavy RAG components lazily so the web server can bind quickly."""
    global llm, hybrid_retriever, reranker

    if llm is None:
        print("[RAG] Initializing Groq client...")
        llm = get_llm()

    if hybrid_retriever is None:
        print("[RAG] Initializing hybrid retriever...")
        hybrid_retriever = get_hybrid_retriever()

    if reranker is None:
        print("[RAG] Initializing reranker...")
        reranker = ComponentReranker()

    return llm, hybrid_retriever, reranker


def create_conversational_chain(llm_instance):
    prompt = ChatPromptTemplate.from_messages([
        ("system", PROMPT_TEMPLATE),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "Context:\n{context}\n\nQuestion:\n{question}")
    ])
    chain = prompt | llm_instance
    return chain


def process_query_with_rag(query: str, session_id: str, get_session_history_func):
    """
    1. Retrieve documents via hybrid search
    2. Rerank with Flashrank
    3. Generate response with context
    """

    llm_instance, retriever_instance, reranker_instance = get_runtime_components()

    # 1. Retrieve
    if hasattr(retriever_instance, "get_relevant_documents"):
        raw_docs = retriever_instance.get_relevant_documents(query)
    else:
        raw_docs = retriever_instance.invoke(query)

    # 2. Rerank
    reranked_docs = reranker_instance.rerank(query, raw_docs, top_k=5)

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
    chain = create_conversational_chain(llm_instance)

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
