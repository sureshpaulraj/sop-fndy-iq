"""
Upload RCCB SOP documents to Azure Blob Storage and create
an indexed blob knowledge source + knowledge base.
This bypasses the SharePoint auth requirement.
"""
import os, requests, json, time, glob
from dotenv import load_dotenv
load_dotenv(override=True)

endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
aoai = os.environ["AZURE_OPENAI_ENDPOINT"].replace(".services.ai.azure.com", ".openai.azure.com")
chat_deploy = os.environ["AZURE_OPENAI_CHATGPT_DEPLOYMENT"]
embed_deploy = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

API_VERSION = "2025-11-01-preview"
HEADERS = {"api-key": key, "Content-Type": "application/json"}
PARAMS = {"api-version": API_VERSION}

KS_NAME = "rccb-sop-blob-ks"
KB_NAME = "rccb-sop-knowledge-base"


def get_blob_connection_string():
    """Get the blob connection string from environment."""
    conn = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    if conn:
        print(f"Using blob connection string from env (length={len(conn)})")
        return conn
    print("WARNING: AZURE_STORAGE_CONNECTION_STRING not set in .env")
    return None


def upload_sops_to_blob(connection_string: str, container_name: str = "rccb-sops"):
    """Upload SOP markdown files to a blob container."""
    from azure.storage.blob import BlobServiceClient
    from azure.identity import DefaultAzureCredential

    # Try key-based first, fall back to identity
    try:
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        blob_service.get_account_information()
    except Exception:
        print("Key auth not permitted, using DefaultAzureCredential...")
        # Extract account URL from connection string
        account_name = ""
        for part in connection_string.split(";"):
            if part.startswith("AccountName="):
                account_name = part.split("=", 1)[1]
        account_url = f"https://{account_name}.blob.core.windows.net"
        blob_service = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())

    # Create container if not exists
    try:
        container = blob_service.create_container(container_name)
        print(f"Created container: {container_name}")
    except Exception:
        container = blob_service.get_container_client(container_name)
        print(f"Container exists: {container_name}")

    # Upload all mock SOP files
    sop_dir = os.path.join(os.path.dirname(__file__), "..", "mock-sops")
    sop_files = glob.glob(os.path.join(sop_dir, "*.md"))

    for fpath in sop_files:
        blob_name = os.path.basename(fpath)
        with open(fpath, "rb") as f:
            container.upload_blob(blob_name, f, overwrite=True)
        print(f"  Uploaded: {blob_name}")

    print(f"Uploaded {len(sop_files)} SOP documents to blob container '{container_name}'")
    return container_name


def create_blob_ks(connection_string: str, container_name: str):
    """Create an indexed Azure Blob knowledge source."""
    body = {
        "name": KS_NAME,
        "kind": "azureBlob",
        "description": "RCCB SOP documents indexed from Azure Blob Storage",
        "azureBlobParameters": {
            "connectionString": connection_string,
            "containerName": container_name,
            "ingestionParameters": {
                "disableImageVerbalization": False,
                "contentExtractionMode": "minimal",
                "embeddingModel": {
                    "kind": "azureOpenAI",
                    "azureOpenAIParameters": {
                        "resourceUri": aoai,
                        "deploymentId": embed_deploy,
                        "modelName": embed_deploy,
                    },
                },
            },
        },
    }
    r = requests.put(
        f"{endpoint}/knowledgesources/{KS_NAME}",
        params=PARAMS, headers=HEADERS, json=body,
    )
    print(f"\n[Blob KS] Status: {r.status_code}")
    if r.status_code in (200, 201):
        data = r.json()
        created = data.get("azureBlobParameters", {}).get("createdResources", {})
        print(f"  Created resources: {json.dumps(created, indent=4)}")
        return True
    else:
        print(f"  Error: {r.text[:500]}")
        return False


def update_knowledge_base():
    """Update the KB to use the blob KS (no user token needed)."""
    body = {
        "name": KB_NAME,
        "description": "RCCB SOP Knowledge Base — answers from blob-indexed SOPs with citations",
        "models": [{
            "kind": "azureOpenAI",
            "azureOpenAIParameters": {
                "resourceUri": aoai,
                "deploymentId": chat_deploy,
                "modelName": chat_deploy,
            },
        }],
        "knowledgeSources": [{"name": KS_NAME}],
        "outputMode": "answerSynthesis",
    }
    r = requests.put(
        f"{endpoint}/knowledgebases/{KB_NAME}",
        params=PARAMS, headers=HEADERS, json=body,
    )
    print(f"\n[Knowledge Base] Status: {r.status_code}")
    if r.status_code in (200, 201):
        print(f"  KB '{KB_NAME}' updated to use blob KS '{KS_NAME}'")
        return True
    else:
        print(f"  Error: {r.text[:500]}")
        return False


def wait_for_indexing(max_checks=20):
    """Wait for the blob KS indexer to finish."""
    # Get the indexer name from the KS
    r = requests.get(f"{endpoint}/knowledgesources/{KS_NAME}", params=PARAMS, headers={"api-key": key})
    if r.status_code != 200:
        print("Could not get KS details")
        return False

    indexer_name = r.json().get("azureBlobParameters", {}).get("createdResources", {}).get("indexer", "")
    if not indexer_name:
        print("No indexer found, skipping wait")
        return True

    print(f"\n[Indexer] Waiting for '{indexer_name}' to complete...")
    for i in range(max_checks):
        r = requests.get(
            f"{endpoint}/indexers('{indexer_name}')/search.status",
            params=PARAMS, headers={"api-key": key},
        )
        if r.status_code == 200:
            data = r.json()
            history = data.get("lastResult", {})
            status = history.get("status", "unknown")
            items = history.get("itemCount", 0)
            failed = history.get("failedItemCount", 0)
            print(f"  Check {i+1}: status={status}, items={items}, failed={failed}")
            if status in ("success", "transientFailure"):
                return status == "success"
        else:
            print(f"  Check {i+1}: HTTP {r.status_code}")
        time.sleep(10)
    return False


def test_kb():
    """Test the KB retrieval."""
    body = {"messages": [{"role": "user", "content": [{"type": "text", "text": "What is the spill response procedure?"}]}]}
    r = requests.post(
        f"{endpoint}/knowledgebases('{KB_NAME}')/retrieve",
        params=PARAMS, headers=HEADERS, json=body,
    )
    print(f"\n[Test] KB Retrieval Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        for msg in data.get("response", []):
            for c in msg.get("content", []):
                print(f"  Response: {c.get('text', '')[:500]}")
        refs = data.get("references", [])
        print(f"  Citations: {len(refs)} references")
        for ref in refs[:3]:
            print(f"    - {ref.get('title', '?')}: {ref.get('url', 'no-url')}")
        return True
    else:
        print(f"  Error: {r.json().get('error', {}).get('message', r.text[:300])}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("RCCB SOP Blob Knowledge Source Setup")
    print("=" * 60)

    # Step 1: Get blob connection string
    conn_str = get_blob_connection_string()
    if not conn_str:
        print("FATAL: No blob connection string available")
        exit(1)

    # Step 2: Upload SOPs to blob
    container = upload_sops_to_blob(conn_str)

    # Step 3: Create blob KS
    ok = create_blob_ks(conn_str, container)
    if not ok:
        print("FATAL: Failed to create blob KS")
        exit(1)

    # Step 4: Wait for indexing
    wait_for_indexing()

    # Step 5: Update KB
    update_knowledge_base()

    # Step 6: Test
    test_kb()

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
