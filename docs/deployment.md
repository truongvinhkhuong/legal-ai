# Deployment

Huong dan cai dat, cau hinh, va chay he thong Legal Intelligence Platform.

## Yeu cau he thong

| Thanh phan | Yeu cau toi thieu |
|-----------|-------------------|
| Python | >= 3.11 |
| Node.js | >= 20 |
| Docker | Docker Engine + Docker Compose |
| RAM | 4GB (8GB neu dung reranker) |
| Disk | 2GB (model reranker ~560MB) |

**API keys can thiet:**

| Service | Bat buoc | Muc dich |
|---------|----------|---------|
| DeepSeek | Yes | LLM generation + contextual enrichment |
| Voyage AI | Yes | Text embedding |
| OpenAI | No | LLM fallback (khi DeepSeek loi) |

---

## Cai dat

### 1. Clone va cau hinh

```bash
git clone <repo-url> legal-rag
cd legal-rag

cp .env.example .env
# Dien API keys vao .env
```

### 2. Khoi dong infrastructure

```bash
make infra
# hoac: docker compose up -d
```

```mermaid
graph LR
    subgraph Docker["Docker Compose"]
        PG["PostgreSQL\n:5432"]
        Q["Qdrant\n:6333 (HTTP)\n:6334 (gRPC)"]
        R["Redis\n:6379"]
    end

    Backend["Backend\n(FastAPI :8000)"] --> PG
    Backend --> Q
    Backend --> R
    Frontend["Frontend\n(Next.js :3000)"] --> Backend
```

**Kiem tra:**

```bash
# PostgreSQL
docker exec legal-rag-postgres pg_isready -U postgres
# Expect: accepting connections

# Qdrant dashboard
open http://localhost:6333/dashboard

# Redis
docker exec legal-rag-redis redis-cli ping
# Expect: PONG
```

### 3. Cai dat Backend

```bash
# Tao virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS/Linux

# Cai dependencies
make install-backend
# hoac: cd backend && pip install -e ".[dev]"
```

Dependencies chinh:
- `fastapi`, `uvicorn`, `sse-starlette` -- API server
- `sqlalchemy[asyncio]`, `asyncpg`, `alembic` -- PostgreSQL
- `python-jose`, `passlib` -- Auth (JWT, password hashing)
- `openai` -- LLM client (DeepSeek + OpenAI)
- `voyageai` -- Embedding
- `qdrant-client` -- Vector DB
- `sentence-transformers`, `torch` -- Reranker
- `underthesea` -- Vietnamese NLP
- `pymupdf`, `python-docx`, `beautifulsoup4` -- File parsing
- `redis[hiredis]` -- Cache/sessions

### 4. Cai dat Frontend

```bash
make install-frontend
# hoac: cd frontend && npm install
```

### 5. Chay ung dung

**Cach 1: Dung Makefile (khuyen nghi)**

```bash
# Terminal 1:
make backend    # FastAPI on :8000

# Terminal 2:
make frontend   # Next.js on :3000
```

**Cach 2: Truc tiep**

```bash
# Terminal 1 — Backend
cd backend
uvicorn src.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

**Output backend mong doi:**

```
INFO     Starting Legal RAG service (env=development)
INFO     PostgreSQL connected
INFO     Creating Qdrant collection 'legal_chunks'
INFO     Collection 'legal_chunks' created with all indexes
INFO     Redis connected at redis://localhost:6379/0
INFO     Uvicorn running on http://0.0.0.0:8000
```

**Truy cap:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Qdrant Dashboard: http://localhost:6333/dashboard

---

## Docker Compose

**File:** `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: legal-rag-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: legal_rag
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: legal-rag-qdrant
    ports:
      - "6333:6333"    # HTTP API + Dashboard
      - "6334:6334"    # gRPC
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: legal-rag-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
```

**Luu y port conflicts:**

Neu port da bi chiem, doi port trong `docker-compose.yml` va cap nhat `.env`:

```bash
# Vi du: Redis port 6380
REDIS_URL=redis://localhost:6380/0

# Vi du: PostgreSQL port 5433
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/legal_rag
```

---

## Makefile commands

| Command | Mo ta |
|---------|-------|
| `make help` | Hien thi tat ca commands |
| `make infra` | Start Docker services (PostgreSQL, Qdrant, Redis) |
| `make stop` | Stop Docker services |
| `make install-backend` | Install Python dependencies |
| `make install-frontend` | Install Node dependencies |
| `make install` | Install tat ca (backend + frontend) |
| `make backend` | Start backend dev server (:8000) |
| `make frontend` | Start frontend dev server (:3000) |
| `make migrate` | Run Alembic migrations |

---

## Xac nhan hoat dong

### Health check

```bash
# Simple
curl http://localhost:8000/health
# {"status":"ok"}

# Detailed (bao gom PostgreSQL)
curl http://localhost:8000/api/health
# {"status":"ok","qdrant":"connected","redis":"connected","postgres":"connected"}
```

### Nap van ban mau

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@data/samples/noi-quy-lao-dong.pdf" \
  -F 'metadata={"doc_number":"NQ-HR-2025-001","doc_title":"Noi quy lao dong 2025","doc_type":"noi_quy","effective_date":"2025-01-01"}'
```

**Response mong doi:**

```json
{
  "success": true,
  "doc_id": "...",
  "chunks_created": 47,
  "structure_detected": "legal_standard",
  "articles_found": 35,
  "cross_references_found": 12,
  "warnings": []
}
```

