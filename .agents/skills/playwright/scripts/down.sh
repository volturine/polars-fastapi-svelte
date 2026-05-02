#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  printf 'usage: %s <workdir> <compose-file>\n' "$0" >&2
  exit 1
fi

cd "$1"
docker compose -f "$2" down
