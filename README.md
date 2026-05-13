# FairShare — Splitwise-style Expense Splitting

Split expenses fairly with friends. Track who paid what, see simplified debts with minimum transactions, and settle up.

---

## Features

- **Groups** — Create expense groups and invite members by email.
- **Expenses** — Record who paid, split by custom amounts or default percentages.
- **Smart balances** — Graph minimisation algorithm computes the fewest transfers to settle all debts.
- **Settle up** — Record payments and watch balances update instantly.
- **Dashboard** — See your net position across all groups at a glance.
- **Invite-only registration** — Share a secret invite code with friends; the endpoint is rate-limited.

---

## Quickstart (local development)

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 18+ and npm

### 1. Environment

```bash
cp .env.example .env.local
# Edit .env.local — at minimum set FAIRSHARE_SECRET_KEY
```

### 2. Backend

```bash
cd server
uv sync
uv run uvicorn app.main:app --port 3000 --reload
```

Health check: `curl http://localhost:3000/health` → `{"status": "ok"}`

### 3. Frontend

```bash
cd web
npm install
npm run dev      # → http://localhost:5173
```

Vite proxies `/api` → `localhost:3000` automatically.

### Tests

```bash
make test          # server + web
make test-server   # server only (pytest)
make test-web      # web only (vitest)
```

---

## Docker deployment

A single Docker image runs nginx (port 8080) and uvicorn together via supervisord. An optional ngrok container provides a public HTTPS tunnel.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- A free [ngrok account](https://dashboard.ngrok.com) for the public tunnel

### 1. Configure

```bash
cp .env.example .env.local
```

Edit `.env.local` — the key fields:

| Variable | Required | Description |
|---|---|---|
| `FAIRSHARE_SECRET_KEY` | ✅ | Strong random string — signs JWTs |
| `REGISTRATION_INVITE_CODE` | ✅ | Secret code friends enter to register |
| `NGROK_AUTHTOKEN` | For tunnel | From [dashboard.ngrok.com/authtokens](https://dashboard.ngrok.com/authtokens) |
| `NGROK_DOMAIN` | Optional | Your static ngrok domain, e.g. `yourapp.ngrok-free.app` |
| `ALLOWED_ORIGINS` | For tunnel | Add your ngrok domain, e.g. `https://yourapp.ngrok-free.app` |

Generate secrets:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Build and start

```bash
make docker-up
# or: docker compose --env-file .env.local up -d --build
```

The app is now running at **http://localhost:8080**.

### 3. Public tunnel (ngrok)

If you set `NGROK_AUTHTOKEN` in `.env.local`, the ngrok container starts automatically alongside the app. Your public URL appears in the ngrok dashboard at **http://localhost:4040**, or `NGROK_DOMAIN` if you set a static domain.

### Useful commands

```bash
make docker-up      # Build + start in background
make docker-down    # Stop containers
make docker-logs    # Tail all container logs
make docker-build   # Rebuild image only
```

### Data persistence

The SQLite database is stored in a named Docker volume (`fairshare-data`) and survives container restarts and rebuilds.

---

## Security

- Non-root container user (`app`, uid 999)
- 512 MB memory cap, 256 PID limit
- Rate limiting: 5 registrations/hour per IP, 20 login attempts/hour per IP
- Security headers on all responses (`X-Content-Type-Options`, `X-Frame-Options`, `CSP`, etc.)
- Invite-only registration — empty `REGISTRATION_INVITE_CODE` disables registration entirely
- Passwords hashed with bcrypt

---

## Tech stack

- **Backend:** Python 3.12, FastAPI, uvicorn, SQLModel, Pydantic v2, structlog, slowapi
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui
- **Database:** SQLite (Docker named volume)
- **Auth:** JWT (HS256) + bcrypt
- **Deployment:** Docker + nginx + supervisord in a single container; ngrok for public tunnel

## Project structure

```
fairshare/
├── server/              # Python / FastAPI backend
│   ├── app/
│   │   ├── api/         #   REST endpoints
│   │   ├── db/          #   SQLModel models & session
│   │   ├── auth.py      #   JWT + password hashing
│   │   ├── config.py    #   Pydantic settings
│   │   ├── limiter.py   #   Rate limiting (slowapi)
│   │   └── main.py      #   App entrypoint
│   └── tests/           #   pytest suite
├── web/                 # React / TypeScript frontend
│   └── src/
│       ├── components/  #   UI components (shadcn/ui)
│       ├── lib/         #   API client, auth helpers, types
│       └── pages/       #   Route pages
├── docker/              # nginx.conf + supervisord.conf
├── docs/                # Implementation stories
├── Dockerfile           # Multi-stage build
├── docker-compose.yml   # App + ngrok services
└── Makefile             # Dev, test, Docker targets
```
