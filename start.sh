#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Device Dashboard - One-Click Start${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# --- Python deps ---
echo -e "${YELLOW}[1/3] Installing Python dependencies...${NC}"
if command -v uv &>/dev/null; then
    uv sync --quiet
else
    echo "uv not found, falling back to pip"
    python3 -m pip install -q -e .
fi

# --- Frontend build ---
echo -e "${YELLOW}[2/3] Building frontend...${NC}"
cd frontend
if [ ! -d node_modules ]; then
    npm install --silent
fi
npm run build --silent
cd ..

# --- .env ---
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || true
fi

# --- Ensure data directory exists for SQLite ---
mkdir -p data

# --- Start ---
echo -e "${YELLOW}[3/3] Starting server on http://0.0.0.0:8090${NC}"
echo ""
echo -e "${GREEN}Dashboard ready at: http://localhost:8090${NC}"
echo -e "${GREEN}Press Ctrl+C to stop${NC}"
echo ""

exec uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090
