"""Tests for FastMCP server tools (mock mode)."""

import pytest
import asyncio


# Import the server tools
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestSearchSops:
    """Tests for the search_sops MCP tool."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        from server import search_sops

        result = await search_sops("forklift safety")
        assert "results" in result
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_result_has_required_fields(self):
        from server import search_sops

        result = await search_sops("warehouse procedure")
        for r in result["results"]:
            assert "content" in r
            assert "score" in r
            assert "source" in r
            assert "title" in r

    @pytest.mark.asyncio
    async def test_search_with_custom_top_k(self):
        from server import search_sops

        result = await search_sops("safety", top_k=3)
        assert "results" in result


class TestGetDocument:
    """Tests for the get_document MCP tool."""

    @pytest.mark.asyncio
    async def test_get_document_returns_content(self):
        from server import get_document

        result = await get_document("SOP-WH-042")
        assert "title" in result
        assert "content" in result
        assert "url" in result
        assert "last_modified" in result


class TestSubmitFeedback:
    """Tests for the submit_feedback MCP tool."""

    @pytest.mark.asyncio
    async def test_submit_feedback_up(self):
        from server import submit_feedback

        result = await submit_feedback("msg-123", "up", "Great answer!")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_submit_feedback_down(self):
        from server import submit_feedback

        result = await submit_feedback("msg-456", "down")
        assert result["success"] is True


class TestGetHistory:
    """Tests for the get_history MCP tool."""

    @pytest.mark.asyncio
    async def test_get_history_returns_messages(self):
        from server import get_history

        result = await get_history("conv-001")
        assert "conversation_id" in result
        assert "messages" in result
        assert len(result["messages"]) > 0

    @pytest.mark.asyncio
    async def test_history_messages_have_roles(self):
        from server import get_history

        result = await get_history("conv-001")
        for msg in result["messages"]:
            assert msg["role"] in ("user", "assistant")
            assert "content" in msg
            assert "timestamp" in msg


class TestChat:
    """Tests for the chat MCP tool (mock mode)."""

    @pytest.mark.asyncio
    async def test_chat_returns_response(self):
        from server import chat

        result = await chat("What is the forklift safety procedure?")
        assert "response" in result
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_chat_includes_citations(self):
        from server import chat

        result = await chat("warehouse receiving process")
        assert "citations" in result
        assert len(result["citations"]) > 0

    @pytest.mark.asyncio
    async def test_chat_citations_have_required_fields(self):
        from server import chat

        result = await chat("safety rules")
        for c in result["citations"]:
            assert "index" in c
            assert "source" in c
            assert "title" in c

    @pytest.mark.asyncio
    async def test_chat_returns_grounding_info(self):
        from server import chat

        result = await chat("compliance check")
        assert "grounded" in result
        assert "confidence" in result
