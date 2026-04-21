"""Quick script to create knowledge sources and knowledge base via REST API."""
import os, json, requests, time
from dotenv import load_dotenv
load_dotenv(override=True)

endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
aoai = os.environ["AZURE_OPENAI_ENDPOINT"]
chat_deploy = os.environ["AZURE_OPENAI_CHATGPT_DEPLOYMENT"]
chat_model = os.environ["AZURE_OPENAI_CHATGPT_MODEL_NAME"]
embed_deploy = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
embed_model = os.environ["AZURE_OPENAI_EMBEDDING_MODEL_NAME"]
sp_url = os.environ["SHAREPOINT_SITE_URL"]

API_VERSION = "2025-11-01-preview"
HEADERS = {"api-key": key, "Content-Type": "application/json"}
PARAMS = {"api-version": API_VERSION}


def create_indexed_ks():
    aoai_uri = aoai.replace(".services.ai.azure.com", ".openai.azure.com")
    body = {
        "name": "Contoso-sop-indexed-ks",
        "kind": "indexedSharePoint",
        "description": "Contoso SOP documents indexed from SharePoint",
        "indexedSharePointParameters": {
            "connectionString": f"SharePointOnlineEndpoint={sp_url}",
            "containerName": "defaultSiteLibrary",
            "ingestionParameters": {
                "disableImageVerbalization": False,
                "contentExtractionMode": "minimal",
                "chatCompletionModel": {
                    "kind": "azureOpenAI",
                    "azureOpenAIParameters": {
                        "resourceUri": aoai_uri,
                        "deploymentId": chat_deploy,
                        "modelName": chat_model,
                    }
                },
                "embeddingModel": {
                    "kind": "azureOpenAI",
                    "azureOpenAIParameters": {
                        "resourceUri": aoai_uri,
                        "deploymentId": embed_deploy,
                        "modelName": embed_model,
                    }
                },
            },
        },
    }
    url = f"{endpoint}/knowledgesources/Contoso-sop-indexed-ks"
    r = requests.put(url, params=PARAMS, headers=HEADERS, json=body)
    print(f"[Indexed KS] Status: {r.status_code}")
    print(r.text[:600])
    return r.status_code in (200, 201)


def create_remote_ks():
    body = {
        "name": "Contoso-sop-remote-ks",
        "kind": "remoteSharePoint",
        "description": "Live query access to Contoso SOP documents in SharePoint",
        "remoteSharePointParameters": {},
    }
    url = f"{endpoint}/knowledgesources/Contoso-sop-remote-ks"
    r = requests.put(url, params=PARAMS, headers=HEADERS, json=body)
    print(f"\n[Remote KS] Status: {r.status_code}")
    print(r.text[:600])
    return r.status_code in (200, 201)


def create_knowledge_base():
    aoai_uri = aoai.replace(".services.ai.azure.com", ".openai.azure.com")
    body = {
        "name": "contoso-sop-knowledge-base",
        "description": "Contoso SOP Agentic Knowledge Base with answer synthesis",
        "models": [
            {
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": aoai_uri,
                    "deploymentId": chat_deploy,
                    "modelName": chat_model,
                }
            }
        ],
        "knowledgeSources": [
            {"name": "Contoso-sop-indexed-ks"},
            {"name": "Contoso-sop-remote-ks"},
        ],
        "outputMode": "answerSynthesis",
    }
    url = f"{endpoint}/knowledgebases/contoso-sop-knowledge-base"
    r = requests.put(url, params=PARAMS, headers=HEADERS, json=body)
    print(f"\n[Knowledge Base] Status: {r.status_code}")
    print(r.text[:600])
    return r.status_code in (200, 201)


def check_ingestion(ks_name, max_checks=10):
    print(f"\n[Ingestion] Monitoring {ks_name}...")
    for i in range(max_checks):
        url = f"{endpoint}/knowledgesources/{ks_name}/ingestionstatus"
        r = requests.get(url, params=PARAMS, headers={"api-key": key})
        if r.status_code == 200:
            data = r.json()
            status = data.get("synchronizationStatus", "unknown")
            state = data.get("currentSynchronizationState", {})
            processed = state.get("itemUpdatesProcessed", 0)
            failed = state.get("itemUpdatesFailed", 0)
            print(f"  Check {i+1}: status={status}, processed={processed}, failed={failed}")
            if status in ("completed", "idle"):
                print("  Ingestion complete!")
                return True
        else:
            print(f"  Check {i+1}: HTTP {r.status_code} - {r.text[:200]}")
        time.sleep(15)
    print("  Max checks reached, ingestion may still be running.")
    return False


def list_all():
    print("\n--- Knowledge Sources ---")
    r = requests.get(f"{endpoint}/knowledgesources", params=PARAMS, headers={"api-key": key})
    if r.status_code == 200:
        for s in r.json().get("value", []):
            print(f"  {s['name']} ({s.get('kind', '?')})")
    print("\n--- Knowledge Bases ---")
    r = requests.get(f"{endpoint}/knowledgebases", params=PARAMS, headers={"api-key": key})
    if r.status_code == 200:
        for kb in r.json().get("value", []):
            print(f"  {kb['name']}")
    else:
        print(f"  HTTP {r.status_code}: {r.text[:200]}")


if __name__ == "__main__":
    print("=" * 60)
    print("Contoso SOP Knowledge Source Provisioning")
    print("=" * 60)

    # Step 1: Create indexed SharePoint KS
    ok1 = create_indexed_ks()

    # Step 2: Create remote SharePoint KS
    ok2 = create_remote_ks()

    # Step 3: Monitor ingestion
    if ok1:
        check_ingestion("Contoso-sop-indexed-ks")

    # Step 4: Create knowledge base
    ok3 = create_knowledge_base()

    # Step 5: List everything
    list_all()

    print("\n" + "=" * 60)
    print("Done!" if (ok1 and ok2 and ok3) else "Some steps failed - check output above.")
    print("=" * 60)
