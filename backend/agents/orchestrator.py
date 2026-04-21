"""
SOP Orchestrator Agent
Routes user queries through the Retrieval → Grounding → Citation agent chain.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def run_sop_orchestrator(
    client, query: str, conversation_id: Optional[str] = None
) -> dict:
    """
    Execute the SOP RAG agent chain:
    1. Retrieval Agent — hybrid search against AI Search
    2. Grounding Validator — check response against source chunks
    3. Citation Formatter — add source references

    Args:
        client: AIProjectClient instance
        query: User's natural language question
        conversation_id: Optional conversation ID for context

    Returns:
        dict with response, citations, grounding status
    """
    from .retrieval import retrieve_sop_chunks
    from .grounding import validate_grounding
    from .citation import format_citations

    # Step 1: Retrieve relevant SOP chunks
    logger.info(f"[Orchestrator] Processing query: {query[:100]}...")
    chunks = await retrieve_sop_chunks(client, query)

    if not chunks:
        return {
            "response": "I couldn't find relevant SOP documents for your question. Please try rephrasing or contact your supervisor.",
            "citations": [],
            "conversation_id": conversation_id or "",
            "grounded": False,
            "confidence": 0.0,
        }

    # Step 2: Generate response and validate grounding
    logger.info(f"[Orchestrator] Retrieved {len(chunks)} chunks, validating grounding...")
    grounding_result = await validate_grounding(client, query, chunks)

    if not grounding_result["grounded"]:
        return {
            "response": "I found some related documents but couldn't generate a well-grounded answer. Please try being more specific.",
            "citations": [],
            "conversation_id": conversation_id or "",
            "grounded": False,
            "confidence": grounding_result["confidence"],
        }

    # Step 3: Format citations
    logger.info("[Orchestrator] Grounding validated, formatting citations...")
    formatted = await format_citations(grounding_result["response"], chunks)

    return {
        "response": formatted["response"],
        "citations": formatted["citations"],
        "conversation_id": conversation_id or "",
        "grounded": True,
        "confidence": grounding_result["confidence"],
    }
