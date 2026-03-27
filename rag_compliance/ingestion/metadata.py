import json
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from rag_compliance.config import LLM_MODEL
from rag_compliance.generation.prompts import METADATA_EXTRACTION_PROMPT


def extract_metadata_for_chunk(text: str, chain) -> dict:
    try:
        response = chain.invoke({"text": text[:500]})  # ✅ smaller input (faster & cleaner)
        content = response.content.strip()

        # Safe JSON parsing
        try:
            data = json.loads(content)
        except:
            return {"act": "Unknown", "section": "Unknown", "topic": "Unknown"}

        return data

    except Exception:
        return {"act": "Unknown", "section": "Unknown", "topic": "Unknown"}


def enrich_chunks_with_metadata(chunks: list) -> list:
    print("Initializing LLM for metadata extraction...")

    llm = ChatOllama(
        model=LLM_MODEL,
        temperature=0,
        format="json"
    )

    prompt = PromptTemplate.from_template(METADATA_EXTRACTION_PROMPT)
    chain = prompt | llm

    print(f"Extracting metadata for {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks):
        if i % 50 == 0:
            print(f"Processed {i}/{len(chunks)} chunks...")

        metadata = extract_metadata_for_chunk(chunk.page_content, chain)

        if isinstance(metadata, dict):
            for key, val in metadata.items():
                chunk.metadata[key] = str(val)

        # ✅ Always ensure source exists
        if "source" not in chunk.metadata:
            chunk.metadata["source"] = "Unknown Source"

    print("Metadata extraction completed.")
    return chunks