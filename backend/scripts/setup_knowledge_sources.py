"""
Setup script for Azure AI Search Knowledge Sources.
Creates both Indexed and Remote SharePoint knowledge sources
for the RCCB SOP RAG application.

Usage:
    cd sop-rag/backend
    .venv\\Scripts\\python scripts/setup_knowledge_sources.py
"""

import os
import json
import time
import logging

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    IndexedSharePointKnowledgeSource,
    IndexedSharePointKnowledgeSourceParameters,
    RemoteSharePointKnowledgeSource,
    RemoteSharePointKnowledgeSourceParameters,
    KnowledgeBaseAzureOpenAIModel,
    KnowledgeSourceAzureOpenAIVectorizer,
    KnowledgeSourceIngestionParameters,
    KnowledgeSourceContentExtractionMode,
    AzureOpenAIVectorizerParameters,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

load_dotenv(override=True)


def get_index_client() -> SearchIndexClient:
    endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
    return SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def create_indexed_sharepoint_ks(client: SearchIndexClient) -> str:
    """Create an Indexed SharePoint Knowledge Source.

    This indexes SP content into AI Search with chunking, vectorization,
    and semantic ranking for fast cached SOP queries.
    """
    name = "rccb-sop-indexed-ks"
    aoai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]

    chat_params = AzureOpenAIVectorizerParameters(
        resource_url=aoai_endpoint,
        deployment_name=os.environ["AZURE_OPENAI_CHATGPT_DEPLOYMENT"],
        model_name=os.environ["AZURE_OPENAI_CHATGPT_MODEL_NAME"],
    )

    embedding_params = AzureOpenAIVectorizerParameters(
        resource_url=aoai_endpoint,
        deployment_name=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        model_name=os.environ["AZURE_OPENAI_EMBEDDING_MODEL_NAME"],
    )

    # Build SharePoint connection string
    site_url = os.environ["SHAREPOINT_SITE_URL"]
    connection_string = f"SharePointOnlineEndpoint={site_url}"

    ingestion = KnowledgeSourceIngestionParameters(
        disable_image_verbalization=False,
        chat_completion_model=KnowledgeBaseAzureOpenAIModel(
            azure_open_ai_parameters=chat_params
        ),
        embedding_model=KnowledgeSourceAzureOpenAIVectorizer(
            azure_open_ai_parameters=embedding_params
        ),
        content_extraction_mode=KnowledgeSourceContentExtractionMode.MINIMAL,
    )

    container_name = os.environ.get("SHAREPOINT_CONTAINER_NAME", "defaultSiteLibrary")

    ks = IndexedSharePointKnowledgeSource(
        name=name,
        description="RCCB SOP documents indexed from SharePoint for agentic retrieval",
        indexed_share_point_parameters=IndexedSharePointKnowledgeSourceParameters(
            connection_string=connection_string,
            container_name=container_name,
            ingestion_parameters=ingestion,
        ),
    )

    logger.info(f"Creating indexed SharePoint knowledge source: {name}")
    client.create_or_update_knowledge_source(knowledge_source=ks)
    logger.info(f"Knowledge source '{name}' created successfully.")
    return name


def create_remote_sharepoint_ks(client: SearchIndexClient) -> str:
    """Create a Remote SharePoint Knowledge Source.

    This queries SP content live without indexing for real-time freshness.
    """
    name = "rccb-sop-remote-ks"

    ks = RemoteSharePointKnowledgeSource(
        name=name,
        description="Live query access to RCCB SOP documents in SharePoint",
        remote_share_point_parameters=RemoteSharePointKnowledgeSourceParameters(),
    )

    logger.info(f"Creating remote SharePoint knowledge source: {name}")
    client.create_or_update_knowledge_source(knowledge_source=ks)
    logger.info(f"Knowledge source '{name}' created successfully.")
    return name


def check_ingestion_status(client: SearchIndexClient, ks_name: str, max_wait: int = 300):
    """Monitor ingestion progress for indexed knowledge sources."""
    import requests

    endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]

    url = f"{endpoint}/knowledgesources/{ks_name}/status"
    params = {"api-version": "2025-11-01-preview"}
    headers = {"api-key": key}

    logger.info(f"Monitoring ingestion for '{ks_name}'...")
    start = time.time()

    while time.time() - start < max_wait:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            status = response.json()
            sync_status = status.get("synchronizationStatus", "unknown")
            current = status.get("currentSynchronizationState", {})
            processed = current.get("itemUpdatesProcessed", 0)
            failed = current.get("itemsUpdatesFailed", 0)

            logger.info(
                f"  Status: {sync_status} | Processed: {processed} | Failed: {failed}"
            )

            if sync_status not in ("creating", "active"):
                break
        else:
            logger.warning(f"  Status check returned {response.status_code}")

        time.sleep(15)

    logger.info("Ingestion monitoring complete.")


def list_knowledge_sources(client: SearchIndexClient):
    """List all knowledge sources on the search service."""
    import requests

    endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]

    url = f"{endpoint}/knowledgesources"
    params = {"api-version": "2025-11-01-preview", "$select": "name, kind"}
    headers = {"api-key": key}

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        sources = response.json().get("value", [])
        logger.info(f"Knowledge Sources ({len(sources)}):")
        for s in sources:
            logger.info(f"  - {s['name']} ({s.get('kind', 'unknown')})")
    else:
        logger.warning(f"List failed: {response.status_code} — {response.text}")


if __name__ == "__main__":
    client = get_index_client()

    # List existing
    list_knowledge_sources(client)

    # Create indexed SP knowledge source
    indexed_name = create_indexed_sharepoint_ks(client)

    # Create remote SP knowledge source
    remote_name = create_remote_sharepoint_ks(client)

    # Monitor indexed KS ingestion
    check_ingestion_status(client, indexed_name)

    # List final state
    list_knowledge_sources(client)

    logger.info("Setup complete!")
