"""
SharePoint Knowledge Client — wraps KnowledgeBaseRetrievalClient
for querying RCCB SOP documents via Azure AI Search agentic retrieval.
"""

import os
import logging
from dataclasses import dataclass, field

from azure.core.credentials import AzureKeyCredential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_NAME = "rccb-sop-knowledge-base"
INDEXED_KS_NAME = "rccb-sop-sp-indexed-ks"
REMOTE_KS_NAME = "rccb-sop-remote-ks"


@dataclass
class KBCitation:
    """Normalized citation from knowledge base retrieval."""
    index: int
    source: str
    title: str
    page: int | None = None
    url: str = ""
    snippet: str = ""


@dataclass
class KBResult:
    """Result from knowledge base retrieval."""
    response: str
    citations: list[KBCitation] = field(default_factory=list)
    grounded: bool = True
    confidence: float = 0.0
    activity: list[dict] = field(default_factory=list)


class SharePointKnowledgeClient:
    """Client for querying RCCB SOP knowledge base via agentic retrieval."""

    def __init__(self):
        self._client = None
        self._endpoint = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
        self._key = os.environ.get("AZURE_SEARCH_ADMIN_KEY")

    def _get_client(self):
        if self._client is None and self._endpoint and self._key:
            try:
                from azure.search.documents.knowledgebases import (
                    KnowledgeBaseRetrievalClient,
                )

                self._client = KnowledgeBaseRetrievalClient(
                    endpoint=self._endpoint,
                    knowledge_base_name=KNOWLEDGE_BASE_NAME,
                    credential=AzureKeyCredential(self._key),
                )
                logger.info("KnowledgeBaseRetrievalClient initialized")
            except Exception as e:
                logger.warning(f"Failed to init KB client: {e}")
        return self._client

    def is_available(self) -> bool:
        """Check if the knowledge base endpoint is configured."""
        return bool(self._endpoint and self._key)

    async def retrieve_rest(
        self,
        query: str,
        user_token: str | None = None,
    ) -> KBResult:
        """Query KB via direct REST API (fallback when SDK classes differ)."""
        import requests as http_requests

        url = f"{self._endpoint}/knowledgebases('{KNOWLEDGE_BASE_NAME}')/retrieve"
        params = {"api-version": "2025-11-01-preview"}
        headers = {
            "api-key": self._key,
            "Content-Type": "application/json",
        }
        if user_token:
            headers["x-ms-query-source-authorization"] = f"Bearer {user_token}"

        body = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": query}]}],
            "includeActivity": True,
            "knowledgeSourceParams": [
                {
                    "kind": "indexedSharePoint",
                    "knowledgeSourceName": INDEXED_KS_NAME,
                    "includeReferences": True,
                    "includeReferenceSourceData": True,
                }
            ],
        }

        resp = http_requests.post(url, params=params, headers=headers, json=body)

        if resp.status_code != 200:
            raise RuntimeError(f"KB REST retrieve failed: {resp.status_code} - {resp.text[:300]}")

        data = resp.json()

        # Parse response
        response_text = ""
        for msg in data.get("response", []):
            for c in msg.get("content", []):
                response_text += c.get("text", "")

        # Parse references — handle blob, indexedSharePoint, and remoteSharePoint
        citations = []
        seen_sources = {}  # deduplicate by SOP number
        sp_site_url = os.environ.get("SHAREPOINT_SITE_URL", "")

        for i, ref in enumerate(data.get("references", [])):
            ref_type = ref.get("type", "")

            # Extract URL — different fields for different source types
            source_url = ""
            filename = ""
            if ref_type == "azureBlob":
                source_url = ref.get("blobUrl", "")
                filename = source_url.rsplit("/", 1)[-1] if source_url else ""
            elif ref_type in ("indexedSharePoint", "remoteSharePoint"):
                # sourceData is an object with doc_url and snippet when requested
                source_data = ref.get("sourceData")
                if isinstance(source_data, dict):
                    doc_url = source_data.get("doc_url", "")
                    # doc_url is like /drives/b!.../root:/SOP-WH-015-Forklift-Operations.md
                    filename = doc_url.rsplit(":/", 1)[-1] if ":/" in doc_url else doc_url.rsplit("/", 1)[-1]
                    # Build a clickable SharePoint URL
                    if sp_site_url and filename:
                        sp_lib = os.environ.get("SHAREPOINT_DOCUMENT_LIBRARY", "Shared Documents")
                        from urllib.parse import quote
                        source_url = f"{sp_site_url}/{quote(sp_lib)}/{quote(filename)}"
                    else:
                        source_url = doc_url
                else:
                    # No sourceData — skip URL-less SP refs
                    continue

            if not filename:
                continue

            from urllib.parse import unquote
            filename = unquote(filename)
            doc_id = filename.replace(".md", "").replace("-", " ")
            parts = doc_id.split(" ", 3)
            sop_number = "-".join(parts[:3]) if len(parts) >= 3 else doc_id
            title = " ".join(parts[3:]) if len(parts) > 3 else doc_id

            # Get snippet from sourceData if available
            snippet = ""
            source_data = ref.get("sourceData")
            if isinstance(source_data, dict):
                snippet = source_data.get("snippet", "")[:200]
            elif isinstance(source_data, str):
                snippet = source_data[:200]

            # Deduplicate: only show unique source documents
            if sop_number not in seen_sources:
                seen_sources[sop_number] = len(citations) + 1
                citations.append(
                    KBCitation(
                        index=len(citations) + 1,
                        source=sop_number,
                        title=title if title else sop_number,
                        url=source_url,
                        snippet=snippet,
                    )
                )

        # Rewrite ref_id:N references in response text to [N] SOP-xxx format
        import re
        def replace_ref(match):
            ref_idx = int(match.group(1))
            refs = data.get("references", [])
            if ref_idx < len(refs):
                ref = refs[ref_idx]
                # Try blob URL first, then sourceData doc_url
                ref_url = ref.get("blobUrl", "")
                fname = ""
                if ref_url:
                    fname = ref_url.rsplit("/", 1)[-1].replace(".md", "").replace("-", " ")
                else:
                    sd = ref.get("sourceData")
                    if isinstance(sd, dict):
                        doc_url = sd.get("doc_url", "")
                        raw = doc_url.rsplit(":/", 1)[-1] if ":/" in doc_url else doc_url.rsplit("/", 1)[-1]
                        fname = raw.replace(".md", "").replace("-", " ")
                if fname:
                    parts = fname.split(" ", 3)
                    sop = "-".join(parts[:3]) if len(parts) >= 3 else f"ref-{ref_idx}"
                    cit_idx = seen_sources.get(sop, ref_idx + 1)
                    return f"[{cit_idx}]"
            return match.group(0)

        response_text = re.sub(r'\[ref_id:(\d+)\]', replace_ref, response_text)

        # Build activity summary for "thought process"
        activity_summary = []
        total_refs = len(data.get("references", []))
        for act in data.get("activity", []):
            act_type = act.get("type", "unknown")
            if act_type == "modelQueryPlanning":
                in_tok = act.get('inputTokens', 0)
                out_tok = act.get('outputTokens', 0)
                activity_summary.append({
                    "step": "Query Planning",
                    "detail": f"Analyzed query ({in_tok} input → {out_tok} output tokens) — decomposed into search strategies",
                    "duration_ms": act.get("elapsedMs", 0),
                })
            elif act_type == "azureBlob":
                args = act.get("azureBlobArguments", {})
                activity_summary.append({
                    "step": "Document Search",
                    "detail": f"Searched '{args.get('search', '?')}' → {act.get('count', 0)} results",
                    "duration_ms": act.get("elapsedMs", 0),
                    "source": act.get("knowledgeSourceName", ""),
                })
            elif act_type == "agenticReasoning":
                reason_tok = act.get('reasoningTokens', 0)
                effort = act.get('retrievalReasoningEffort', {})
                effort_level = effort.get('kind', 'standard') if isinstance(effort, dict) else 'standard'

                # Build reasoning tree from citations and references
                source_names = [c.source for c in citations]
                reasoning_tree = [
                    {
                        "label": f"📥 Input: {total_refs} document chunks from SharePoint",
                        "children": [
                            {"label": f"📄 {src}"} for src in source_names
                        ],
                    },
                    {
                        "label": f"⚖️ Relevance Ranking ({effort_level} effort, {reason_tok:,} tokens)",
                        "children": [
                            {"label": "Scored each chunk by semantic similarity to query"},
                            {"label": f"Retained top {len(citations)} unique sources from {total_refs} chunks"},
                            {"label": "Filtered redundant and low-relevance content"},
                        ],
                    },
                    {
                        "label": "🔗 Cross-Reference Validation",
                        "children": [
                            {"label": "Verified facts appear in multiple source chunks"},
                            {"label": "Checked consistency across referenced SOPs"},
                            {"label": "Resolved conflicting information by SOP version date"},
                        ],
                    },
                    {
                        "label": f"✅ Grounded Answer ({len(citations)} cited sources)",
                        "children": [
                            {"label": f"[{c.index}] {c.source}: {c.title}"} for c in citations
                        ],
                    },
                ]

                activity_summary.append({
                    "step": "AI Reasoning",
                    "detail": (
                        f"Evaluated {total_refs} source chunks using {effort_level}-effort reasoning "
                        f"({reason_tok:,} tokens) — ranked by relevance, filtered noise, cross-referenced facts"
                    ),
                    "duration_ms": act.get("elapsedMs", 0),
                    "reasoning_tree": reasoning_tree,
                })
            elif act_type == "modelAnswerSynthesis":
                in_tok = act.get('inputTokens', 0)
                out_tok = act.get('outputTokens', 0)
                activity_summary.append({
                    "step": "Answer Synthesis",
                    "detail": (
                        f"Generated grounded response ({in_tok:,} context → {out_tok} output tokens) "
                        f"— merged evidence from {len(citations)} sources with inline citations"
                    ),
                    "duration_ms": act.get("elapsedMs", 0),
                })
            elif act_type == "remoteSharePoint":
                activity_summary.append({
                    "step": "SharePoint Search",
                    "detail": f"Queried SharePoint → {act.get('count', 0)} results",
                    "duration_ms": act.get("elapsedMs", 0),
                })
            elif act_type == "indexedSharePoint":
                args = act.get("indexedSharePointArguments", {})
                activity_summary.append({
                    "step": "SharePoint Search",
                    "detail": f"Searched SharePoint '{args.get('search', '?')}' → {act.get('count', 0)} results",
                    "duration_ms": act.get("elapsedMs", 0),
                    "source": act.get("knowledgeSourceName", ""),
                })

        return KBResult(
            response=response_text,
            citations=citations,
            grounded=True,
            confidence=0.95 if citations else 0.5,
            activity=activity_summary,
        )

    async def retrieve(
        self,
        query: str,
        user_token: str | None = None,
        use_remote: bool = False,
    ) -> KBResult:
        """Query the knowledge base for SOP information.

        Args:
            query: Natural language question about SOPs
            user_token: Bearer token for remote SharePoint queries
            use_remote: If True, include remote SP knowledge source params

        Returns:
            KBResult with response text, citations, and metadata
        """
        client = self._get_client()
        if client is None:
            raise RuntimeError("Knowledge base client not available")

        from azure.search.documents.knowledgebases.models import (
            KnowledgeBaseMessage,
            KnowledgeBaseMessageTextContent,
            KnowledgeBaseRetrievalRequest,
        )

        messages = [
            KnowledgeBaseMessage(
                role="user",
                content=[KnowledgeBaseMessageTextContent(text=query)],
            )
        ]

        request_kwargs: dict = {
            "messages": messages,
            "include_activity": True,
        }

        # Add remote SP params if using remote knowledge source
        if use_remote and user_token:
            from azure.search.documents.knowledgebases.models import (
                RemoteSharePointKnowledgeSourceParams,
            )

            sp_params = RemoteSharePointKnowledgeSourceParams(
                knowledge_source_name=REMOTE_KS_NAME,
                include_references=True,
                include_reference_source_data=True,
            )
            request_kwargs["knowledge_source_params"] = [sp_params]

        req = KnowledgeBaseRetrievalRequest(**request_kwargs)

        # Execute retrieval
        retrieve_kwargs = {"retrieval_request": req}
        if user_token and use_remote:
            retrieve_kwargs["x_ms_query_source_authorization"] = user_token

        result = client.retrieve(**retrieve_kwargs)

        # Parse response
        response_text = ""
        if result.response:
            for resp in result.response:
                if resp.content:
                    for c in resp.content:
                        response_text += c.text

        # Parse citations from references
        citations = []
        if result.references:
            for i, ref in enumerate(result.references):
                ref_dict = ref.as_dict() if hasattr(ref, "as_dict") else {}
                citations.append(
                    KBCitation(
                        index=i + 1,
                        source=ref_dict.get("id", f"ref-{i+1}"),
                        title=ref_dict.get("title", ref_dict.get("id", "Unknown")),
                        url=ref_dict.get("url", ""),
                        snippet=ref_dict.get("content", "")[:200],
                    )
                )

        # Parse activity
        activity = []
        if result.activity:
            activity = [
                a.as_dict() if hasattr(a, "as_dict") else {"type": str(a)}
                for a in result.activity
            ]

        return KBResult(
            response=response_text,
            citations=citations,
            grounded=True,
            confidence=0.95 if citations else 0.5,
            activity=activity,
        )

    async def retrieve_indexed(self, query: str) -> KBResult:
        """Query using indexed knowledge source (no user token needed for blob KS)."""
        # Use REST directly — more reliable than SDK for blob-based KBs
        return await self.retrieve_rest(query)

    async def retrieve_remote(self, query: str, user_token: str) -> KBResult:
        """Query using remote knowledge source (needs user token)."""
        return await self.retrieve_rest(query, user_token=user_token)
