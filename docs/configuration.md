# Configuration

Toan bo cau hinh he thong quan ly qua environment variables, doc boi Pydantic Settings.

## Cach hoat dong

```mermaid
graph LR
    ENV[".env file\n(project root)"]
    SYS["System env vars"]
    DEF["Default values\nin Settings class"]

    PYDANTIC["Pydantic Settings\nbackend/src/config/settings.py"]
    SINGLETON["settings = Settings()\n(singleton)"]

    ENV --> PYDANTIC
    SYS --> PYDANTIC
    DEF --> PYDANTIC
    PYDANTIC --> SINGLETON

    SINGLETON --> Modules["All modules\nimport settings"]
```

**Thu tu uu tien:** System env vars > `.env` file > default values.

**File:** `backend/src/config/settings.py`

**Usage:**
```python
from src.config.settings import settings

print(settings.deepseek_model)       # "deepseek-chat"
print(settings.embedding_dim)        # 1024
print(settings.database_url)         # "postgresql+asyncpg://..."
```

---

## Danh sach bien moi truong

### LLM (DeepSeek primary, OpenAI fallback)

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `DEEPSEEK_API_KEY` | string | `""` | API key cho DeepSeek |
| `DEEPSEEK_BASE_URL` | string | `"https://api.deepseek.com"` | Base URL cho DeepSeek API |
| `DEEPSEEK_MODEL` | string | `"deepseek-chat"` | Model name |
| `OPENAI_API_KEY` | string | `""` | API key cho OpenAI (fallback) |
| `FALLBACK_MODEL` | string | `"gpt-4o-mini"` | Model OpenAI fallback |
| `LLM_TEMPERATURE` | float | `0.05` | Temperature cho generation |

**Luu y:** `LLM_TEMPERATURE` dat thap (0.05) de dam bao output nhat quan cho van ban phap ly. Khong nen tang cao.

### Embedding (Voyage AI)

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `VOYAGE_API_KEY` | string | `""` | API key cho Voyage AI |
| `EMBEDDING_MODEL` | string | `"voyage-3.5-lite"` | Model embedding |
| `EMBEDDING_DIM` | int | `1024` | So chieu vector |

### Vector DB (Qdrant)

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `QDRANT_URL` | string | `"http://localhost:6333"` | Qdrant server URL |
| `QDRANT_API_KEY` | string | `""` | Qdrant API key (optional for local) |
| `QDRANT_COLLECTION` | string | `"legal_chunks"` | Ten collection |

### PostgreSQL

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `DATABASE_URL` | string | `"postgresql+asyncpg://postgres:postgres@localhost:5432/legal_rag"` | PostgreSQL connection URL |

**Luu y:** Dung driver `asyncpg` cho async SQLAlchemy. Credentials phai khop voi `docker-compose.yml`. PostgreSQL luu tru relational data (tenants, users, documents, audit logs), khong luu vectors.

### Auth (JWT)

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `JWT_SECRET_KEY` | string | `"change-me-in-production"` | Secret key cho JWT signing |
| `JWT_ALGORITHM` | string | `"HS256"` | Algorithm JWT |
| `JWT_EXPIRE_MINUTES` | int | `60` | Thoi gian het han token (phut) |

**Luu y:** Auth system chua duoc trien khai trong Phase 1. Cac bien nay duoc chuan bi cho Phase 2 multi-tenancy. **BAT BUOC thay doi `JWT_SECRET_KEY` trong production.**

### Cache & Sessions (Redis)

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `REDIS_URL` | string | `"redis://localhost:6379/0"` | Redis connection URL |

**Luu y:** Redis la optional trong Phase 1. Neu Redis khong kha dung, he thong van hoat dong binh thuong -- chi sessions/cache bi disable.

### LlamaParse (Optional)

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `LLAMA_CLOUD_API_KEY` | string | `""` | API key cho LlamaParse (Phase 1 dung PyMuPDF) |

### Retrieval

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `RETRIEVAL_TOP_K` | int | `20` | So chunks lay tu Qdrant |
| `RERANK_TOP_N` | int | `5` | So chunks sau rerank |
| `RERANKER_MODEL` | string | `"BAAI/bge-reranker-v2-m3"` | Cross-encoder model |

**Luu y:** `RETRIEVAL_TOP_K=20` dam bao recall cao. Reranker loc xuong `RERANK_TOP_N=5` de giu precision. Tang `TOP_K` neu thay thieu ket qua, giam `TOP_N` neu context qua dai.

### Chunking

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `CHUNK_MAX_TOKENS` | int | `1500` | Token toi da cho 1 Dieu truoc khi tach |
| `CHUNK_OVERLAP_TOKENS` | int | `200` | Overlap khi tach unstructured |
| `SENTENCE_CHUNK_SIZE` | int | `1024` | Kich thuoc chunk cho unstructured |

### Ingestion

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `SKIP_ENRICHMENT` | bool | `False` | Bo qua LLM contextual enrichment |
| `ENRICHMENT_CONCURRENCY` | int | `5` | So luong enrichment dong thoi |

### Application

| Bien | Type | Default | Mo ta |
|------|------|---------|-------|
| `APP_ENV` | string | `"development"` | Moi truong (development/staging/production) |
| `LOG_LEVEL` | string | `"INFO"` | Log level (DEBUG/INFO/WARNING/ERROR) |
| `BACKEND_CORS_ORIGINS` | list[string] | `["http://localhost:3000"]` | Allowed CORS origins |
| `STATIC_FALLBACK_MESSAGE` | string | (xem ben duoi) | Thong bao khi khong tim thay ket qua |

Default fallback message:
```
Toi chua tim thay quy dinh cu the ve van de nay. Vui long lien he Phong Hanh chinh - Phap che de duoc ho tro.
```

---

## File `.env.example`

```bash
# === LLM ===
DEEPSEEK_API_KEY=
OPENAI_API_KEY=

# === Embedding ===
VOYAGE_API_KEY=

# === Vector DB ===
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# === PostgreSQL ===
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/legal_rag

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === LlamaParse ===
LLAMA_CLOUD_API_KEY=

# === Auth ===
JWT_SECRET_KEY=change-me-in-production

# === App ===
APP_ENV=development
LOG_LEVEL=INFO
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

**Setup:**
```bash
cp .env.example .env
# Dien API keys vao .env
```

---

## Tham so quan trong theo use case

### Development / Smoke test

```bash
SKIP_ENRICHMENT=true        # Bo qua LLM enrichment, nhanh hon
LOG_LEVEL=DEBUG              # Log chi tiet de debug
RETRIEVAL_TOP_K=10           # Giam de test nhanh
```

### Production

```bash
SKIP_ENRICHMENT=false        # Bat enrichment cho chat luong cao
LOG_LEVEL=WARNING            # Chi log canh bao va loi
APP_ENV=production
LLM_TEMPERATURE=0.05         # Giu thap cho do chinh xac
ENRICHMENT_CONCURRENCY=5     # Gioi han rate limit
JWT_SECRET_KEY=<random-64-char-string>  # BAT BUOC thay doi
BACKEND_CORS_ORIGINS=["https://your-domain.com"]
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/legal_rag
```

### Khi khong co GPU (reranker)

Reranker (`bge-reranker-v2-m3`) can `torch` va ~560MB RAM. Neu khong co GPU hoac thieu RAM, reranker tu dong fallback ve no-op mode (sort by cosine score). Khong can config gi them.
