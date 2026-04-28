#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  printf 'usage: %s <workdir> <panda-config-path>\n' "$0" >&2
  exit 1
fi

WORKDIR="$1"
CONFIG="$2"

cd "$WORKDIR"

if [[ ! -f "$CONFIG" ]]; then
  printf 'panda config not found: %s\n' "$CONFIG" >&2
  exit 1
fi

npx panda --help >/dev/null
npx panda codegen --help >/dev/null
npx panda analyze --help >/dev/null
printf 'panda cli ok and config exists at %s\n' "$CONFIG"
