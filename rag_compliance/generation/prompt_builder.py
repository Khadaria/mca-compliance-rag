"""
Prompt Builder for MCA Compliance RAG system.

Constructs strictly grounded prompts for LLM generation:
- System prompt enforces legal grounding constraints
- Context injection from retrieved chunks
- Structured output schema (answer, statutory_basis, forms, penalty, notes)
"""

import logging
from typing import Any

logger = logging.getLogger("rag_compliance.generation.prompt_builder")

# ── System Prompt — Legal Grounding Constraints ───────────────────────
SYSTEM_PROMPT = """You are a compliance-grade AI assistant specializing in Indian corporate law.

YOUR CONSTRAINTS — FOLLOW STRICTLY:

1. ANSWER ONLY from the provided CONTEXT. Do NOT use any external knowledge.
2. CITE specific section numbers, rule numbers, or form names from the context.
3. DO NOT speculate, assume, or fabricate any statutory provisions.
4. DO NOT provide general legal advice beyond what is explicitly stated in the context.
5. If the context does not contain enough information to answer the question, respond with EXACTLY:
   "I could not find an exact statutory provision for this in the retrieved documents."

YOUR OUTPUT FORMAT — Return a valid JSON object with these exact keys:
{
  "answer": "Your grounded answer based on the context",
  "statutory_basis": ["Section X of Act Y", "Rule Z of Rules"],
  "forms_involved": ["Form Name"],
  "penalty": "Penalty details if mentioned in context, otherwise null",
  "notes": "Any relevant additional notes from the context, otherwise null"
}

IMPORTANT:
- Every claim must be traceable to the provided context.
- Do not add information not present in the context.
- If a field is not applicable, set it to null or an empty list.
- Return ONLY the JSON object, no additional text.
"""


class PromptBuilder:
    """Builds grounded prompts from retrieved context for LLM generation.

    Combines the system prompt (legal constraints), retrieved document
    chunks (with source citations), and the user query into a structured
    prompt suitable for any LLM.
    """

    def __init__(self) -> None:
        logger.info("PromptBuilder initialized")

    def build(self, query: str, context: dict[str, Any]) -> dict[str, str]:
        """Build a complete prompt from query and retrieved context.

        Args:
            query: The user's compliance question.
            context: Dict from Retriever.retrieve_with_context() containing
                     'contexts' (list of {text, source, score}) and 'sources'.

        Returns:
            Dict with 'system' and 'user' prompt strings.
        """
        contexts = context.get("contexts", [])

        if not contexts:
            logger.warning("No context provided — LLM will return fallback")

        # Build context block
        context_block = self._format_context(contexts)

        user_prompt = f"""CONTEXT (Retrieved statutory provisions):
{context_block}

QUESTION: {query}

Provide your answer as a JSON object following the output format specified in your instructions.
Remember: Answer ONLY from the context above. Cite specific sections and forms."""

        logger.info(
            "Prompt built: %d context chunks, query='%s...'",
            len(contexts),
            query[:60],
        )

        return {
            "system": SYSTEM_PROMPT,
            "user": user_prompt,
        }

    @staticmethod
    def _format_context(contexts: list[dict[str, Any]]) -> str:
        """Format retrieved contexts into a numbered block for the prompt.

        Args:
            contexts: List of context dicts with 'text', 'source', 'score'.

        Returns:
            Formatted string with numbered, sourced context passages.
        """
        if not contexts:
            return "[No relevant documents were retrieved for this query.]"

        formatted_parts = []
        for idx, ctx in enumerate(contexts, 1):
            source = ctx.get("source", "Unknown source")
            text = ctx.get("text", "").strip()
            score = ctx.get("score", 0.0)

            formatted_parts.append(
                f"--- Document {idx} (Source: {source}, Relevance: {score:.2f}) ---\n"
                f"{text}\n"
            )

        return "\n".join(formatted_parts)
