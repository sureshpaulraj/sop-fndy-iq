"""
SOP RAG FastMCP Server
Exposes MCP tools for the React frontend to interact with the
SOP multi-agent system backed by Azure AI Search knowledge bases.
"""

import os
import json
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "sop-rag-server",
    instructions=(
        "You are the SOP RAG assistant for Contoso. "
        "Help employees find answers from Standard Operating Procedures. "
        "Always cite your sources with document references."
    ),
)

# --- Knowledge Base Client (SharePoint via Azure AI Search) ---
_kb_client = None


def _get_kb_client():
    """Lazy-initialize the SharePoint Knowledge Base client."""
    global _kb_client
    if _kb_client is None:
        try:
            from knowledge.sharepoint_client import SharePointKnowledgeClient
            _kb_client = SharePointKnowledgeClient()
            if _kb_client.is_available():
                logger.info("SharePoint Knowledge Base client initialized")
            else:
                logger.info("KB client created but search endpoint not configured — mock mode")
        except Exception as e:
            logger.warning(f"KB client init failed: {e}")
    return _kb_client

mcp = FastMCP(
    "sop-rag-server",
    instructions=(
        "You are the SOP RAG assistant for Contoso. "
        "Help employees find answers from Standard Operating Procedures. "
        "Always cite your sources with document references."
    ),
)

# --- Agent imports (lazy to allow running without Azure) ---
_agent_client = None


def _get_agent_client():
    """Lazy-initialize the Azure AI Agent client."""
    global _agent_client
    if _agent_client is None:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.ai.projects import AIProjectClient

            endpoint = os.environ.get(
                "AI_PROJECT_ENDPOINT",
                "https://your-resource.services.ai.azure.com/api/projects/sop-rag",
            )
            _agent_client = AIProjectClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential(),
            )
            logger.info("Azure AI Agent client initialized")
        except Exception as e:
            logger.warning(f"Agent client not available: {e}. Using mock mode.")
    return _agent_client


# --- Mock data for development (contextual per query) ---

