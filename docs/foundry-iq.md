# Foundry IQ — Knowledge Layer for SOP Agents

> Reference for integrating Foundry IQ with the SOP RAG agentic application.
> Source: [What is Foundry IQ](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/what-is-foundry-iq?view=foundry)

## What is Foundry IQ

Foundry IQ is a managed knowledge layer in Microsoft Foundry that gives agents permission-aware access to enterprise data. It creates a configurable, multi-source **knowledge base** that agents query via **agentic retrieval** — a pipeline that decomposes complex questions into subqueries, runs them in parallel across knowledge sources, semantically reranks results, and returns grounded answers with citations.

Azure AI Search provides the underlying indexing and retrieval infrastructure.

## Key Concepts

| Concept | Description |
|---|---|
| **Knowledge Base** | Top-level resource that orchestrates agentic retrieval. Defines which knowledge sources to query and retrieval parameters (reasoning effort: minimal / low / medium). |
| **Knowledge Source** | Connection to indexed or remote content. A knowledge base references one or more knowledge sources. Types: `indexedSharePoint`, `remoteSharePoint`, `azureBlob`, `searchIndex`, `oneLake`, `web`. |
| **Agentic Retrieval** | Multi-query pipeline: decomposes → parallel search → semantic rerank → unified response. Uses an optional LLM (e.g., GPT-4.1-mini) for query planning. |
| **MCP Endpoint** | Each knowledge base exposes `knowledge_base_retrieve` as an MCP tool at `{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2025-11-01-preview`. |

## Capabilities

- Connect **one knowledge base to multiple agents** — shared knowledge layer
- Supported sources: Azure Blob Storage, SharePoint Online, OneLake, public web
- Automated document chunking, vector embedding generation, metadata extraction
- Keyword, vector, or hybrid queries across indexed and remote sources
- Extractive responses with **citations** — agents trace answers to source docs
- **ACL synchronization** and Microsoft Purview sensitivity label enforcement
- Queries run under the caller's **Entra identity** for end-to-end permission enforcement
- Incremental indexer runs for data refresh

## How It Applies to This Project

This SOP RAG application uses Foundry IQ in the following way:

```
User Query → Foundry Agent Service (GPT-4.1)
                ↓ MCP tool call
             Foundry IQ Knowledge Base ("contoso-sop-knowledge-base")
                ├── Indexed SharePoint KS (SOPs from SharePoint Online)
                └── Azure Blob KS (supplementary docs)
                ↓ agentic retrieval
             Grounded answer + citations → Agent → User
```

### Project Knowledge Base Configuration

| Setting | Value |
|---|---|
| Knowledge Base Name | `contoso-sop-knowledge-base` |
| Indexed KS Name | `Contoso-sop-sp-indexed-ks` |
| Remote KS Name | `Contoso-sop-remote-ks` |
| AI Search Endpoint | `AZURE_SEARCH_SERVICE_ENDPOINT` env var |
| API Version | `2025-11-01-preview` |

These are defined in [backend/knowledge/sharepoint_client.py](../sop-rag/backend/knowledge/sharepoint_client.py).

## Connecting to Foundry Agent Service

### 1. Create a Project Connection (RemoteTool / MCP)

```python
import requests
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

credential = DefaultAzureCredential()
project_resource_id = "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.MachineLearningServices/workspaces/{account}/projects/{project}"
connection_name = "sop-kb-mcp-connection"
mcp_endpoint = f"{search_endpoint}/knowledgebases/contoso-sop-knowledge-base/mcp?api-version=2025-11-01-preview"

bearer = get_bearer_token_provider(credential, "https://management.azure.com/.default")
requests.put(
    f"https://management.azure.com{project_resource_id}/connections/{connection_name}?api-version=2025-10-01-preview",
    headers={"Authorization": f"Bearer {bearer()}"},
    json={
        "name": connection_name,
        "type": "Microsoft.MachineLearningServices/workspaces/connections",
        "properties": {
            "authType": "ProjectManagedIdentity",
            "category": "RemoteTool",
            "target": mcp_endpoint,
            "isSharedToAll": True,
            "audience": "https://search.azure.com/",
            "metadata": {"ApiType": "Azure"}
        }
    }
).raise_for_status()
```

### 2. Create an Agent with MCP Tool

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool

project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

mcp_tool = MCPTool(
    server_label="knowledge-base",
    server_url=mcp_endpoint,
    require_approval="never",
    allowed_tools=["knowledge_base_retrieve"],
    project_connection_id=connection_name,
)

agent = project.agents.create_version(
    agent_name="sop-assistant",
    definition=PromptAgentDefinition(
        model="gpt-4.1",
        instructions="""You are a helpful SOP assistant. Use the knowledge base tool to answer questions.
If the knowledge base doesn't contain the answer, respond with "I don't know".
Always include citations to retrieved sources.""",
        tools=[mcp_tool],
    ),
)
```

### 3. Invoke the Agent

```python
openai = project.get_openai_client()
conversation = openai.conversations.create()

response = openai.responses.create(
    conversation=conversation.id,
    input="What is the spill cleanup procedure?",
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
)
print(response.output_text)
```

## RBAC Requirements

| Role | Scope | Purpose |
|---|---|---|
| `Azure AI User` | Foundry parent resource | Access model deployments, create agents |
| `Azure AI Project Manager` | Foundry parent resource | Create project connections |
| `Search Index Data Reader` | AI Search service | Read knowledge base content |
| `Search Index Data Contributor` | AI Search service | Write to indexes (if needed) |

## Relationship to Other IQ Workloads

| Workload | Focus |
|---|---|
| **Foundry IQ** | Enterprise data (Azure, SharePoint, OneLake, web) — used by this project |
| **Fabric IQ** | Business analytics (OneLake, Power BI semantic models) |
| **Work IQ** | Collaboration signals (M365 documents, meetings, chats) |

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| 403 from AI Search | Missing RBAC role | Add `Search Index Data Reader` to project managed identity |
| 400/404 from MCP endpoint | Wrong endpoint or KB name | Verify `AZURE_SEARCH_SERVICE_ENDPOINT` and KB name match |
| Agent doesn't ground answers | Tool not configured or instructions too weak | Ensure `allowed_tools` includes `knowledge_base_retrieve`; strengthen instructions |
| Empty citations | Content not yet indexed | Wait for indexer run or trigger manual run |

## Reference Links

- [Foundry IQ Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/what-is-foundry-iq?view=foundry)
- [Connect Foundry IQ KB to Agent Service](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/foundry-iq-connect?view=foundry)
- [Create a Knowledge Base in AI Search](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-create-knowledge-base)
- [Knowledge Source Overview](https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-overview)
- [Agentic Retrieval Pipeline Sample (GitHub)](https://github.com/Azure-Samples/azure-search-python-samples/tree/main/agentic-retrieval-pipeline-example)
- [Tool Best Practices](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/tool-best-practice?view=foundry)
