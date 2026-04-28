#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  printf 'usage: %s <workdir> <compose-file> <server-url>\n' "$0" >&2
  exit 1
fi

WORKDIR="$1"
COMPOSE_FILE="$2"
SERVER_URL="$3"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$WORKDIR"
docker compose -f "$COMPOSE_FILE" up -d
python3 "$SCRIPT_DIR/check_playwright_mcp.py" "$SERVER_URL"
