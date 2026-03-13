from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
import re

from get_embedding_function import get_embedding_function
from prompts import PROMPT_TEMPLATE

CHROMA_PATH = "chroma"

# Load LLM
model = ChatOllama(model="mistral")


def expand_section_query(query_text: str):
    """
    Expand section-based queries to improve semantic retrieval.
    Embeddings struggle with numbers like 'Section 164', so we add
    additional legal hints.
    """

    match = re.search(r"section\s*(\d+)", query_text.lower())

    if match:
        section_number = match.group(1)

        expanded_query = f"""
        Section {section_number} Companies Act legal provision
        Section {section_number} corporate law
        Disqualification for appointment of director Section {section_number}
        {query_text}
        """

        return expanded_query

    return query_text


def generate_answer(query_text: str):

    # Expand section queries
    query_text = expand_section_query(query_text)

    # Load vector database
    embedding_function = get_embedding_function()

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_function
    )

    # Retriever
    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,
            "fetch_k": 30
        }
    )

    # Retrieve documents
    docs = retriever.invoke(query_text)

    # DEBUG: print retrieved chunks
    for doc in docs:
        print("\n--- Retrieved Chunk ---")
        print(doc.page_content[:500])

    # Combine context
    context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])

    # Build prompt
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    prompt = prompt_template.format(
        context=context_text,
        question=query_text
    )

    # Streaming generator
    def stream_response():
        for chunk in model.stream(prompt):
            if chunk.content:
                yield chunk.content

    # Collect sources
    sources = []
    for doc in docs:
        source = doc.metadata.get("source", None)
        if source:
            sources.append(source)

    return stream_response(), sources