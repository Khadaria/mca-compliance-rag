import json
from langchain_core.prompts import PromptTemplate
from rag_compliance.config import GROQ_API_KEY, GROQ_MODEL
from rag_compliance.generation.prompts import METADATA_EXTRACTION_PROMPT


def get_metadata_llm():
    """Return a zero-temperature Groq model for structured metadata extraction."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set.")

    from langchain_groq import ChatGroq

    return ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, temperature=0)


def extract_metadata_for_chunk(text: str, chain) -> dict:
    try:
        response = chain.invoke({"text": text[:500]})
        content = response.content.strip()

        # Strip markdown code fences if present (Groq/Gemini may add them)
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        try:
            data = json.loads(content)
        except Exception:
            return {"act": "Unknown", "section": "Unknown", "topic": "Unknown"}

        return data

    except Exception:
        return {"act": "Unknown", "section": "Unknown", "topic": "Unknown"}


def enrich_chunks_with_metadata(chunks: list) -> list:
    print("Initializing LLM for metadata extraction...")
    llm = get_metadata_llm()
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

        if "source" not in chunk.metadata:
            chunk.metadata["source"] = "Unknown Source"

    print("Metadata extraction completed.")
    return chunks
