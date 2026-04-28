#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'usage: %s <workdir>\n' "$0" >&2
  exit 1
fi

cd "$1"
npx -y @sveltejs/mcp list-sections >/tmp/svelte-mcp-sections.txt
printf 'svelte mcp ok; first lines:\n'
sed -n '1,8p' /tmp/svelte-mcp-sections.txt