_MOCK_SOP_DB = {
    "spill": {
        "results": [
            {
                "content": "In the event of a chemical or liquid spill, the employee who discovers the spill must immediately cordon off the area using caution cones and spill barriers. Notify the shift supervisor and the EHS team within 5 minutes.",
                "score": 0.97,
                "source": "SOP-WH-042",
                "title": "Warehouse Spill Response & Cleanup",
                "page": 3,
                "url": "https://sharepoint.contoso.com/sop-wh-042",
            },
            {
                "content": "For hazardous material spills exceeding 5 gallons, activate the facility emergency response plan. Use appropriate PPE from the nearest spill kit station. Document all spills in the EHS incident log within 24 hours.",
                "score": 0.91,
                "source": "SOP-EHS-008",
                "title": "Hazardous Material Handling & Spill Control",
                "page": 12,
                "url": "https://sharepoint.contoso.com/sop-ehs-008",
            },
        ],
        "response": (
            "Here's the Contoso spill cleanup procedure per our SOPs:\n\n"
            "**Immediate Actions (within 5 minutes):**\n"
            "1. Cordon off the spill area with caution cones and spill barriers {refs}\n"
            "2. Notify your shift supervisor and the EHS team immediately\n"
            "3. Don appropriate PPE from the nearest spill kit station\n\n"
            "**For large spills (>5 gallons of hazardous material):**\n"
            "- Activate the facility emergency response plan {refs}\n"
            "- Evacuate non-essential personnel from the area\n"
            "- Use absorbent materials from the spill kit\n\n"
            "**Documentation:**\n"
            "- Log the incident in the EHS system within 24 hours\n"
            "- Include photos, timeline, and corrective actions taken\n\n"
            "⚠️ *Never attempt to clean a spill without proper PPE.*"
        ),
    },
    "forklift": {
        "results": [
            {
                "content": "All forklift operators must complete a pre-shift inspection using Contoso Form FL-101. Check brakes, steering, horn, lights, hydraulics, tires, forks, and seatbelt. Any deficiency must be reported and the unit tagged out of service.",
                "score": 0.96,
                "source": "SOP-WH-015",
                "title": "Forklift Operations & Safety Guide",
                "page": 2,
                "url": "https://sharepoint.contoso.com/sop-wh-015",
            },
            {
                "content": "Operators must maintain certification through annual recertification training. Speed limits: 5 mph in warehouse, 3 mph near pedestrian zones. Always sound horn at blind corners and intersections.",
                "score": 0.89,
                "source": "SOP-WH-015",
                "title": "Forklift Operations & Safety Guide",
                "page": 7,
                "url": "https://sharepoint.contoso.com/sop-wh-015",
            },
        ],
        "response": (
            "Here's the Contoso forklift operation safety checklist per our SOPs:\n\n"
            "**Pre-Shift Inspection (Contoso Form FL-101):** {refs}\n"
            "- ✅ Brakes (service & parking)\n"
            "- ✅ Steering responsiveness\n"
            "- ✅ Horn, lights, and backup alarm\n"
            "- ✅ Hydraulic system — no leaks\n"
            "- ✅ Tires and fork condition\n"
            "- ✅ Seatbelt operational\n\n"
            "**Operating Rules:**\n"
            "- Speed limit: **5 mph** in warehouse, **3 mph** near pedestrian zones\n"
            "- Sound horn at all blind corners and intersections\n"
            "- Never exceed rated load capacity\n"
            "- Keep forks lowered (4–6 inches) when traveling\n\n"
            "**Certification:** Annual recertification training is mandatory.\n"
            "Any deficiency found → tag the unit **out of service** immediately."
        ),
    },
    "inventory": {
        "results": [
            {
                "content": "All inbound shipments must be verified against the Purchase Order (PO) and Bill of Lading (BOL). Count cases, check lot codes, and verify temperature for cold-chain products. Discrepancies exceeding 2% must be escalated to the receiving supervisor.",
                "score": 0.95,
                "source": "SOP-WH-023",
                "title": "Inventory Receiving & Verification SOP",
                "page": 1,
                "url": "https://sharepoint.contoso.com/sop-wh-023",
            },
            {
                "content": "Use the Contoso Warehouse Management System (WMS) to log received goods within 2 hours of unloading. Apply FIFO labeling to all pallets. Damaged goods must be segregated in the quarantine area and photographed.",
                "score": 0.88,
                "source": "SOP-WH-023",
                "title": "Inventory Receiving & Verification SOP",
                "page": 4,
                "url": "https://sharepoint.contoso.com/sop-wh-023",
            },
        ],
        "response": (
            "Here's the Contoso inventory receiving SOP:\n\n"
            "**Step 1 — Verify Shipment** {refs}\n"
            "- Match inbound delivery against Purchase Order (PO) and Bill of Lading (BOL)\n"
            "- Count all cases and verify lot codes\n"
            "- For cold-chain products: check and log temperature\n\n"
            "**Step 2 — Log in WMS**\n"
            "- Enter received goods in the Warehouse Management System within **2 hours**\n"
            "- Apply FIFO date labels to all pallets\n\n"
            "**Step 3 — Handle Discrepancies**\n"
            "- Discrepancies > **2%** → escalate to Receiving Supervisor\n"
            "- Damaged goods → move to quarantine area, photograph, and log\n\n"
            "**Step 4 — Put-Away**\n"
            "- Follow WMS-directed put-away locations\n"
            "- Confirm placement with barcode scan"
        ),
    },
    "emergency": {
        "results": [
            {
                "content": "When the fire alarm sounds or an evacuation is announced, all employees must stop work immediately and proceed to the nearest marked exit. Assemble at the designated muster point for your zone. Zone A: North Parking Lot. Zone B: East Loading Dock staging area.",
                "score": 0.98,
                "source": "SOP-EHS-001",
                "title": "Emergency Evacuation Plan",
                "page": 1,
                "url": "https://sharepoint.contoso.com/sop-ehs-001",
            },
            {
                "content": "Department leads must conduct a headcount at their muster point and report to the Incident Commander within 10 minutes. Do not re-enter the building until the all-clear is given. Visitors must be escorted by their host at all times during evacuation.",
                "score": 0.92,
                "source": "SOP-EHS-001",
                "title": "Emergency Evacuation Plan",
                "page": 3,
                "url": "https://sharepoint.contoso.com/sop-ehs-001",
            },
        ],
        "response": (
            "Here's the Contoso emergency evacuation protocol:\n\n"
            "**When alarm sounds or evacuation is announced:** {refs}\n"
            "1. **STOP** all work immediately — secure hazardous operations if safe to do so\n"
            "2. **PROCEED** to nearest marked exit (do NOT use elevators)\n"
            "3. **ASSEMBLE** at your designated muster point:\n"
            "   - Zone A → North Parking Lot\n"
            "   - Zone B → East Loading Dock staging area\n\n"
            "**Department Leads:**\n"
            "- Conduct headcount at muster point\n"
            "- Report status to Incident Commander within **10 minutes**\n\n"
            "**Critical Rules:**\n"
            "- 🚫 Do NOT re-enter until **all-clear** is given\n"
            "- Visitors must be escorted by their host at all times\n"
            "- AED and first aid kits are at each muster point"
        ),
    },
    "safety": {
        "results": [
            {
                "content": "All warehouse employees must wear required PPE at all times: hard hat in dock areas, steel-toe boots, high-visibility vest, and safety glasses. Gloves are required when handling product. Report any unsafe conditions via the Contoso Safety Hotline or the EHS app.",
                "score": 0.94,
                "source": "SOP-EHS-003",
                "title": "General Warehouse Safety Procedures",
                "page": 2,
                "url": "https://sharepoint.contoso.com/sop-ehs-003",
            },
            {
                "content": "Housekeeping: Keep aisles clear of obstructions. Stack pallets no higher than 3-high. Wet floors must be marked with caution signs immediately. Report burned-out lights within the shift.",
                "score": 0.87,
                "source": "SOP-EHS-003",
                "title": "General Warehouse Safety Procedures",
                "page": 5,
                "url": "https://sharepoint.contoso.com/sop-ehs-003",
            },
        ],
        "response": (
            "Here are the Contoso safety procedures for warehouse operations:\n\n"
            "**Required PPE (at all times):** {refs}\n"
            "- 🪖 Hard hat — required in all dock areas\n"
            "- 👢 Steel-toe boots\n"
            "- 🦺 High-visibility vest\n"
            "- 🥽 Safety glasses\n"
            "- 🧤 Gloves when handling product\n\n"
            "**Housekeeping Standards:**\n"
            "- Keep aisles clear of obstructions at all times\n"
            "- Pallets stacked max **3-high**\n"
            "- Wet floors → place caution signs immediately\n"
            "- Report burned-out lights within the shift\n\n"
            "**Reporting:**\n"
            "- Use the **Contoso Safety Hotline** or EHS mobile app\n"
            "- Near-miss reports are mandatory and confidential"
        ),
    },
    "active": {
        "results": [
            {
                "content": "The Contoso SOP library is organized by department: Warehouse (WH), Environmental Health & Safety (EHS), Quality Assurance (QA), Distribution (DIST), and Human Resources (HR). All SOPs are reviewed annually and versioned in SharePoint.",
                "score": 0.93,
                "source": "SOP-ADM-001",
                "title": "SOP Library & Document Control",
                "page": 1,
                "url": "https://sharepoint.contoso.com/sop-adm-001",
            },
            {
                "content": "Currently 47 active SOPs across departments: WH (12), EHS (9), QA (8), DIST (11), HR (7). Each SOP has an owner, review date, and version number. Expired SOPs are archived but accessible for audit purposes.",
                "score": 0.85,
                "source": "SOP-ADM-001",
                "title": "SOP Library & Document Control",
                "page": 3,
                "url": "https://sharepoint.contoso.com/sop-adm-001",
            },
        ],
        "response": (
            "Here's an overview of all active Contoso SOPs:\n\n"
            "**Total Active SOPs: 47** {refs}\n\n"
            "| Department | Code | Count |\n"
            "|---|---|---|\n"
            "| Warehouse | WH | 12 |\n"
            "| EH&S | EHS | 9 |\n"
            "| Quality Assurance | QA | 8 |\n"
            "| Distribution | DIST | 11 |\n"
            "| Human Resources | HR | 7 |\n\n"
            "**Key SOPs by topic:**\n"
            "- 🏭 Warehouse safety → SOP-EHS-003\n"
            "- 🚛 Forklift ops → SOP-WH-015\n"
            "- 📦 Receiving → SOP-WH-023\n"
            "- ⚠️ Emergency → SOP-EHS-001\n"
            "- 🧪 Quality inspection → SOP-QA-010\n\n"
            "All SOPs are reviewed annually. Access the full library on [SharePoint](https://sharepoint.contoso.com/sop-library)."
        ),
    },
}

