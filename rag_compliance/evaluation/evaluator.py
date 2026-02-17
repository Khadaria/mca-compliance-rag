"""
Evaluation module for MCA Compliance RAG system.

Provides basic evaluation utilities for measuring retrieval quality
and generation accuracy. Phase 1 scaffold — to be expanded with
comprehensive metrics in Phase 2.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("rag_compliance.evaluation.evaluator")


@dataclass
class EvaluationResult:
    """Result of evaluating a single query-response pair."""

    query: str
    has_answer: bool
    num_sources: int
    avg_retrieval_score: float
    has_statutory_basis: bool
    has_forms: bool
    has_penalty: bool
    response_length: int


class Evaluator:
    """Evaluates RAG pipeline output for quality and compliance.

    Phase 1 metrics:
    - Retrieval coverage (did we find relevant documents?)
    - Response completeness (are all structured fields populated?)
    - Grounding check (does the response cite statutory provisions?)

    Phase 2 will add:
    - Ground truth comparison
    - Hallucination detection
    - Citation accuracy verification
    """

    def __init__(self) -> None:
        logger.info("Evaluator initialized")

    def evaluate(
        self,
        query: str,
        response: dict[str, Any],
        retrieval_context: dict[str, Any],
    ) -> EvaluationResult:
        """Evaluate a single query-response pair.

        Args:
            query: The original query.
            response: Structured response from the generator.
            retrieval_context: Context dict from the retriever.

        Returns:
            EvaluationResult with quality metrics.
        """
        contexts = retrieval_context.get("contexts", [])
        scores = [c.get("score", 0.0) for c in contexts]

        has_answer = (
            response.get("answer", "")
            != "I could not find an exact statutory provision for this in the retrieved documents."
            and bool(response.get("answer"))
        )

        result = EvaluationResult(
            query=query,
            has_answer=has_answer,
            num_sources=len(contexts),
            avg_retrieval_score=sum(scores) / len(scores) if scores else 0.0,
            has_statutory_basis=bool(response.get("statutory_basis")),
            has_forms=bool(response.get("forms_involved")),
            has_penalty=response.get("penalty") is not None,
            response_length=len(response.get("answer", "")),
        )

        logger.info(
            "Evaluation for '%s...': answer=%s, sources=%d, avg_score=%.3f",
            query[:50],
            result.has_answer,
            result.num_sources,
            result.avg_retrieval_score,
        )

        return result

    def evaluate_batch(
        self,
        queries: list[str],
        responses: list[dict[str, Any]],
        contexts: list[dict[str, Any]],
    ) -> list[EvaluationResult]:
        """Evaluate a batch of query-response pairs.

        Args:
            queries: List of queries.
            responses: List of structured responses.
            contexts: List of retrieval context dicts.

        Returns:
            List of EvaluationResult instances.
        """
        results = []
        for q, r, c in zip(queries, responses, contexts):
            results.append(self.evaluate(q, r, c))

        # Summary statistics
        answered = sum(1 for r in results if r.has_answer)
        avg_score = (
            sum(r.avg_retrieval_score for r in results) / len(results)
            if results
            else 0.0
        )

        logger.info(
            "Batch evaluation: %d/%d answered, avg_retrieval_score=%.3f",
            answered,
            len(results),
            avg_score,
        )

        return results
