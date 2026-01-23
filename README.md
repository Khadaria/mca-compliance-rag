# Corporate Compliance RAG Assistant (India)

This project implements a **Retrieval-Augmented Generation (RAG)** system focused on **Indian corporate compliance**, specifically the **Companies Act, 2013** and the **Limited Liability Partnership (LLP) Act, 2008**.

The system assists in answering compliance-related queries by retrieving relevant statutory provisions, forms, and filing requirements from a curated document corpus and generating grounded, context-aware responses using a language model.

---

## Problem Statement

Indian corporate compliance involves navigating extensive legal texts, frequent amendments, and strict filing timelines. Professionals and students often need quick, accurate answers to questions such as:
- Applicable forms for a specific compliance event
- Due dates and penalties
- Relevant sections of the Companies Act or LLP Act


---

## Solution Overview

This project uses a **RAG architecture** to:
1. Embed statutory documents into a vector database
2. Retrieve the most relevant legal context for a user query
3. Generate responses strictly grounded in the retrieved content

This approach helps **reduce hallucinations** and improves reliability in the legal domain.

---

## Key Features

- Query-based retrieval from Companies Act and LLP Act documents
- Context-aware and explainable responses
- Metadata-based filtering (Act, Section, Form, Due Date)
- Modular and extensible RAG pipeline

---

## Tech Stack

- **Language:** Python  
- **LLM:** Open-source LLM (Mistral / LLaMA)  
- **Embeddings:** Sentence Transformers  
- **Vector Database:** ChromaDB  
- **RAG Framework:** LangChain  
- **Frontend:** Streamlit  

---

## Data Sources

- Companies Act, 2013 (selected sections)
- LLP Act, 2008
- Statutory forms and compliance rules
- Official circulars and amendments (where applicable)

All data used is publicly available.

---

## System Architecture

User Query  
→ Embedding  
→ Vector Database Retrieval  
→ Context Injection  
→ LLM Response Generation

---

## Intended Use

- Academic project on RAG and vector databases
- Educational assistance for corporate law concepts
- Demonstration of legal-domain AI applications

 *This tool is for educational purposes only and does not constitute legal advice.*

---

##  Future Enhancements

- Annual compliance calendar generation
- Document upload and analysis
- Citation highlighting

---

##  Author

**Vishesh Khadaria**  
**Dhruv Chaturvedi**
