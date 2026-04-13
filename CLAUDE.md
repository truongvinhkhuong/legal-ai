# CLAUDE.md

Instructions for Claude Code when working on this project.

## Project Overview

Legal Intelligence Platform — a RAG-based legal assistant for Vietnamese SMEs. Monorepo with `backend/` (Python FastAPI) and `frontend/` (Next.js 15).

## Common Commands

```bash
# Infrastructure (PostgreSQL, Qdrant, Redis)
make infra
make stop

# Backend (port 8000)
make backend
# Or: cd backend && uvicorn src.main:app --reload --port 8000

# Frontend (port 3000)
make frontend
# Or: cd frontend && npm run dev

# Install all dependencies
make install

# Database migrations
make migrate

# Frontend build check
cd frontend && npx next build

# Quick Python syntax check
python3 -c "import ast; ast.parse(open('path/to/file.py').read())"
```

## Project Structure

```
backend/
  src/
    api/           # FastAPI routes (chat, contracts, ingest, admin)
    api/models.py  # Pydantic models — single source of truth for request/response schemas
    config/        # Settings (.env), database connection
    core/          # RAG engine, query decomposer, action plan synthesizer
    contracts/     # Template engine (Jinja2), compliance rules, form schemas, export
    contracts/templates/  # 7 Jinja2 contract template files
    db/models/     # SQLAlchemy models (base, tenant, user, document, contract)
    ingestion/     # Document processing pipeline (9 stages)
    retrieval/     # Qdrant vector search + BM25 hybrid
    reranker/      # Cross-encoder reranking
  main.py          # FastAPI app entry point

frontend/
  src/
    app/           # Next.js App Router pages
    components/    # React components (chat, contracts, layout, admin)
    hooks/         # Custom hooks (use-chat, use-contract-form)
    lib/           # Types (types.ts), API client (api-client.ts)
```

## Code Conventions

### Backend (Python)

- Python >= 3.11, use full type hints
- Pydantic v2 for models (BaseModel, Field)
- SQLAlchemy 2.0 async (Mapped, mapped_column)
- Absolute imports from `src.` (e.g., `from src.api.models import ...`)
- Compliance engine uses pure Python only — NEVER use LLM for calculations
- Template variables must match field_key values in form_schemas.py
- Linter: ruff (line-length=100)
- Tests: pytest + pytest-asyncio

### Frontend (TypeScript/React)

- Next.js 15 App Router, React 19
- Tailwind CSS 3, no CSS modules
- Brand color: brand-500 = #016494 (teal). Use brand-50 through brand-900 defined in tailwind.config.ts
- NO emojis in the UI. Status badges use text labels: "Dat" / "Khong dat" / "Canh bao"
- Minimize scrolling: pin action bars, use collapsible sections, keep critical info visible
- Mobile-first responsive design using Tailwind breakpoints (md:, lg:)
- API client lives in `src/lib/api-client.ts`, types in `src/lib/types.ts`
- Frontend types mirror backend Pydantic models

### General

- Domain-specific variable names and comments use Vietnamese without diacritics (e.g., `luong_toi_thieu`, not `lương_tối_thiểu`)
- UI labels are in Vietnamese without diacritics
- Commit messages in English
- Do not create documentation files unless explicitly requested

## Contract Templates

7 templates in `backend/src/contracts/templates/`:
- `hdld_xdth` / `hdld_kxdth` — Labor contracts (fixed-term / indefinite)
- `hd_thu_viec` — Probation contract
- `hd_thue_mat_bang` — Premises lease agreement
- `hd_dich_vu` — Service agreement
- `qd_cham_dut_hdld` — Labor contract termination decision
- `bien_ban_vi_pham` — Disciplinary violation report

To add a new template: create the .jinja2 file, add form schema in form_schemas.py, add key to TEMPLATE_METADATA, add checker route in compliance_rules.py, add enum value to ContractTemplateKey in models.py.

## Compliance Rules

Legal constants (minimum wages, social insurance rates, probation limits) are in `backend/src/contracts/compliance_rules.py`. Updated when laws change via code review — NEVER stored in the database.

## LLM / AI Pipeline

- Primary LLM: DeepSeek (deepseek-chat)
- Fallback LLM: OpenAI (gpt-4o-mini)
- Embeddings: Voyage AI (voyage-3.5-lite, 1024 dimensions)
- Reranker: BAAI/bge-reranker-v2-m3 (local cross-encoder)
- Query decomposition: LLM classifies simple vs complex queries, splits into sub-questions
- Action plan synthesis: LLM merges multi-source context, streams via SSE

## Database

- PostgreSQL 16: users, tenants, documents, contracts, contract_templates
- Qdrant: vector storage for document chunks
- Redis: cache & sessions
- Alembic for migrations (`cd backend && alembic upgrade head`)
