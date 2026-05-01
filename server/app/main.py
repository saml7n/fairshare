"""FairShare — Splitwise-style expense splitting application."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.balances import router as balances_router
from app.api.dashboard import router as dashboard_router
from app.api.expenses import router as expenses_router
from app.api.groups import router as groups_router
from app.api.payments import router as payments_router
from app.api.users import router as users_router
from app.auth import ensure_admin_user, init_auth
from app.db.session import get_session, init_db
from app.logging import setup_logging

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    init_db()
    init_auth()

    session = next(get_session())
    ensure_admin_user(session)

    logger.info("app_started")
    yield


app = FastAPI(title="FairShare", description="Splitwise-style expense splitting", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(balances_router)
app.include_router(dashboard_router)
app.include_router(expenses_router)
app.include_router(groups_router)
app.include_router(payments_router)
app.include_router(users_router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
