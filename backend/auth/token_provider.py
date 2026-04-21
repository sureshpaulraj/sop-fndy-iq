"""
Token provider for Azure AI Search and SharePoint access.
Handles bearer token acquisition for remote SharePoint queries.
"""

import os
import logging

logger = logging.getLogger(__name__)

_cached_token: str | None = None


def get_search_token() -> str | None:
    """Get a bearer token for Azure AI Search / SharePoint access.

    For indexed queries: API key is sufficient (no token needed).
    For remote SP queries: Need a user-scoped bearer token.

    In production, this token comes from the user's MSAL session.
    For development, we use DefaultAzureCredential.
    """
    global _cached_token
    if _cached_token:
        return _cached_token

    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://search.azure.com/.default"
        )
        _cached_token = token_provider()
        logger.info("Search bearer token acquired via DefaultAzureCredential")
        return _cached_token
    except Exception as e:
        logger.warning(f"Could not acquire search token: {e}")
        return None


def get_graph_token() -> str | None:
    """Get a Microsoft Graph token for SharePoint access.

    Used when querying SharePoint via Graph API directly.
    """
    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://graph.microsoft.com/.default"
        )
        token = token_provider()
        logger.info("Graph bearer token acquired")
        return token
    except Exception as e:
        logger.warning(f"Could not acquire Graph token: {e}")
        return None
