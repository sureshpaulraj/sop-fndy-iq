"""Quick test of the live knowledge base retrieval."""
import os, sys, requests, json
from dotenv import load_dotenv
load_dotenv(override=True)

endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
key = os.environ["AZURE_SEARCH_ADMIN_KEY"]

# Read token from file (created by PowerShell)
token_file = os.path.join(os.path.dirname(__file__), "..", ".graph_token.tmp")
if os.path.exists(token_file):
    with open(token_file) as f:
        token = f.read().strip()
    print(f"Token loaded: {token[:20]}...")
else:
    print("ERROR: No token file found. Run: az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv > .graph_token.tmp")
    sys.exit(1)

query = sys.argv[1] if len(sys.argv) > 1 else "What is the spill response procedure?"
print(f"\nQuery: {query}")

body = {
    "messages": [{"role": "user", "content": [{"type": "text", "text": query}]}],
    "includeActivity": True,
}

r = requests.post(
    f"{endpoint}/knowledgebases('contoso-sop-knowledge-base')/retrieve",
    params={"api-version": "2025-11-01-preview"},
    headers={
        "api-key": key,
        "Content-Type": "application/json",
        "x-ms-query-source-authorization": f"Bearer {token}",
    },
    json=body,
)

print(f"\nHTTP Status: {r.status_code}")
data = r.json()
print(json.dumps(data, indent=2)[:5000])
