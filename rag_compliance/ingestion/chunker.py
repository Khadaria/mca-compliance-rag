from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=[
            "\nSection ", "\nRule ", "\nChapter ",
            "\n\n", "\n", ". ", " "
        ],
        length_function=len,
        is_separator_regex=False,
    )

def split_documents(documents: list[Document]) -> list[Document]:
    print("Splitting documents into chunks...")
    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")
    return chunks
