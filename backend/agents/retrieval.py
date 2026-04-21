"""
Retrieval Agent
Performs hybrid vector + keyword search against Azure AI Search.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def retrieve_sop_chunks(
    client, query: str, top_k: int = 5
) -> list[dict]:
    """
    Retrieve relevant SOP document chunks using hybrid search.

    Args:
        client: AIProjectClient instance
        query: Search query
        top_k: Number of results

    Returns:
        List of chunk dicts with content, source, score, metadata
    """
    try:
        from azure.search.documents import SearchClient
        from azure.identity import DefaultAzureCredential

        search_endpoint = os.environ["AI_SEARCH_ENDPOINT"]
        index_name = os.environ.get("AI_SEARCH_INDEX", "sop-index")

        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=DefaultAzureCredential(),
        )

        results = search_client.search(
            search_text=query,
            query_type="semantic",
            semantic_configuration_name="sop-semantic-config",
            top=top_k,
            select=["content", "title", "source_id", "page", "url", "chunk_id"],
        )

        chunks = []
        for r in results:
            chunks.append(
                {
                    "content": r["content"],
                    "source": r["source_id"],
                    "title": r["title"],
                    "page": r.get("page"),
                    "url": r.get("url", ""),
                    "chunk_id": r.get("chunk_id", ""),
                    "score": r["@search.score"],
                }
            )

        logger.info(f"[Retrieval] Found {len(chunks)} chunks for query: {query[:50]}...")
        return chunks

    except Exception as e:
        logger.error(f"[Retrieval] Search failed: {e}")
        return []
