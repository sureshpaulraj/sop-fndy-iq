"""
Citation Formatter Agent
Formats responses with inline citation references and source metadata.
"""

import logging
import re

logger = logging.getLogger(__name__)


async def format_citations(response: str, chunks: list[dict]) -> dict:
    """
    Add inline citation references to the response and build citation metadata.

    For each source chunk used, inserts [N] references in the response text
    and builds a citations array with source details.

    Args:
        response: Raw response text from the grounding validator
        chunks: Source chunks used to generate the response

    Returns:
        dict with 'response' (annotated text) and 'citations' (metadata list)
    """
    # Build unique sources list (deduplicate by source ID)
    seen_sources = {}
    citations = []

    for chunk in chunks:
        source_id = chunk.get("source", "unknown")
        if source_id not in seen_sources:
            idx = len(citations) + 1
            seen_sources[source_id] = idx
            citations.append(
                {
                    "index": idx,
                    "source": source_id,
                    "title": chunk.get("title", source_id),
                    "page": chunk.get("page"),
                    "url": chunk.get("url", ""),
                }
            )

    # Add citation references to the response if not already present
    formatted_response = response
    if not re.search(r"\[\d+\]", response):
        # No inline citations yet — append source references
        source_refs = "\n\n**Sources:**\n"
        for c in citations:
            page_info = f" (p.{c['page']})" if c.get("page") else ""
            source_refs += f"- [{c['index']}] {c['title']}{page_info}\n"
        formatted_response = response + source_refs

    logger.info(f"[Citation] Formatted response with {len(citations)} citations")

    return {
        "response": formatted_response,
        "citations": citations,
    }
