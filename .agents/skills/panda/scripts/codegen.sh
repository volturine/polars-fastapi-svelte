#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  printf 'usage: %s <workdir> [codegen-args...]\n' "$0" >&2
  exit 1
fi

WORKDIR="$1"
shift

cd "$WORKDIR"
exec npx panda codegen "$@"
