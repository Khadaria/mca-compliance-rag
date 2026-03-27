from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=600,              # ✅ Reduced (better precision)
        chunk_overlap=120,           # ✅ Maintain context
        separators=[
            "\nSection ",            # 🔥 Most important for legal docs
            "\nRule ",
            "\nCHAPTER ",
            "\nChapter ",
            "\n\n",
            "\n",
            ". ",
            " "
        ],
        length_function=len,
        is_separator_regex=False,
    )


def split_documents(documents: list[Document]) -> list[Document]:
    print("Splitting documents into chunks...")

    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)

    # ✅ Remove very small noisy chunks
    filtered_chunks = [
        chunk for chunk in chunks if len(chunk.page_content.strip()) > 100
    ]

    print(f"Created {len(filtered_chunks)} clean chunks (from {len(chunks)} raw).")
    return filtered_chunks