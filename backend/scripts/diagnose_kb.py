"""List all indexes and knowledge bases on the search service."""
import os, requests, json
from dotenv import load_dotenv
load_dotenv(override=True)

endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
headers = {"api-key": key}
params = {"api-version": "2025-11-01-preview"}

print("=== INDEXES ===")
r = requests.get(f"{endpoint}/indexes", params={**params, "$select": "name"}, headers=headers)
for idx in r.json().get("value", []):
    name = idx["name"]
    r2 = requests.get(f"{endpoint}/indexes('{name}')/docs/$count", params=params, headers=headers)
    print(f"  {name}: {r2.text.strip()} docs")

print("\n=== KNOWLEDGE SOURCES ===")
r = requests.get(f"{endpoint}/knowledgesources", params=params, headers=headers)
for ks in r.json().get("value", []):
    print(f"  {ks['name']} ({ks.get('kind', '?')})")

print("\n=== KNOWLEDGE BASES ===")
r = requests.get(f"{endpoint}/knowledgebases", params=params, headers=headers)
for kb in r.json().get("value", []):
    sources = [s["name"] for s in kb.get("knowledgeSources", [])]
    print(f"  {kb['name']} -> {sources}")

# Test KB retrieval WITHOUT user token (should fail for remote SP)
print("\n=== TEST KB RETRIEVAL (no user token) ===")
body = {"messages": [{"role": "user", "content": [{"type": "text", "text": "spill response procedure"}]}]}
r = requests.post(f"{endpoint}/knowledgebases('rccb-sop-knowledge-base')/retrieve",
    params=params, headers={**headers, "Content-Type": "application/json"}, json=body)
print(f"  rccb-sop-knowledge-base: HTTP {r.status_code}")
if r.status_code != 200:
    print(f"  Error: {r.json().get('error', {}).get('message', r.text[:200])}")

# Test an existing blob-based KB (should work without token)
for kb_name in ["upload-blob-knowledge-base-minimal", "upload-blob-knowledge-base-standard", "kb-livsrcsvc"]:
    r = requests.post(f"{endpoint}/knowledgebases('{kb_name}')/retrieve",
        params=params, headers={**headers, "Content-Type": "application/json"}, json=body)
    print(f"  {kb_name}: HTTP {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        resp_text = ""
        for msg in data.get("response", []):
            for c in msg.get("content", []):
                resp_text += c.get("text", "")
        refs = [ref.get("title", "?") for ref in data.get("references", [])]
        print(f"    Response: {resp_text[:150]}...")
        print(f"    References: {refs}")
