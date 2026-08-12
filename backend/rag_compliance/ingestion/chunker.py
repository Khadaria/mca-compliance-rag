from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Fallback splitter only. Used for the 6 form PDFs (DIR-3 KYC, INC-20A,
# INC-22, MGT-7, Form 8/11 LLP) which have no Section/Rule numbering, and as
# a safety-net catch-all when legal_parser.parse_legal_pdf finds zero
# structural matches in a nominal Act/Rule PDF. Do NOT reintroduce this for
# Act/Rule PDFs -- the "\nSection "/"\nRule " separators used to live here
# but never actually matched real extracted text (headings are bare
# "160. Title.--", no literal "Section"/"Rule" prefix), which is what
# produced the mid-sentence/TOC-page chunk quality problems this rewrite
# fixes. Structured legal text should go through legal_parser instead.


def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " "],
        length_function=len,
        is_separator_regex=False,
    )


def split_documents(documents: list[Document]) -> list[Document]:
    print("Splitting documents into chunks (fallback splitter)...")

    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)

    # ✅ Remove very small noisy chunks
    filtered_chunks = [
        chunk for chunk in chunks if len(chunk.page_content.strip()) > 100
    ]

    print(f"Created {len(filtered_chunks)} clean chunks (from {len(chunks)} raw).")
    return filtered_chunks