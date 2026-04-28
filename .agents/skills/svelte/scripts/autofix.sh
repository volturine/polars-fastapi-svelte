#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  printf 'usage: %s <workdir> <file-or-code> [extra-args...]\n' "$0" >&2
  exit 1
fi

WORKDIR="$1"
shift

cd "$WORKDIR"
exec npx -y @sveltejs/mcp svelte-autofixer "$1" --svelte-version 5 "${@:2}"
