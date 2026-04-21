"""Test blob-based KB with safe query."""
import os, requests, json
from dotenv import load_dotenv
load_dotenv(override=True)

endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
key = os.environ["AZURE_SEARCH_ADMIN_KEY"]

query = "What are the company health policies?"
body = {"messages": [{"role": "user", "content": [{"type": "text", "text": query}]}]}

for kb_name in ["upload-blob-knowledge-base-minimal", "hrdocs-knowledge-base", "kb-livsrcsvc"]:
    r = requests.post(
        f"{endpoint}/knowledgebases('{kb_name}')/retrieve",
        params={"api-version": "2025-11-01-preview"},
        headers={"api-key": key, "Content-Type": "application/json"},
        json=body,
    )
    print(f"\n--- {kb_name}: HTTP {r.status_code} ---")
    data = r.json()
    if r.status_code == 200:
        for msg in data.get("response", []):
            for c in msg.get("content", []):
                print(c.get("text", "")[:300])
        refs = [ref.get("title", "?") for ref in data.get("references", [])]
        print(f"References: {refs}")
    else:
        print(data.get("error", {}).get("message", json.dumps(data)[:300]))
