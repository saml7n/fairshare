.PHONY: dev dev-server dev-web test test-server test-web deploy clean

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

# ─── Cloud deployment ────────────────────────────────────────────
deploy:  ## Deploy to Fly.io
	fly deploy --ha=false

deploy-setup:  ## First-time Fly.io setup
	./scripts/fly-setup.sh

# ─── Cleanup ──────────────────────────────────────────────────────
clean:  ## Remove database, caches
	rm -f server/fairshare.db
	find server -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ─── Help ─────────────────────────────────────────────────────────
help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
