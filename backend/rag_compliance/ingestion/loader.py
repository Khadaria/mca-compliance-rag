import re
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document


def clean_text(text: str) -> str:
    """
    Clean PDF noise while preserving line breaks -- legal_parser's heading/
    sub-section regexes anchor on "start of line" (a real \\n), so collapsing
    all whitespace (including newlines) into single spaces, as this used to
    do, silently destroyed every structural anchor before parsing ever ran.
    That was also why the old chunker's "\\nSection "/"\\nRule " separators
    never fired -- there were no newlines left for them to match either.
    """
    text = re.sub(r'[ \t]+', ' ', text)           # collapse horizontal whitespace only
    text = re.sub(r'\n[ \t]*\n+', '\n', text)     # collapse blank/whitespace-only lines
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)  # trim spaces around remaining newlines
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


def load_and_filter_documents(data_path: str) -> dict[str, list[Document]]:
    """Load all PDFs and return their filtered pages grouped by source
    filename (order preserved), so callers can process one document's pages
    at a time (sections/rules span pages, so per-document reassembly needs
    this grouping)."""
    print(f"Loading documents from {data_path}...")

    loader = PyPDFDirectoryLoader(data_path)
    raw_docs = loader.load()

    grouped: dict[str, list[Document]] = {}
    hindi_pages_dropped = 0

    for doc in raw_docs:
        cleaned_text = clean_text(doc.page_content)

        if not is_hindi_heavy(cleaned_text) and len(cleaned_text) > 200:
            doc.page_content = cleaned_text
            source = doc.metadata.get("source", "Unknown Source")
            grouped.setdefault(source, []).append(doc)
        else:
            hindi_pages_dropped += 1

    total_pages = sum(len(pages) for pages in grouped.values())
    print(f"Loaded {total_pages} cleaned pages across {len(grouped)} files.")
    print(f"Dropped {hindi_pages_dropped} pages (Hindi/noise).")

    return grouped