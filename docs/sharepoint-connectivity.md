# SharePoint Online Connectivity — SOP Document Retrieval

> Reference for connecting SharePoint Online as a knowledge source for the SOP RAG agents.
> Sources: [SharePoint Tool (preview)](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/sharepoint?view=foundry) · [Foundry IQ Connect](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/foundry-iq-connect?view=foundry)

## Overview

This project retrieves SOP documents from SharePoint Online in two ways:

1. **Foundry IQ — Indexed SharePoint Knowledge Source** (primary): SOP documents in SharePoint are indexed into Azure AI Search via Foundry IQ. The agentic retrieval pipeline queries the index and returns grounded answers with citations. This path uses the `KnowledgeBaseRetrievalClient` REST API.

2. **SharePoint Grounding Tool** (direct agent tool): The Foundry Agent Service `SharepointPreviewTool` connects directly to SharePoint using OBO (On-Behalf-Of) identity passthrough and the Microsoft 365 Copilot Retrieval API.

## Architecture

```
                          ┌──────────────────────────┐
                          │   SharePoint Online       │
                          │   /sites/Contoso-SOPs     │
                          │   └── ContosoSOPs Docs    │
                          └──────────┬───────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │ (indexed)      │                 │ (direct)
                    ▼                │                 ▼
        ┌───────────────────┐       │     ┌────────────────────────┐
        │ Azure AI Search   │       │     │ SharePoint Grounding   │
        │ Foundry IQ KB     │       │     │ Tool (preview)         │
        │ contoso-sop-kb    │       │     │ OBO identity passthru  │
        └───────┬───────────┘       │     └──────────┬─────────────┘
                │ agentic retrieval │                 │
                ▼                   │                 ▼
        ┌───────────────────────────┴─────────────────────────┐
        │              Foundry Agent Service                    │
        │              (SOP Orchestrator Agent)                 │
        └──────────────────────┬──────────────────────────────┘
                               │
                               ▼
                        React Frontend
```

## Path 1: Foundry IQ Indexed SharePoint (Current Implementation)

### Configuration

Defined in [backend/knowledge/sharepoint_client.py](../sop-rag/backend/knowledge/sharepoint_client.py):

| Constant | Value | Purpose |
|---|---|---|
| `KNOWLEDGE_BASE_NAME` | `contoso-sop-knowledge-base` | Foundry IQ knowledge base name in AI Search |
| `INDEXED_KS_NAME` | `Contoso-sop-sp-indexed-ks` | Indexed SharePoint knowledge source (auto-chunked, vectorized) |
| `REMOTE_KS_NAME` | `Contoso-sop-remote-ks` | Remote SharePoint source (live query via M365 Copilot API) |

### Environment Variables

From [.env.template](../sop-rag/backend/.env.template):

```env
AZURE_SEARCH_SERVICE_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_ADMIN_KEY=<key>
AZURE_SEARCH_CONNECTION_NAME=<connection-name>
SHAREPOINT_SITE_URL=https://enterpriselandingzone.sharepoint.com/sites/Contoso-SOPs
SHAREPOINT_DOCUMENT_LIBRARY=ContosoSOPs Docs
```

### How It Works

1. SharePoint documents are indexed into Azure AI Search by the Foundry IQ indexer
2. The `SharePointKnowledgeClient.retrieve_rest()` method calls the AI Search KB retrieval API:
   ```
   POST {endpoint}/knowledgebases('contoso-sop-knowledge-base')/retrieve?api-version=2025-11-01-preview
   ```
3. The request body specifies `indexedSharePoint` knowledge source with `includeReferences: true`
4. Responses include grounded text + reference citations with SharePoint doc URLs
5. The client parses blob, indexedSharePoint, and remoteSharePoint reference types
6. Citations are deduplicated by SOP number and returned to the agent

### Reference Parsing

The client handles three reference types from the KB API response:

| `type` | URL Source | Example |
|---|---|---|
| `azureBlob` | `ref.blobUrl` | Direct blob storage URL |
| `indexedSharePoint` | `ref.sourceData.doc_url` | SharePoint drive path, reconstructed to clickable URL |
| `remoteSharePoint` | `ref.sourceData.doc_url` | Same as indexed, from live M365 query |

Clickable URLs are constructed as: `{SHAREPOINT_SITE_URL}/{SHAREPOINT_DOCUMENT_LIBRARY}/{filename}`

## Path 2: SharePoint Grounding Tool (Direct)

The Foundry Agent Service provides a native `SharepointPreviewTool` for direct SharePoint access. This is an alternative to the indexed path when you want live, un-indexed document retrieval.

### Prerequisites

- Microsoft 365 Copilot license **or** [pay-as-you-go model](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/paygo-retrieval) enabled
- `Azure AI User` RBAC role on the Foundry project
- User has `READ` access to the SharePoint site
- SharePoint tenant and Foundry project in the **same Entra tenant**
- SDK: `pip install "azure-ai-projects>=2.0.0"`

### Setup Steps

1. **Add a SharePoint connection** in the Foundry portal:
   - Navigate to your project → Settings → Connections
   - Add new connection → SharePoint
   - Site URL: `https://enterpriselandingzone.sharepoint.com/sites/Contoso-SOPs`
   - Save and copy the connection ID

