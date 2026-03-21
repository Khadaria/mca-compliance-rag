import re
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document

def is_hindi_heavy(text: str, threshold: float = 0.1) -> bool:
    """Returns True if the proportion of Devanagari characters exceeds the threshold."""
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
        if not is_hindi_heavy(doc.page_content):
            filtered_docs.append(doc)
        else:
            hindi_pages_dropped += 1
            
    print(f"Loaded {len(filtered_docs)} pages. Dropped {hindi_pages_dropped} pages due to Hindi text > 10%.")
    return filtered_docs
