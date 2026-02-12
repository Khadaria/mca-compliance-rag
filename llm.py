from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama

from prompts import PROMPT_TEMPLATE
from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

def generate_answer(query_text: str):
    # -------------------------------
    # Load vector database
    # -------------------------------
    embedding_function = get_embedding_function()
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_function
    )

    # -------------------------------
    # Retrieve relevant chunks
    # -------------------------------
    results = db.similarity_search_with_score(query_text, k=5)

    context_text = "\n\n---\n\n".join(
        [doc.page_content for doc, _score in results]
    )

    # -------------------------------
    # Format prompt
    # -------------------------------
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(
        context=context_text,
        question=query_text
    )

    # -------------------------------
    # Call LLM
    # -------------------------------
    model = Ollama(model="mistral")
    response_text = model.invoke(prompt).strip()

    # -------------------------------
    # Prepare readable sources
    # -------------------------------
    sources = []
    for doc, _score in results:
        source = doc.metadata.get("source", "Unknown document")
        page = doc.metadata.get("page", "Unknown page")
        sources.append(f"{source} (Page {page})")

    return response_text, list(set(sources))
