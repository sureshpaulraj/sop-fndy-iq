"""Tests for Citation Formatter Agent."""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_format_citations_adds_sources():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from agents.citation import format_citations

    chunks = [
        {"source": "SOP-WH-042", "title": "Warehouse Safety", "page": 3, "url": "https://sp.com/1"},
        {"source": "SOP-WH-015", "title": "Forklift Ops", "page": 7, "url": "https://sp.com/2"},
    ]
    result = await format_citations("Here is the answer about safety.", chunks)

    assert "response" in result
    assert "citations" in result
    assert len(result["citations"]) == 2
    assert result["citations"][0]["index"] == 1
    assert result["citations"][1]["index"] == 2


@pytest.mark.asyncio
async def test_format_citations_deduplicates():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from agents.citation import format_citations

    chunks = [
        {"source": "SOP-WH-042", "title": "Safety", "page": 3, "url": ""},
        {"source": "SOP-WH-042", "title": "Safety", "page": 5, "url": ""},
    ]
    result = await format_citations("Answer here.", chunks)
    # Same source ID → deduplicated to 1 citation
    assert len(result["citations"]) == 1


@pytest.mark.asyncio
async def test_format_preserves_existing_citations():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from agents.citation import format_citations

    chunks = [{"source": "SOP-1", "title": "Doc", "url": ""}]
    # Response already has inline citations
    result = await format_citations("Answer [1] here.", chunks)
    # Should not double-add
    assert result["response"].count("Sources:") == 0
