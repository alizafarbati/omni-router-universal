#!/usr/bin/env bash
# ============================================================
#  OmniRouter - Unix (Linux/macOS) launcher
#  Starts the free-tier AI router on http://127.0.0.1:8787/v1
#  Usage: ./omni-router.sh [port]
# ============================================================
set -euo pipefail
PORT="${1:-8787}"
export OMNI_PORT="$PORT"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python || true)"
if [[ -z "$PY" ]]; then
    echo "[OmniRouter] ERROR: python3 not found. Install Python 3.8+."
    exit 1
fi

echo "[OmniRouter] Starting on port $PORT ..."
exec "$PY" "$SCRIPT_DIR/../omni_router/omni_router.py"

