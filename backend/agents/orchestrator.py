"""
SOP Orchestrator Agent
Routes user queries through the Retrieval → Grounding → Citation agent chain.
Tracks activity steps for the thought-process UI.
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


def _generate_follow_ups(query: str, response: str) -> list[str]:
    """Generate contextual follow-up prompt suggestions."""
    q = query.lower()
    if any(w in q for w in ["spill", "cleanup", "hazard"]):
        return [
            "What PPE do I need for hazardous spills?",
            "Where are the spill kit locations?",
            "How do I fill out the EHS Incident Report?",
        ]
    elif any(w in q for w in ["forklift", "lift", "truck"]):
        return [
            "What are the forklift speed limits?",
            "How do I report a forklift deficiency?",
            "When is forklift recertification required?",
        ]
    elif any(w in q for w in ["receiv", "inventory", "shipment"]):
        return [
            "How do I handle receiving discrepancies?",
            "What is the FIFO labeling procedure?",
            "How do I log goods in the WMS?",
        ]
    elif any(w in q for w in ["emergency", "evacuat", "fire"]):
        return [
            "Where are the muster points?",
            "What is the headcount procedure?",
            "How do I use the emergency notification system?",
        ]
    elif any(w in q for w in ["safety", "ppe", "protect"]):
        return [
            "What PPE is required in the dock area?",
            "How do I report a near-miss?",
            "What are the housekeeping standards?",
        ]
    return [
        "What are the warehouse safety rules?",
        "How do I handle a spill emergency?",
        "Show me the forklift inspection checklist",
    ]


async def run_sop_orchestrator(
    client, query: str, conversation_id: Optional[str] = None
) -> dict:
    """
    Execute the SOP RAG agent chain:
    1. Retrieval Agent — hybrid search against AI Search
    2. Grounding Validator — check response against source chunks
    3. Citation Formatter — add source references

    Tracks wall-clock timing and activity steps for the thought-process UI.

    Args:
        client: AIProjectClient instance
        query: User's natural language question
        conversation_id: Optional conversation ID for context

    Returns:
        dict with response, citations, grounding status, activity, follow_up_prompts
    """
    from .retrieval import retrieve_sop_chunks
    from .grounding import validate_grounding
    from .citation import format_citations

    activity: list[dict] = []

    # --- Step 1: Query Planning ---
    t0 = time.perf_counter()
    logger.info(f"[Orchestrator] Processing query: {query[:100]}...")
    activity.append({
        "step": "Query Planning",
        "description": f'Analyzing query: "{query}"',
        "duration_ms": int((time.perf_counter() - t0) * 1000),
    })

    # --- Step 2: Document Search ---
    t1 = time.perf_counter()
    chunks = await retrieve_sop_chunks(client, query)
    search_duration = int((time.perf_counter() - t1) * 1000)

    if not chunks:
        activity.append({
            "step": "Document Search",
            "description": "No relevant SOP documents found",
            "duration_ms": search_duration,
        })
        return {
            "response": "I couldn't find relevant SOP documents for your question. Please try rephrasing or contact your supervisor.",
            "citations": [],
            "conversation_id": conversation_id or "",
            "grounded": False,
            "confidence": 0.0,
            "activity": activity,
            "follow_up_prompts": _generate_follow_ups(query, ""),
        }

    source_names = ", ".join(c.get("source", "unknown") for c in chunks[:5])
    activity.append({
        "step": "Document Search",
        "description": f"Found {len(chunks)} relevant chunks from: {source_names}",
        "duration_ms": search_duration,
    })

    # --- Step 3: AI Reasoning (Grounding) ---
    t2 = time.perf_counter()
    logger.info(f"[Orchestrator] Retrieved {len(chunks)} chunks, validating grounding...")
    grounding_result = await validate_grounding(client, query, chunks)
    grounding_duration = int((time.perf_counter() - t2) * 1000)

    reasoning_tree = [
        {
            "label": "Extract relevant sections from matched SOPs",
            "children": [
                {"label": f"Reviewing {c.get('source', 'doc')}: {c.get('title', '')}"} for c in chunks[:5]
            ],
        },
        {"label": "Cross-reference procedures for consistency"},
        {"label": f"Grounding confidence: {grounding_result.get('confidence', 0):.0%}"},
    ]

    if grounding_result.get("reasoning"):
        reasoning_tree.append({"label": grounding_result["reasoning"]})

    activity.append({
        "step": "AI Reasoning",
        "description": f"Grounding validation — confidence: {grounding_result.get('confidence', 0):.0%}",
        "duration_ms": grounding_duration,
        "reasoning_tree": reasoning_tree,
    })

    if not grounding_result["grounded"]:
        return {
            "response": "I found some related documents but couldn't generate a well-grounded answer. Please try being more specific.",
            "citations": [],
            "conversation_id": conversation_id or "",
            "grounded": False,
            "confidence": grounding_result["confidence"],
            "activity": activity,
            "follow_up_prompts": _generate_follow_ups(query, ""),
        }

    # --- Step 4: Citation Formatting ---
    t3 = time.perf_counter()
    logger.info("[Orchestrator] Grounding validated, formatting citations...")
    formatted = await format_citations(grounding_result["response"], chunks)
    citation_duration = int((time.perf_counter() - t3) * 1000)

    activity.append({
        "step": "Answer Synthesis",
        "description": f"Composed response with {len(formatted['citations'])} inline citations",
        "duration_ms": citation_duration,
    })

    response_text = formatted["response"]
    return {
        "response": response_text,
        "citations": formatted["citations"],
        "conversation_id": conversation_id or "",
        "grounded": True,
        "confidence": grounding_result["confidence"],
        "activity": activity,
        "follow_up_prompts": _generate_follow_ups(query, response_text),
    }
