.PHONY: help install dev backend frontend infra stop migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Infrastructure ---
infra: ## Start PostgreSQL, Qdrant, Redis via Docker
	docker compose up -d

stop: ## Stop all Docker services
	docker compose down

# --- Backend ---
install-backend: ## Install backend Python dependencies
	cd backend && pip install -e ".[dev]"

backend: ## Start backend dev server (port 8000)
	cd backend && uvicorn src.main:app --reload --port 8000

migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

# --- Frontend ---
install-frontend: ## Install frontend Node dependencies
	cd frontend && npm install

frontend: ## Start frontend dev server (port 3000)
	cd frontend && npm run dev

# --- All-in-one ---
install: install-backend install-frontend ## Install all dependencies

dev: ## Start both backend and frontend (requires tmux or run in separate terminals)
	@echo "Run in separate terminals:"
	@echo "  make infra     # Docker services"
	@echo "  make backend   # FastAPI on :8000"
	@echo "  make frontend  # Next.js on :3000"
