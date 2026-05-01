#!/usr/bin/env bash
set -euo pipefail

APP_NAME="fairshare-app"
REGION="lhr"

echo "=== FairShare Fly.io Setup ==="

# Create app
echo "Creating app ${APP_NAME}..."
fly apps create "${APP_NAME}" --machines 2>/dev/null || echo "App already exists"

# Create volume
echo "Creating 1GB volume..."
fly volumes create fairshare_data --region "${REGION}" --size 1 --app "${APP_NAME}" --yes 2>/dev/null || echo "Volume already exists"

# Set secrets from .env.local if it exists
if [ -f .env.local ]; then
  echo "Importing secrets from .env.local..."
  grep -v '^#' .env.local | grep '=' | while IFS='=' read -r key value; do
    [ -n "$key" ] && fly secrets set "${key}=${value}" --app "${APP_NAME}" 2>/dev/null || true
  done
fi

# Deploy
echo "Deploying..."
fly deploy --ha=false --app "${APP_NAME}"

echo ""
echo "=== Done! ==="
echo "App URL: https://${APP_NAME}.fly.dev"
