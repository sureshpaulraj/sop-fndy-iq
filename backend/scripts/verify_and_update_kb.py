"""Verify and update KB to use blob KS with managed identity."""
import os, requests, json
from dotenv import load_dotenv
load_dotenv(override=True)

endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
aoai = os.environ["AZURE_OPENAI_ENDPOINT"].replace(".services.ai.azure.com", ".openai.azure.com")
headers = {"api-key": key, "Content-Type": "application/json"}
params = {"api-version": "2025-11-01-preview"}

# Step 1: Verify KS uses managed identity
print("=== Verify Blob KS ===")
r = requests.get(f"{endpoint}/knowledgesources/Contoso-sop-blob-ks", params=params, headers={"api-key": key})
data = r.json()
conn = data.get("azureBlobParameters", {}).get("connectionString", "")
uses_mi = "ResourceId" in conn
print(f"Connection: {conn[:80]}...")
print(f"Uses managed identity (ResourceId): {uses_mi}")
print(f"Created: {json.dumps(data.get('azureBlobParameters', {}).get('createdResources', {}), indent=2)}")

# Step 2: Update KB to use blob KS
print("\n=== Update Knowledge Base ===")
body = {
    "name": "contoso-sop-knowledge-base",
    "description": "Contoso SOP Knowledge Base — blob-indexed SOPs with answer synthesis (managed identity)",
    "models": [{
        "kind": "azureOpenAI",
        "azureOpenAIParameters": {
            "resourceUri": aoai,
            "deploymentId": "gpt-4.1",
            "modelName": "gpt-4.1",
        },
    }],
    "knowledgeSources": [{"name": "Contoso-sop-blob-ks"}],
    "outputMode": "answerSynthesis",
}
r = requests.put(f"{endpoint}/knowledgebases/contoso-sop-knowledge-base", params=params, headers=headers, json=body)
print(f"KB Update Status: {r.status_code}")
if r.status_code in (200, 201):
    kb = r.json()
    print(f"Sources: {[s['name'] for s in kb.get('knowledgeSources', [])]}")
else:
    print(r.text[:300])

# Step 3: Check indexer status
print("\n=== Indexer Status ===")
r = requests.get(f"{endpoint}/indexers('Contoso-sop-blob-ks-indexer')/search.status", params=params, headers={"api-key": key})
if r.status_code == 200:
    idx = r.json()
    last = idx.get("lastResult", {})
    print(f"Status: {last.get('status', '?')}")
    print(f"Items indexed: {last.get('itemCount', 0)}")
    print(f"Failed: {last.get('failedItemCount', 0)}")
else:
    print(f"Indexer status: HTTP {r.status_code}")

# Step 4: Check index doc count
print("\n=== Index Document Count ===")
r = requests.get(f"{endpoint}/indexes('Contoso-sop-blob-ks-index')/docs/$count", params=params, headers={"api-key": key})
print(f"Documents in index: {r.text.strip()}")

# Step 5: Test KB retrieval
print("\n=== Test KB Retrieval ===")
body = {"messages": [{"role": "user", "content": [{"type": "text", "text": "What is the spill response procedure?"}]}]}
r = requests.post(f"{endpoint}/knowledgebases('contoso-sop-knowledge-base')/retrieve", params=params, headers=headers, json=body)
print(f"Retrieve Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    for msg in data.get("response", []):
        for c in msg.get("content", []):
            print(f"Response: {c.get('text', '')[:500]}")
    refs = data.get("references", [])
    print(f"Citations: {len(refs)}")
    for ref in refs[:5]:
        print(f"  - {ref.get('title', '?')}: {ref.get('url', 'no-url')}")
else:
    err = r.json().get("error", {}).get("message", r.text[:300])
    print(f"Error: {err}")