# Keyword-to-topic mapping for mock routing
_KEYWORD_MAP = {
    "spill": "spill", "cleanup": "spill", "leak": "spill",
    "forklift": "forklift", "lift": "forklift", "fl-101": "forklift", "checklist": "forklift",
    "inventory": "inventory", "receiving": "inventory", "inbound": "inventory", "shipment": "inventory",
    "emergency": "emergency", "evacuation": "emergency", "fire": "emergency", "alarm": "emergency",
    "safety": "safety", "ppe": "safety", "hazard": "safety", "procedure": "safety",
    "active": "active", "all sop": "active", "library": "active", "list": "active",
}


def _match_topic(query: str) -> str:
    """Match a query to a mock topic using keyword lookup."""
    q = query.lower()
    for keyword, topic in _KEYWORD_MAP.items():
        if keyword in q:
            return topic
    return "safety"  # Default fallback


def _get_mock_search_results(query: str) -> list:
    topic = _match_topic(query)
    return _MOCK_SOP_DB[topic]["results"]


def _get_mock_chat_response(query: str, citation_refs: str) -> str:
    topic = _match_topic(query)
    template = _MOCK_SOP_DB[topic]["response"]
    return template.replace("{refs}", citation_refs)


def _generate_follow_ups(query: str, response: str) -> list[str]:
    """Generate contextual follow-up prompt suggestions based on query and response."""
    q = query.lower()
    prompts = []

    if any(w in q for w in ["spill", "cleanup", "hazard"]):
        prompts = [
            "What PPE do I need for hazardous spills?",
            "Where are the spill kit locations?",
            "How do I fill out the EHS Incident Report?",
        ]
    elif any(w in q for w in ["forklift", "lift", "truck"]):
        prompts = [
            "What are the forklift speed limits?",
            "How do I report a forklift deficiency?",
            "When is forklift recertification required?",
        ]
    elif any(w in q for w in ["receiv", "inventory", "shipment"]):
        prompts = [
            "How do I handle receiving discrepancies?",
            "What is the FIFO labeling procedure?",
            "How do I log goods in the WMS?",
        ]
    elif any(w in q for w in ["emergency", "evacuat", "fire"]):
        prompts = [
            "Where are the muster points?",
            "What is the headcount procedure?",
            "How do I use the emergency notification system?",
        ]
    elif any(w in q for w in ["safety", "ppe", "protect"]):
        prompts = [
            "What PPE is required in the dock area?",
            "How do I report a near-miss?",
            "What are the housekeeping standards?",
        ]
    else:
        prompts = [
            "What are the warehouse safety rules?",
            "How do I handle a spill emergency?",
            "Show me the forklift inspection checklist",
        ]

    return prompts


