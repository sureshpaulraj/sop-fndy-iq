# SOP RAG Agentic Application

> AI-powered SOP chatbot for Reyes Coca-Cola Bottling using multi-agent orchestration

## Architecture

```
React Frontend (Contoso themed) → FastMCP Server → SOP Orchestrator Agent
                                                  ├── Retrieval Agent (AI Search)
                                                  ├── Grounding Validator Agent
                                                  └── Citation Formatter Agent
```

## Quick Start

### Backend (FastMCP)
```bash
cd backend
pip install -r requirements.txt
python server.py
```

### Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

## Project Structure
```
sop-rag/
├── frontend/          # React 19.2 + TypeScript + Vite
├── backend/           # FastMCP server (Python 3.12)
├── infra/             # Terraform (Azure resources)
└── tests/             # E2E tests (Playwright)
```

## Tech Stack
- **Frontend**: React 19.2, TypeScript, Vite, MSAL.js
- **Backend**: FastMCP, Python 3.12, azure-ai-agents SDK
- **Agents**: Azure AI Agent Service, Microsoft Agent Framework
- **Search**: Azure AI Search (hybrid vector + keyword)
- **Models**: GPT-4.1 (generation), ada-002 (embeddings)
- **State**: Cosmos DB
- **IaC**: Terraform
