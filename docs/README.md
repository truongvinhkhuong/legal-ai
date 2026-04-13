# Legal Intelligence Platform -- Documentation

Tai lieu ky thuat cho he thong RAG phap ly tieng Viet. Project duoc to chuc theo monorepo voi `backend/` (Python FastAPI) va `frontend/` (Next.js 15).

## Muc luc

| Tai lieu | Mo ta |
|----------|-------|
| [Kien truc he thong](./architecture.md) | Tong quan kien truc monorepo, data flow giua cac module |
| [Ingestion Pipeline](./ingestion-pipeline.md) | Quy trinh nap van ban: parse, phan tich cau truc, chunking, embedding |
| [Query Pipeline](./query-pipeline.md) | Quy trinh truy van: retrieval, rerank, LLM generation, citation |
| [API Reference](./api-reference.md) | Dac ta cac endpoint HTTP, SSE, va Admin API |
| [Data Models](./data-models.md) | Pydantic models, SQLAlchemy models, enums, Qdrant payload schema |
| [Configuration](./configuration.md) | Bien moi truong, tham so cau hinh, settings |
| [Deployment](./deployment.md) | Docker Compose, setup backend + frontend, Makefile |
| [Dataset Integration](./dataset-integration.md) | Tich hop dataset `vietnamese-legal-documents` tu HuggingFace |
| [SaaS Roadmap](./saas-roadmap.md) | Lo trinh phat trien SaaS multi-tenant |
| [AI Features](./ai-features.md) | 7 tinh nang AI nang cao de xuat |
| [SME Feature Analysis](./sme-feature-analysis.md) | Phan tich tinh nang cho SME & ho kinh doanh: multi-agent drafting, neuro-symbolic compliance, agentic search |

## Trang thai trien khai

**Phase 1 -- Core Pipeline + Foundation Refactor** da hoan thanh:

- Monorepo: `backend/` (FastAPI + SQLAlchemy) va `frontend/` (Next.js 15 + React 19)
- PostgreSQL: models Tenant, User, Document, DocumentRelationship, AuditLog
- Admin API: CRUD documents, relationships
- Nap van ban PDF / DOCX / HTML / plain text
- Phan tich cau truc phap ly (Chuong / Muc / Dieu / Khoan / Diem)
- Chunk theo cau truc voi quan he parent-child
- Embedding (Voyage AI) va luu tru vector (Qdrant)
- Truy van bang ngon ngu tu nhien voi streaming SSE
- Tra loi co trich dan Dieu/Khoan cu the
- Phan quyen tai lieu (ACL) o tang Qdrant filter
- Frontend: Chat UI voi SSE streaming, Citation cards, Document management

**Chua trien khai** (Phase 2+): Auth system (JWT), multi-tenancy, BM25 hybrid search, citation engine nang cao, contradiction detector, multi-turn query rewriter, semantic cache, FAQ filter, contract drafting.
