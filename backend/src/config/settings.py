"""Application settings — loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM (DeepSeek primary, OpenAI fallback) ---
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    fallback_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.05

    # --- Embedding (Voyage AI) ---
    voyage_api_key: str = ""
    embedding_model: str = "voyage-3.5-lite"
    embedding_dim: int = 1024

    # --- Vector DB (Qdrant) ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "legal_chunks"

    # --- PostgreSQL ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/legal_rag"

    # --- Cache & Sessions (Redis) ---
    redis_url: str = "redis://localhost:6379/0"

    # --- LlamaParse (optional) ---
    llama_cloud_api_key: str = ""

    # --- Retrieval params ---
    retrieval_top_k: int = 20
    rerank_top_n: int = 5
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # --- Chunking params ---
    chunk_max_tokens: int = 1500
    chunk_overlap_tokens: int = 200
    sentence_chunk_size: int = 1024

    # --- Ingestion ---
    skip_enrichment: bool = False
    enrichment_concurrency: int = 5

    # --- Auth ---
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    backend_cors_origins: list[str] = ["http://localhost:3000"]
    static_fallback_message: str = (
        "Toi chua tim thay quy dinh cu the ve van de nay. "
        "Vui long lien he Phong Hanh chinh - Phap che de duoc ho tro."
    )


settings = Settings()