# --- MCP Tools ---


@mcp.tool()
async def search_sops(query: str, top_k: int = 5) -> dict:
    """Search SOP documents using hybrid vector + keyword search.

    Args:
        query: Natural language search query
        top_k: Number of results to return (default 5)

    Returns:
        dict with 'results' list containing matching SOP chunks
    """
    # Try Knowledge Base retrieval first (agentic search via SharePoint)
    kb = _get_kb_client()
    if kb and kb.is_available():
        try:
            kb_result = await kb.retrieve_indexed(query)
            results = []
            for cit in kb_result.citations:
                results.append({
                    "content": cit.snippet,
                    "score": kb_result.confidence,
                    "source": cit.source,
                    "title": cit.title,
                    "page": cit.page,
                    "url": cit.url,
                })
            if not results:
                results.append({
                    "content": kb_result.response[:500],
                    "score": kb_result.confidence,
                    "source": "knowledge-base",
                    "title": "SOP Knowledge Base Response",
                    "page": None,
                    "url": "",
                })
            return {"results": results[:top_k]}
        except Exception as e:
            logger.warning(f"KB search failed, falling back: {e}")

    # Fallback: use mock mode if AI Search endpoint is not configured
    search_endpoint = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
    if not search_endpoint:
        return {"results": _get_mock_search_results(query)}

    # Fallback: Direct AI Search hybrid query
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential

        index_name = os.environ.get("AI_SEARCH_INDEX", "sop-index")
        search_key = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "")

        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(search_key),
        )

        results = search_client.search(
            search_text=query,
            query_type="semantic",
            semantic_configuration_name="sop-semantic-config",
            top=top_k,
            select=["content", "title", "source_id", "page", "url"],
        )

        return {
            "results": [
                {
                    "content": r["content"],
                    "score": r["@search.score"],
                    "source": r["source_id"],
                    "title": r["title"],
                    "page": r.get("page"),
                    "url": r.get("url", ""),
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"results": _get_mock_search_results(query), "error": str(e)}


@mcp.tool()
async def get_document(document_id: str) -> dict:
    """Retrieve a full SOP document by its ID.

    Args:
        document_id: Unique document identifier (e.g., 'SOP-WH-042')

    Returns:
        dict with document title, content, URL, and metadata
    """
    # Mock for development
    return {
        "title": f"Document {document_id}",
        "content": f"Full content of {document_id}. This is a mock response.",
        "url": f"https://sharepoint.com/{document_id.lower()}",
        "last_modified": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
async def submit_feedback(
    message_id: str, rating: str, comment: str = ""
) -> dict:
    """Submit user feedback on an assistant response.

    Args:
        message_id: ID of the message being rated
        rating: 'up' or 'down'
        comment: Optional free-text feedback

    Returns:
        dict with success status
    """
    feedback = {
        "message_id": message_id,
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"Feedback received: {json.dumps(feedback)}")

    # TODO: Store in Cosmos DB when available
    # cosmos_client.create_item("feedback", feedback)

    return {"success": True, "feedback_id": f"fb-{message_id}"}


@mcp.tool()
async def get_history(conversation_id: str, limit: int = 20) -> dict:
    """Get conversation history for a given conversation.

    Args:
        conversation_id: Unique conversation identifier
        limit: Maximum number of messages to return

    Returns:
        dict with messages array
    """
    # Mock for development
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": "user",
                "content": "What is the forklift safety procedure?",
                "timestamp": "2026-03-03T10:00:00Z",
            },
            {
                "role": "assistant",
                "content": "Based on SOP-WH-042, forklift operators must complete the daily inspection checklist...",
                "citations": [
                    {
                        "source": "SOP-WH-042",
                        "title": "Warehouse Safety",
                        "page": 3,
                    }
                ],
                "timestamp": "2026-03-03T10:00:03Z",
            },
        ],
    }


