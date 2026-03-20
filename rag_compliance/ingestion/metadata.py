import json
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from rag_compliance.config import LLM_MODEL
from rag_compliance.generation.prompts import METADATA_EXTRACTION_PROMPT

def extract_metadata_for_chunk(text: str, chain) -> dict:
    try:
        # Limit text content to speed up inference and avoid context overflow
        response = chain.invoke({"text": text[:800]})
        content = response.content
        data = json.loads(content)
        return data
    except Exception as e:
        return {"act": "Unknown", "section": "Unknown", "topic": "Unknown"}

def enrich_chunks_with_metadata(chunks: list) -> list:
    print("Initializing LLM for metadata extraction...")
    llm = ChatOllama(model=LLM_MODEL, temperature=0, format="json")
    prompt = PromptTemplate.from_template(METADATA_EXTRACTION_PROMPT)
    chain = prompt | llm

    print(f"Extracting metadata for {len(chunks)} chunks...")
    for i, chunk in enumerate(chunks):
        if i % 50 == 0:
            print(f"Processed {i}/{len(chunks)} chunks...")
        metadata = extract_metadata_for_chunk(chunk.page_content, chain)
        
        # Merge JSON metadata into the chunk's built-in metadata
        if isinstance(metadata, dict):
            for key, val in metadata.items():
                chunk.metadata[key] = str(val)
                
    print("Metadata extraction completed.")
    return chunks
