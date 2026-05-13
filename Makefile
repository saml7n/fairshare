.PHONY: dev dev-server dev-web test test-server test-web docker-up docker-down docker-logs docker-build clean

# Load .env and .env.local if they exist
ifneq (,$(wildcard .env))
  include .env
  export
endif
ifneq (,$(wildcard .env.local))
  include .env.local
  export
endif

# ─── Local development ────────────────────────────────────────────
dev:  ## Start server + web locally
	@echo "Starting server on :3000 and web on :5173..."
	@cd server && uv run uvicorn app.main:app --port 3000 --reload &
	@cd web && npm run dev &
	@wait

dev-server:  ## Start only the backend server
	cd server && uv run uvicorn app.main:app --port 3000 --reload

dev-web:  ## Start only the web frontend
	cd web && npm run dev

# ─── Testing ──────────────────────────────────────────────────────
test:  ## Run all tests (server + web)
	cd server && uv run python -m pytest -x -q
	cd web && npm test -- --run

test-server:  ## Run server tests only
	cd server && uv run python -m pytest -x -q

test-web:  ## Run web tests only
	cd web && npm test -- --run

# ─── Docker deployment ───────────────────────────────────────────
docker-up:  ## Build and start all containers (app + ngrok)
	docker compose --env-file .env.local up -d --build

docker-down:  ## Stop all containers
	docker compose --env-file .env.local down

docker-logs:  ## Tail logs from all containers
	docker compose --env-file .env.local logs -f

docker-build:  ## Rebuild the app image without starting
	docker compose --env-file .env.local build

# ─── Cleanup ──────────────────────────────────────────────────────
clean:  ## Remove database, caches
	rm -f server/fairshare.db
	find server -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ─── Help ─────────────────────────────────────────────────────────
help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
