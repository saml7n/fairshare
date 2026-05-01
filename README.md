# FairShare — Splitwise-style Expense Splitting

Split expenses fairly with friends. Track who paid what, see simplified debts with minimum transactions, and settle up.

See [docs/stories.md](docs/stories.md) for the implementation plan.

---

## Features

- **Groups** — Create expense groups and invite members.
- **Expenses** — Record who paid, split by custom amounts or default percentages.
- **Smart balances** — Graph minimisation algorithm computes the fewest transfers to settle all debts.
- **Settle up** — Record payments and watch balances update in real time.
- **Dashboard** — See your net position across all groups at a glance.

---

## Quickstart (local development)

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+ and npm

### 1. Environment variables

```bash
cp .env.example .env.local
# Set FAIRSHARE_SECRET_KEY to any strong secret string
```

### 2. Server (Python + FastAPI)

```bash
cd server
uv sync                                             # Install deps
uv run uvicorn app.main:app --port 3000 --reload    # Start dev server
```

Check health: `curl http://localhost:3000/health` → `{"status": "ok"}`

### 3. Web UI (React + Vite)

```bash
cd web
npm install      # Install deps
npm run dev      # Start dev server → http://localhost:5173
```

The Vite dev server proxies `/api` requests to `localhost:3000`.

### Running tests

```bash
# Server
cd server && uv run pytest -v

# Web
cd web && npm test

# Both
make test
```

---

## Cloud deployment (Fly.io)

### First-time setup

```bash
./scripts/fly-setup.sh
```

### Subsequent deploys

```bash
make deploy    # or: fly deploy --ha=false
```

---

## Tech stack

- **Server:** Python 3.12, FastAPI, uvicorn, SQLModel, Pydantic, structlog
- **Web:** React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui
- **Database:** SQLite (persistent volume on Fly.io)
- **Auth:** JWT (HS256) + bcrypt passwords
- **Deployment:** Fly.io (nginx + supervisord in single container)

## Project structure

```
fairshare/
├── server/           # Python / FastAPI backend
│   ├── app/          #   Application code
│   │   ├── api/      #     REST endpoints
│   │   ├── db/       #     SQLModel models & session
│   │   └── main.py   #     App entrypoint
│   └── tests/        #   pytest test suite
├── web/              # React / TypeScript frontend
│   └── src/
│       ├── components/  #   UI components (shadcn/ui)
│       ├── lib/         #   API client, auth, types
│       └── pages/       #   Route pages
├── fly/              # Fly.io deployment configs
├── docs/             # Stories, architecture docs
├── Dockerfile.fly    # Multi-stage build for Fly.io
├── fly.toml          # Fly.io app config
└── Makefile          # Dev, test, deploy targets
```