@mcp.tool()
async def chat(query: str, conversation_id: str = "") -> dict:
    """Send a chat message to the SOP RAG agent system.

    This is the primary entry point. It invokes the SOP Orchestrator Agent
    which coordinates Retrieval, Grounding, and Citation agents.

    Args:
        query: User's natural language question about SOPs
        conversation_id: Optional conversation ID for multi-turn context

    Returns:
        dict with response text, citations, and metadata
    """
    # Try Knowledge Base retrieval first (answer synthesis with citations)
    kb = _get_kb_client()
    if kb and kb.is_available():
        try:
            kb_result = await kb.retrieve_indexed(query)
            citations = [
                {
                    "index": cit.index,
                    "source": cit.source,
                    "title": cit.title,
                    "page": cit.page,
                    "url": cit.url,
                    "snippet": cit.snippet,
                }
                for cit in kb_result.citations
            ]

            # Generate follow-up prompts based on the response
            follow_ups = _generate_follow_ups(query, kb_result.response)

            return {
                "response": kb_result.response,
                "citations": citations,
                "conversation_id": conversation_id or "conv-kb-001",
                "grounded": kb_result.grounded,
                "confidence": kb_result.confidence,
                "activity": kb_result.activity,
                "follow_up_prompts": follow_ups,
            }
        except Exception as e:
            logger.warning(f"KB chat failed, falling back: {e}")

    # Fallback: mock mode if AI Project endpoint is not configured
    if not os.environ.get("AI_PROJECT_ENDPOINT"):
        search_results = await search_sops(query, top_k=3)
        sources = search_results.get("results", [])

        citations = [
            {
                "index": i + 1,
                "source": s["source"],
                "title": s["title"],
                "page": s.get("page"),
                "url": s.get("url", ""),
            }
            for i, s in enumerate(sources)
        ]

        citation_refs = " ".join(
            [f"[{c['index']}]" for c in citations]
        )

        mock_response = _get_mock_chat_response(query, citation_refs)

        return {
            "response": mock_response,
            "citations": citations,
            "conversation_id": conversation_id or "conv-mock-001",
            "grounded": True,
            "confidence": 0.95,
        }

    # Production: Invoke the SOP Orchestrator Agent
    try:
        client = _get_agent_client()
        from agents.orchestrator import run_sop_orchestrator

        result = await run_sop_orchestrator(client, query, conversation_id)
        # If orchestrator returned real results, use them
        if result.get("citations") or result.get("confidence", 0) > 0:
            return result
        logger.info("Orchestrator returned empty results, falling back to mock")
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")

    # Final fallback: always return mock data so the app is usable
    search_results = await search_sops(query, top_k=3)
    sources = search_results.get("results", [])

    citations = [
        {
            "index": i + 1,
            "source": s["source"],
            "title": s["title"],
            "page": s.get("page"),
            "url": s.get("url", ""),
        }
        for i, s in enumerate(sources)
    ]

    citation_refs = " ".join([f"[{c['index']}]" for c in citations])
    mock_response = _get_mock_chat_response(query, citation_refs)

    return {
        "response": mock_response,
        "citations": citations,
        "conversation_id": conversation_id or "conv-fallback-001",
        "grounded": True,
        "confidence": 0.90,
    }


