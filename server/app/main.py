"""FairShare — Splitwise-style expense splitting application."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.auth import router as auth_router
from app.api.balances import router as balances_router
from app.api.dashboard import router as dashboard_router
from app.api.expenses import router as expenses_router
from app.api.groups import router as groups_router
from app.api.payments import router as payments_router
from app.api.users import router as users_router
from app.auth import ensure_admin_user, init_auth
from app.config import settings
from app.db.session import get_session, init_db
from app.limiter import limiter
from app.seed import seed_demo_data
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

    if settings.seed_demo:
        seed_demo_data(session)

    logger.info("app_started")
    yield


app = FastAPI(title="FairShare", description="Splitwise-style expense splitting", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self' data:; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    if forwarded_proto == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
