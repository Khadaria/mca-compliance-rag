import re
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document


def clean_text(text: str) -> str:
    """
    Clean PDF noise
    """
    text = re.sub(r'\s+', ' ', text)              # remove extra whitespace
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()
    return text


def is_hindi_heavy(text: str, threshold: float = 0.1) -> bool:
    if not text.strip():
        return False

    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    total_chars = len(text)

    if total_chars == 0:
        return False

    return (devanagari_chars / total_chars) > threshold


def load_and_filter_documents(data_path: str) -> list[Document]:
    print(f"Loading documents from {data_path}...")

    loader = PyPDFDirectoryLoader(data_path)
    raw_docs = loader.load()

    filtered_docs = []
    hindi_pages_dropped = 0

    for doc in raw_docs:
        cleaned_text = clean_text(doc.page_content)

        if not is_hindi_heavy(cleaned_text) and len(cleaned_text) > 200:
            doc.page_content = cleaned_text
            filtered_docs.append(doc)
        else:
            hindi_pages_dropped += 1

    print(f"Loaded {len(filtered_docs)} cleaned pages.")
    print(f"Dropped {hindi_pages_dropped} pages (Hindi/noise).")

    return filtered_docs