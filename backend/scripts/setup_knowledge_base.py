"""
Setup script for Azure AI Search Knowledge Base.
Creates a knowledge base referencing both Indexed and Remote
SharePoint knowledge sources with answer synthesis enabled.

Usage:
    cd sop-rag/backend
    .venv\\Scripts\\python scripts/setup_knowledge_base.py
"""

import os
import logging

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel,
    KnowledgeRetrievalOutputMode,
    KnowledgeSourceReference,
    AzureOpenAIVectorizerParameters,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

load_dotenv(override=True)

KNOWLEDGE_BASE_NAME = "contoso-sop-knowledge-base"
INDEXED_KS_NAME = "Contoso-sop-indexed-ks"
REMOTE_KS_NAME = "Contoso-sop-remote-ks"


def get_index_client() -> SearchIndexClient:
    endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
    return SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def create_knowledge_base(client: SearchIndexClient):
    """Create a knowledge base with answer synthesis referencing both KS."""
    aoai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]

    aoai_params = AzureOpenAIVectorizerParameters(
        resource_url=aoai_endpoint,
        deployment_name=os.environ["AZURE_OPENAI_CHATGPT_DEPLOYMENT"],
        model_name=os.environ["AZURE_OPENAI_CHATGPT_MODEL_NAME"],
    )

    kb = KnowledgeBase(
        name=KNOWLEDGE_BASE_NAME,
        description="Contoso SOP Agentic Knowledge Base — answers questions using SharePoint SOP documents with citations",
        models=[KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=aoai_params)],
        knowledge_sources=[
            KnowledgeSourceReference(name=INDEXED_KS_NAME),
            KnowledgeSourceReference(name=REMOTE_KS_NAME),
        ],
        output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
    )

    logger.info(f"Creating knowledge base: {KNOWLEDGE_BASE_NAME}")
    client.create_or_update_knowledge_base(kb)
    logger.info(f"Knowledge base '{KNOWLEDGE_BASE_NAME}' created successfully.")
    logger.info(f"  Sources: {INDEXED_KS_NAME}, {REMOTE_KS_NAME}")
    logger.info(f"  Output mode: ANSWER_SYNTHESIS")


def list_knowledge_bases(client: SearchIndexClient):
    """List all knowledge bases."""
    import requests

    endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]

    url = f"{endpoint}/knowledgebases"
    params = {"api-version": "2025-11-01-preview"}
    headers = {"api-key": key}

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        bases = response.json().get("value", [])
        logger.info(f"Knowledge Bases ({len(bases)}):")
        for kb in bases:
            logger.info(f"  - {kb['name']}")
    else:
        logger.warning(f"List failed: {response.status_code}")


if __name__ == "__main__":
    client = get_index_client()
    create_knowledge_base(client)
    list_knowledge_bases(client)
    logger.info("Knowledge base setup complete!")
