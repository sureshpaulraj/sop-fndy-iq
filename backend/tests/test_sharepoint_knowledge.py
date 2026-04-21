"""
Tests for SharePoint Knowledge Source integration.
Tests the knowledge client, token provider, and server integration.
"""

import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock


# --- sharepoint_client tests ---

class TestSharePointKnowledgeClient:
    def test_client_not_available_without_env(self):
        """Client reports unavailable when env vars are missing."""
        with patch.dict(os.environ, {}, clear=True):
            from knowledge.sharepoint_client import SharePointKnowledgeClient
            client = SharePointKnowledgeClient()
            assert not client.is_available()

    def test_client_import(self):
        """Knowledge client module imports cleanly."""
        from knowledge.sharepoint_client import (
            SharePointKnowledgeClient,
            KBResult,
            KBCitation,
            KNOWLEDGE_BASE_NAME,
        )
        assert KNOWLEDGE_BASE_NAME == "rccb-sop-knowledge-base"

    def test_kb_result_dataclass(self):
        """KBResult dataclass works correctly."""
        from knowledge.sharepoint_client import KBResult, KBCitation
        cit = KBCitation(index=1, source="SOP-WH-042", title="Spill Response")
        result = KBResult(
            response="Test response",
            citations=[cit],
            grounded=True,
            confidence=0.95,
        )
        assert result.response == "Test response"
        assert len(result.citations) == 1
        assert result.citations[0].source == "SOP-WH-042"


# --- token_provider tests ---

class TestTokenProvider:
    def test_import(self):
        """Token provider module imports cleanly."""
        from auth.token_provider import get_search_token, get_graph_token
        assert callable(get_search_token)
        assert callable(get_graph_token)

    def test_search_token_returns_none_without_credentials(self):
        """Returns None gracefully when no Azure credentials available."""
        from auth.token_provider import get_search_token
        import auth.token_provider as tp
        tp._cached_token = None
        with patch.dict("sys.modules", {}):
            with patch("azure.identity.DefaultAzureCredential", side_effect=Exception("no creds")):
                token = get_search_token()
                assert token is None

    def test_graph_token_returns_none_without_credentials(self):
        """Returns None gracefully when no Azure credentials available."""
        from auth.token_provider import get_graph_token
        with patch("azure.identity.DefaultAzureCredential", side_effect=Exception("no creds")):
            token = get_graph_token()
            assert token is None


# --- server integration tests ---

class TestServerKBIntegration:
    def test_server_imports_and_kb_client_available(self):
        """Server module imports and exposes _get_kb_client."""
        import server
        assert hasattr(server, '_get_kb_client')

    def test_search_sops_falls_back_to_mock(self):
        """search_sops returns mock results when KB is not available."""
        import server
        # Reset to ensure mock mode
        server._kb_client = None
        with patch.dict(os.environ, {"AZURE_SEARCH_SERVICE_ENDPOINT": ""}, clear=False):
            result = asyncio.get_event_loop().run_until_complete(
                server.search_sops("spill response")
            )
            assert "results" in result
            assert len(result["results"]) > 0

    def test_chat_falls_back_to_mock(self):
        """chat returns mock results when KB is not available."""
        import server
        server._kb_client = None
        with patch.dict(os.environ, {"AI_PROJECT_ENDPOINT": ""}, clear=False):
            result = asyncio.get_event_loop().run_until_complete(
                server.chat("How do I handle a spill?")
            )
            assert "response" in result
            assert "citations" in result
            assert len(result["response"]) > 0

    def test_chat_uses_kb_when_available(self):
        """chat uses KB client when available and returns structured results."""
        from knowledge.sharepoint_client import KBResult, KBCitation
        mock_result = KBResult(
            response="Follow SOP-WH-042 for spill response procedures.",
            citations=[
                KBCitation(
                    index=1,
                    source="SOP-WH-042",
                    title="Spill Response Procedures",
                    url="https://sharepoint.rccb.com/sop-wh-042",
                    snippet="When a spill occurs...",
                )
            ],
            grounded=True,
            confidence=0.97,
        )

        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.retrieve_indexed = AsyncMock(return_value=mock_result)

        import server
        server._kb_client = mock_client

        result = asyncio.get_event_loop().run_until_complete(
            server.chat("How do I handle a spill?")
        )

        assert result["response"] == "Follow SOP-WH-042 for spill response procedures."
        assert len(result["citations"]) == 1
        assert result["citations"][0]["source"] == "SOP-WH-042"
        assert result["grounded"] is True

        # Cleanup
        server._kb_client = None


# --- setup scripts tests ---

class TestSetupScripts:
    def test_setup_knowledge_sources_imports(self):
        """setup_knowledge_sources.py can be imported."""
        import scripts.setup_knowledge_sources as sks
        assert hasattr(sks, 'get_index_client')

    def test_setup_knowledge_base_imports(self):
        """setup_knowledge_base.py can be imported."""
        import scripts.setup_knowledge_base as skb
        assert hasattr(skb, 'create_knowledge_base')
        assert skb.KNOWLEDGE_BASE_NAME == "rccb-sop-knowledge-base"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