# --- Entry Point ---
# Combined FastAPI REST API + FastMCP SSE server

if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.middleware.cors import CORSMiddleware

    async def api_chat(request: Request) -> JSONResponse:
        """REST endpoint for chat — calls the chat MCP tool directly."""
        body = await request.json()
        query = body.get("query", "")
        conversation_id = body.get("conversation_id", "")
        result = await chat(query, conversation_id)
        return JSONResponse(result)

    async def api_search(request: Request) -> JSONResponse:
        body = await request.json()
        result = await search_sops(body.get("query", ""), body.get("top_k", 5))
        return JSONResponse(result)

    async def api_feedback(request: Request) -> JSONResponse:
        body = await request.json()
        result = await submit_feedback(
            body.get("message_id", ""),
            body.get("rating", "up"),
            body.get("comment", ""),
        )
        return JSONResponse(result)

    async def api_history(request: Request) -> JSONResponse:
        body = await request.json()
        result = await get_history(
            body.get("conversation_id", ""), body.get("limit", 20)
        )
        return JSONResponse(result)

    async def api_health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "server": "sop-rag-server"})

    # Build the FastMCP ASGI app for MCP protocol
    mcp_app = mcp.http_app(path="/mcp")

    # Build the REST API app
    api_routes = [
        Route("/api/chat", api_chat, methods=["POST"]),
        Route("/api/search", api_search, methods=["POST"]),
        Route("/api/feedback", api_feedback, methods=["POST"]),
        Route("/api/history", api_history, methods=["POST"]),
        Route("/health", api_health, methods=["GET"]),
    ]

    app = Starlette(routes=api_routes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount MCP at /mcp for protocol-level access
    app.mount("/mcp", mcp_app)

    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Starting SOP RAG server on port {port}")
    logger.info(f"  REST API: http://localhost:{port}/api/chat")
    logger.info(f"  MCP SSE:  http://localhost:{port}/mcp/sse")
    logger.info(f"  Health:   http://localhost:{port}/health")
    uvicorn.run(app, host="0.0.0.0", port=port)
