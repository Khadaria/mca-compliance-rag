"""
LLM Generator for MCA Compliance RAG system.

Supports two free LLM backends:
1. Google Gemini (free tier via Google AI Studio — recommended)
2. Ollama (fully local, no API key needed)

Generates structured compliance answers from grounded prompts.
"""

import json
import logging
from typing import Any, Optional

import httpx

from rag_compliance.config import get_settings
from rag_compliance.generation.prompt_builder import PromptBuilder

logger = logging.getLogger("rag_compliance.generation.generator")

# ── Default fallback response ─────────────────────────────────────────
FALLBACK_RESPONSE = {
    "answer": "I could not find an exact statutory provision for this in the retrieved documents.",
    "statutory_basis": [],
    "forms_involved": [],
    "penalty": None,
    "notes": "The retrieved documents did not contain sufficient information to answer this query. Please try rephrasing or narrowing your question.",
}


class Generator:
    """Generates structured compliance answers using a free LLM backend.

    Supports:
    - Google Gemini free tier (via google-genai SDK)
    - Ollama local inference (via HTTP API)

    The provider is selected via the LLM_PROVIDER config setting.

    Args:
        prompt_builder: PromptBuilder instance for constructing prompts.
    """

    def __init__(self, prompt_builder: Optional[PromptBuilder] = None) -> None:
        self.settings = get_settings()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.provider = self.settings.llm_provider

        logger.info("Generator initialized (provider=%s)", self.provider)

    def generate(
        self,
        query: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a structured compliance answer.

        Args:
            query: The user's compliance question.
            context: Retrieved context dict from Retriever.retrieve_with_context().

        Returns:
            Structured dict with answer, statutory_basis, forms_involved,
            penalty, and notes.
        """
        # Check if we have any context
        if not context.get("contexts"):
            logger.warning("No context available — returning fallback")
            return FALLBACK_RESPONSE.copy()

        # Build the prompt
        prompt = self.prompt_builder.build(query, context)

        # Generate response based on provider
        try:
            if self.provider == "gemini":
                raw_response = self._generate_gemini(prompt)
            elif self.provider == "ollama":
                raw_response = self._generate_ollama(prompt)
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")

            # Parse the structured response
            result = self._parse_response(raw_response)

            logger.info("Generated response for query: '%s...'", query[:60])
            return result

        except Exception as e:
            logger.error("Generation failed: %s", e, exc_info=True)
            fallback = FALLBACK_RESPONSE.copy()
            fallback["notes"] = f"Generation error: {str(e)}"
            return fallback

    def _generate_gemini(self, prompt: dict[str, str]) -> str:
        """Generate response using Google Gemini free tier.

        Args:
            prompt: Dict with 'system' and 'user' keys.

        Returns:
            Raw text response from Gemini.
        """
        from google import genai

        api_key = self.settings.gemini_api_key
        if not api_key or api_key == "your-gemini-api-key-here":
            raise ValueError(
                "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com"
            )

        client = genai.Client(api_key=api_key)

        # Combine system + user into a single prompt for Gemini
        combined_prompt = f"{prompt['system']}\n\n{prompt['user']}"

        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=combined_prompt,
        )

        result = response.text
        logger.debug("Gemini response length: %d chars", len(result))
        return result

    def _generate_ollama(self, prompt: dict[str, str]) -> str:
        """Generate response using Ollama local inference.

        Args:
            prompt: Dict with 'system' and 'user' keys.

        Returns:
            Raw text response from Ollama.
        """
        url = f"{self.settings.ollama_base_url}/api/generate"

        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt["user"],
            "system": prompt["system"],
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for factual accuracy
                "num_predict": 2048,
            },
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                result = data.get("response", "")
                logger.debug("Ollama response length: %d chars", len(result))
                return result
        except httpx.ConnectError:
            raise ConnectionError(
                "Cannot connect to Ollama. Is it running? Start with: ollama serve"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama error: {e.response.status_code} — {e.response.text}")

    def _parse_response(self, raw_response: str) -> dict[str, Any]:
        """Parse the LLM response into a structured dict.

        Attempts to extract JSON from the response. Falls back to wrapping
        the raw text as an answer if JSON parsing fails.

        Args:
            raw_response: Raw text from the LLM.

        Returns:
            Structured dict with answer, statutory_basis, etc.
        """
        # Try to extract JSON from the response
        text = raw_response.strip()

        # Remove markdown code fences if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            parsed = json.loads(text)

            # Validate expected keys
            result = {
                "answer": parsed.get("answer", ""),
                "statutory_basis": parsed.get("statutory_basis", []),
                "forms_involved": parsed.get("forms_involved", []),
                "penalty": parsed.get("penalty"),
                "notes": parsed.get("notes"),
            }

            # Guard against empty answer
            if not result["answer"]:
                return FALLBACK_RESPONSE.copy()

            return result

        except json.JSONDecodeError:
            logger.warning(
                "Could not parse JSON from LLM response, wrapping as raw answer"
            )

            # Attempt to find JSON within the text
            json_start = text.find("{")
            json_end = text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                try:
                    embedded_json = json.loads(text[json_start:json_end])
                    return {
                        "answer": embedded_json.get("answer", text),
                        "statutory_basis": embedded_json.get("statutory_basis", []),
                        "forms_involved": embedded_json.get("forms_involved", []),
                        "penalty": embedded_json.get("penalty"),
                        "notes": embedded_json.get("notes"),
                    }
                except json.JSONDecodeError:
                    pass

            # Final fallback: wrap raw text as answer
            return {
                "answer": text,
                "statutory_basis": [],
                "forms_involved": [],
                "penalty": None,
                "notes": "Response was not returned in structured format.",
            }