2. **Set environment variable**:
   ```env
   SHAREPOINT_PROJECT_CONNECTION_ID=/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}/connections/{connection}
   ```

### Code Example

```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    SharepointPreviewTool,
    SharepointGroundingToolParameters,
    ToolProjectConnection,
)

project = AIProjectClient(
    endpoint="https://<resource>.ai.azure.com/api/projects/<project>",
    credential=DefaultAzureCredential(),
)
openai = project.get_openai_client()

# Get connection from Foundry project
sp_connection = project.connections.get("my-sharepoint-connection")

# Configure SharePoint tool
sp_tool = SharepointPreviewTool(
    sharepoint_grounding_preview=SharepointGroundingToolParameters(
        project_connections=[
            ToolProjectConnection(project_connection_id=sp_connection.id)
        ]
    )
)

# Create agent with SharePoint tool
agent = project.agents.create_version(
    agent_name="sop-sp-agent",
    definition=PromptAgentDefinition(
        model="gpt-4.1-mini",
        instructions="You help users find SOP information from SharePoint. Use the SharePoint tool.",
        tools=[sp_tool],
    ),
)

# Query — uses streaming via Responses API
stream = openai.responses.create(
    stream=True,
    tool_choice="required",
    input="What is the forklift inspection procedure?",
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
)

for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="")
    elif event.type == "response.output_item.done":
        if event.item.type == "message":
            for annotation in event.item.content[-1].annotations:
                if annotation.type == "url_citation":
                    print(f"\n[Citation: {annotation.url}]")
```

### Limitations

- **User identity only** — app-only / service principal auth not supported
- **Same tenant** — SharePoint site and Foundry agent must be in the same Entra tenant
- **One per agent** — only one SharePoint tool per agent is supported
- **Text only** — images and charts in documents are not retrieved
- **Supported file types**: `.doc`, `.docx`, `.pptx`, `.pdf`, `.aspx`, `.one`
- **Does not work** when the agent is published to Microsoft Teams

## Comparing the Two Paths

| Aspect | Foundry IQ (Indexed) | SharePoint Grounding Tool |
|---|---|---|
| **Data freshness** | Periodic indexer runs (configurable) | Live query, always current |
| **Search quality** | Hybrid (keyword + vector + semantic rerank) | M365 Copilot semantic indexing |
| **ACL enforcement** | Synced ACLs at index time | OBO identity passthrough at query time |
| **Licensing** | No M365 Copilot license needed | M365 Copilot license or pay-as-you-go |
| **Latency** | Faster (pre-indexed) | Slightly slower (live retrieval) |
| **Multi-source** | Yes — combine SP + Blob + OneLake + web | SharePoint only |
| **File types** | Any text-extractable format | .doc, .docx, .pptx, .pdf, .aspx, .one |
| **Best for** | Production RAG with complex queries | Quick proof-of-concept, always-live access |

## Terraform Infrastructure

SharePoint connectivity depends on the AI Search service defined in [infra/ai-search.tf](../sop-rag/infra/ai-search.tf):

```hcl
resource "azurerm_search_service" "sop" {
  name                = "search-${var.project_name}-${var.environment}"
  sku                 = var.ai_search_sku
  semantic_search { sku = "standard" }   # Required for agentic retrieval
  identity { type = "SystemAssigned" }
}
```

The knowledge base and knowledge sources are created via the Foundry portal or API (not Terraform), as they require the AI Search agentic retrieval preview API (`2025-11-01-preview`).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `AppOnly OBO tokens not supported` | Using service principal instead of user identity | Use user identity (OBO) for SharePoint tool |
| `Authorization Failed - User does not have valid license` | Missing M365 Copilot license | Assign license or enable pay-as-you-go |
| 401 / auth failures | Cross-tenant access attempt | Verify SP site and Foundry project are in same tenant |
| Tool returns no results | User lacks SP read access | Grant user `READ` on the SharePoint site |
| Empty `sourceData` in KB response | `includeReferenceSourceData` not set | Set `includeReferenceSourceData: true` in retrieve call |
| `KB REST retrieve failed: 404` | Wrong KB name or endpoint | Verify `AZURE_SEARCH_SERVICE_ENDPOINT` and `KNOWLEDGE_BASE_NAME` |
| Stale content in indexed path | Indexer hasn't run | Trigger incremental indexer run or check schedule |

## Reference Links

- [SharePoint Tool (preview)](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/sharepoint?view=foundry)
- [Connect Foundry IQ KB to Agent Service](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/foundry-iq-connect?view=foundry)
- [Foundry IQ Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/what-is-foundry-iq?view=foundry)
- [Azure AI Search Tool](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/ai-search?view=foundry)
- [M365 Copilot Retrieval API](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api-reference/retrieval-api-overview)
- [Semantic Indexing for M365 Copilot](https://learn.microsoft.com/en-us/microsoftsearch/semantic-index-for-copilot)
- [Agent Identity Concepts](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/agent-identity?view=foundry)
- [Add Connections to Your Project](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/connections-add?view=foundry)
