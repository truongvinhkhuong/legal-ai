# Legal Intelligence Platform

AI-powered legal assistant for Vietnamese SMEs and household businesses. Built on RAG (Retrieval-Augmented Generation) for legal document Q&A, automated contract drafting, and compliance checking against Vietnamese labor and civil law.

## Architecture

```
frontend/          Next.js 15 + React 19 + Tailwind CSS
backend/           FastAPI + SQLAlchemy 2.0 (async)
docker-compose.yml PostgreSQL 16, Qdrant, Redis
docs/              Architecture & API documentation
```

### Backend Modules

| Module | Purpose |
|--------|---------|
| `src/api/` | FastAPI routes: chat, contracts, ingest, admin |
| `src/core/` | RAG engine, query decomposer, action plan synthesizer |
| `src/ingestion/` | Document processing pipeline (9 stages) |
| `src/retrieval/` | Hybrid vector search (Qdrant) + BM25 |
| `src/reranker/` | Cross-encoder reranking (bge-reranker-v2-m3) |
| `src/contracts/` | Template engine (Jinja2), compliance rules, DOCX/PDF export |
| `src/db/` | SQLAlchemy models, Alembic migrations |
| `src/config/` | Settings, database connection |

### Frontend Pages

| Route | Purpose |
|-------|---------|
| `/chat` | Legal Q&A chat with precise citations |
| `/contracts` | Contract template selection & user's contracts list |
| `/contracts/new/[templateKey]` | Multi-step form wizard for contract drafting |
| `/contracts/[contractId]` | Contract preview & download (PDF/DOCX) |
| `/admin/documents` | Legal document management |

## Prerequisites

- Python >= 3.11
- Node.js >= 18
- Docker & Docker Compose

## Setup

```bash
# 1. Clone the repo
git clone <repo-url> && cd legal-rag

# 2. Start infrastructure (PostgreSQL, Qdrant, Redis)
make infra

# 3. Install dependencies
make install
# Or individually:
#   make install-backend
#   make install-frontend

# 4. Configure environment
cp backend/.env.example backend/.env
# Edit API keys: DEEPSEEK_API_KEY, VOYAGE_API_KEY, OPENAI_API_KEY (fallback)
```

## Environment Variables (backend/.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key (primary LLM) | — |
| `OPENAI_API_KEY` | OpenAI API key (fallback LLM) | — |
| `VOYAGE_API_KEY` | Voyage AI API key (embeddings) | — |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/legal_rag` |
| `QDRANT_URL` | Qdrant vector DB URL | `http://localhost:6333` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `LLAMA_CLOUD_API_KEY` | LlamaParse key (optional, for complex PDFs) | — |
| `APP_ENV` | `development` / `production` | `development` |

## Running the Application

```bash
# Terminal 1: Infrastructure
make infra

# Terminal 2: Backend (port 8000)
make backend

# Terminal 3: Frontend (port 3000)
make frontend
```

App: http://localhost:3000

API docs (Swagger): http://localhost:8000/docs

## Make Commands

| Command | Description |
|---------|-------------|
| `make infra` | Start PostgreSQL, Qdrant, Redis via Docker |
| `make stop` | Stop all Docker services |
| `make backend` | Start backend dev server (port 8000) |
| `make frontend` | Start frontend dev server (port 3000) |
| `make install` | Install all dependencies |
| `make install-backend` | Install Python dependencies |
| `make install-frontend` | Install Node dependencies |
| `make migrate` | Run Alembic database migrations |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/stream` | Legal Q&A with SSE streaming |
| POST | `/api/ingest` | Upload & process legal documents |
| GET | `/api/contracts/templates` | List 7 available contract templates |
| GET | `/api/contracts/templates/{key}` | Template detail with form schema |
| POST | `/api/contracts/validate` | Real-time compliance validation |
| POST | `/api/contracts/` | Create a new contract |
| GET | `/api/contracts/{id}` | Get contract detail |
| GET | `/api/contracts/{id}/export?format=pdf` | Export contract as PDF or DOCX |
| GET | `/api/admin/documents` | List ingested documents |
| GET | `/api/health` | Health check |

## Contract Templates

| Key | Name | Category |
|-----|------|----------|
| `hdld_xdth` | Fixed-term labor contract | Labor |
| `hdld_kxdth` | Indefinite-term labor contract | Labor |
| `hd_thu_viec` | Probation contract | Labor |
| `hd_thue_mat_bang` | Premises lease agreement | Lease |
| `hd_dich_vu` | Service agreement | Service |
| `qd_cham_dut_hdld` | Labor contract termination decision | Labor |
| `bien_ban_vi_pham` | Disciplinary violation report | Labor |

## Compliance Engine

Automated contract compliance checking against current Vietnamese law:

- Regional minimum wage (Decree 74/2024/ND-CP)
- Maximum probation period (Labor Code 2019, Article 25)
- Probation salary >= 85% of official salary (Labor Code 2019, Article 26)
- Maximum 48 working hours/week (Labor Code 2019, Article 105)
- 10 mandatory fields in labor contracts (Labor Code 2019, Article 21)
- Lease deposit reasonability (market practice)

All calculations are pure deterministic Python — the LLM is never used for compliance math.

## Tech Stack

**Backend:** FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, Jinja2, python-docx, WeasyPrint

**Frontend:** Next.js 15 (App Router), React 19, Tailwind CSS 3, react-markdown, PWA

**AI/ML:** DeepSeek (primary LLM), OpenAI (fallback), Voyage AI (embeddings), bge-reranker-v2-m3 (reranker)

**Infrastructure:** PostgreSQL 16, Qdrant (vector DB), Redis (cache/sessions)

**NLP:** underthesea (Vietnamese word segmentation)
