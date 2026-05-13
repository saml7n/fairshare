# ── Stage 1: Build web static files ──────────────────────────────────────────
FROM node:20-alpine AS web-build

WORKDIR /app
COPY web/package.json web/package-lock.json* ./
RUN npm ci
COPY web/ .
RUN npm run build

# ── Stage 2: Production image (nginx + uvicorn via supervisord) ───────────────
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx supervisor curl && \
    rm -rf /var/lib/apt/lists/*

# uv for fast Python dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies first (layer-cached until pyproject.toml changes)
COPY server/pyproject.toml server/uv.lock* ./
RUN uv sync --no-dev --no-install-project

# Application code
COPY server/app/ ./app/

# Built frontend assets
COPY --from=web-build /app/dist /usr/share/nginx/html

# Config
COPY docker/nginx.conf /etc/nginx/sites-enabled/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/fairshare.conf
RUN rm -f /etc/nginx/conf.d/default.conf

# Redirect nginx PID file to /tmp so non-root user can write it
RUN sed -i 's|pid /run/nginx.pid;|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf

# Persistent data directory (mount a volume here)
RUN mkdir -p /app/data

# Run as non-root for security
RUN groupadd -r app && useradd -r -g app -d /app app \
    && chown -R app:app /app \
    && chown -R app:app /usr/share/nginx/html \
    && chown -R app:app /var/log/nginx \
    && chown -R app:app /var/lib/nginx \
    && chown -R app:app /etc/supervisor/conf.d

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/fairshare.conf"]
