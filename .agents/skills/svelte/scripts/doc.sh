#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  printf 'usage: %s <workdir> [section]\n' "$0" >&2
  exit 1
fi

WORKDIR="$1"
shift

cd "$WORKDIR"

if [[ $# -eq 0 ]]; then
  exec npx -y @sveltejs/mcp list-sections
fi

exec npx -y @sveltejs/mcp get-documentation "$*"