### Truy van thu

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Quy dinh nghi phep nam cua nhan vien chinh thuc?"}'
```

**Ket qua:** SSE stream voi token chunks, ket thuc bang event `done` chua citations.

### Kiem tra Qdrant

```bash
curl http://localhost:6333/collections/legal_chunks
```

Hoac mo Qdrant Dashboard tai `http://localhost:6333/dashboard`.

### Kiem tra Frontend

Mo `http://localhost:3000` trong browser:
- **Chat page** (`/chat`): Nhap cau hoi, nhan tra loi streaming voi citations
- **Documents page** (`/admin/documents`): Upload file, xem danh sach tai lieu

---

## Cau truc thu muc

```
legal-rag/
├── .env                    # API keys (KHONG commit)
├── .env.example            # Template
├── .gitignore
├── Makefile                # Dev commands
├── docker-compose.yml      # PostgreSQL + Qdrant + Redis
│
├── backend/
│   ├── pyproject.toml      # Python deps
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/            # DB migrations
│   ├── scripts/            # Batch ingest, download samples
│   ├── eval/               # Evaluation framework (stubs)
│   └── src/
│       ├── main.py         # FastAPI entry point
│       ├── config/
│       │   ├── settings.py  # Pydantic Settings
│       │   └── database.py  # SQLAlchemy async setup
│       ├── api/
│       │   ├── models.py    # Enums, schemas
│       │   ├── dependencies.py  # Singletons
│       │   └── routes/      # chat, ingest, health, admin
│       ├── core/
│       │   ├── rag_engine.py    # Orchestrator
│       │   └── redis_client.py  # Redis wrapper
│       ├── db/models/       # SQLAlchemy models
│       ├── ingestion/       # 8 pipeline modules
│       ├── retrieval/       # Qdrant retriever
│       └── reranker/        # Cross-encoder
│
├── frontend/
│   ├── package.json        # Next.js 15 deps
│   ├── Dockerfile
│   ├── next.config.ts      # API proxy
│   └── src/
│       ├── app/            # Pages (chat, admin)
│       ├── components/     # Chat UI, citations, upload
│       ├── hooks/          # useChat SSE hook
│       └── lib/            # API client, types
│
├── data/
│   └── samples/            # Van ban mau de test
│
└── docs/                   # Tai lieu ky thuat
```

---

## Startup Sequence

```mermaid
sequenceDiagram
    participant U as Uvicorn
    participant A as FastAPI Lifespan
    participant PG as PostgreSQL
    participant Q as Qdrant
    participant R as Redis

    U->>A: Start app

    A->>PG: init_db() — create tables
    alt PostgreSQL khong kha dung
        A->>A: Log warning, admin features disabled
    end

    A->>Q: ensure_collection()
    alt Collection khong ton tai
        Q-->>A: Create collection + indexes
    else Collection da co
        Q-->>A: Skip
    end
    alt Qdrant khong kha dung
        A->>A: Log warning, retry on first request
    end

    A->>R: redis_client.connect()
    alt Redis khong kha dung
        A->>A: Log warning, continue without Redis
    end

    A-->>U: Ready to serve

    Note over U: Shutdown signal
    A->>PG: close_db()
    A->>R: redis_client.close()
    A->>Q: close_qdrant_client()
```

**Graceful degradation:**

| Service | Khong kha dung | He thong van hoat dong? |
|---------|---------------|----------------------|
| PostgreSQL | Startup warning, admin features disabled | Co (ingestion + query hoat dong binh thuong) |
| Qdrant | Startup warning, retry on first request | Khong (can cho ingestion + query) |
| Redis | Startup warning, disable sessions/cache | Co (Phase 1 khong bat buoc Redis) |
| DeepSeek | Fallback sang OpenAI | Co (neu co OpenAI key) |
| OpenAI | Static fallback message | Co (giam chat luong) |
| Reranker model | No-op fallback (sort by cosine) | Co (giam do chinh xac) |

---

## Troubleshooting

### PostgreSQL connection refused

```
PostgreSQL unavailable — admin features disabled
```

Kiem tra Docker container:

```bash
docker ps | grep postgres
docker logs legal-rag-postgres
```

Dam bao `DATABASE_URL` trong `.env` dung voi port va credentials trong `docker-compose.yml`.

### Qdrant connection refused

```
Could not connect to Qdrant — will retry on first request
```

Kiem tra Docker container:

```bash
docker ps | grep qdrant
docker logs legal-rag-qdrant
```

### Redis unavailable

```
Redis unavailable — sessions/cache disabled
```

Binh thuong trong Phase 1. Neu can Redis:

```bash
docker ps | grep redis
docker logs legal-rag-redis
```

### Frontend API proxy loi

Neu frontend khong ket noi duoc backend, kiem tra:

1. Backend dang chay tren port 8000
2. `next.config.ts` co proxy rule `/api/:path*` -> `http://localhost:8000/api/:path*`
3. Khoi dong lai frontend sau khi sua `next.config.ts`

### Reranker model download cham

Lan dau chay, reranker tai model ~560MB. Neu timeout, reranker tu dong fallback ve no-op mode.

### underthesea import error

```bash
pip install underthesea
# Neu loi tren Python 3.13:
pip install underthesea --no-deps
pip install scikit-learn regex
```
