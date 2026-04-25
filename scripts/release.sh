#!/usr/bin/env bash
set -euo pipefail

version="${1:-}"
mode="${2:-}"

if [[ -z "$version" ]]; then
	printf 'Usage: bash scripts/release.sh <version> [--dry-run]\n' >&2
	exit 1
fi

if [[ -n "$mode" && "$mode" != "--dry-run" ]]; then
	printf 'Unsupported flag: %s\n' "$mode" >&2
	exit 1
fi

if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
	printf 'Invalid version: %s\n' "$version" >&2
	exit 1
fi

if [[ -n "$(git status --short)" ]]; then
	printf 'Working tree must be clean before running release.\n' >&2
	exit 1
fi

branch="$(git branch --show-current)"

if [[ -z "$branch" ]]; then
	printf 'Release requires a checked out branch.\n' >&2
	exit 1
fi

if git rev-parse --verify "v$version" >/dev/null 2>&1; then
	printf 'Tag v%s already exists locally.\n' "$version" >&2
	exit 1
fi

if git ls-remote --tags origin "refs/tags/v$version" | grep -q .; then
	printf 'Tag v%s already exists on origin.\n' "$version" >&2
	exit 1
fi

current="$(grep -E '^DF_APP_VERSION=' docker/env/prod.env | cut -d= -f2 | tr -d '"')"

if [[ -z "$current" ]]; then
	printf 'Could not read current version from docker/env/prod.env.\n' >&2
	exit 1
fi

if [[ "$current" == "$version" ]]; then
	printf 'Version %s is already current.\n' "$version" >&2
	exit 1
fi

tmp="$(mktemp -d)"
files=(
	"backend/pyproject.toml"
	"frontend/package.json"
	"docker/env/prod.env"
	"docker/env/dev.env"
	"backend/prod.env"
	"backend/dev.env"
	"ENV_VARIABLES.md"
	"docs/prd/docker-release.md"
)

cleanup() {
	rm -rf "$tmp"
}

trap cleanup EXIT

render() {
	local src="$1"
	local dst="$2"
	cp "$src" "$dst"

	case "$src" in
		backend/pyproject.toml)
			perl -0pi -e 's/version = "'"$current"'"/version = "'"$version"'"/' "$dst"
			;;
		frontend/package.json)
			perl -0pi -e 's/"version": "'"$current"'"/"version": "'"$version"'"/' "$dst"
			;;
		docker/env/prod.env)
			perl -0pi -e 's/^DF_APP_VERSION=.*/DF_APP_VERSION='"$version"'/m' "$dst"
			perl -0pi -e 's#^DF_API_IMAGE=.*#DF_API_IMAGE=ghcr.io/volturine/data-forge-api:'"$version"'#m' "$dst"
			perl -0pi -e 's#^DF_SCHEDULER_IMAGE=.*#DF_SCHEDULER_IMAGE=ghcr.io/volturine/data-forge-scheduler:'"$version"'#m' "$dst"
			perl -0pi -e 's#^DF_WORKER_IMAGE=.*#DF_WORKER_IMAGE=ghcr.io/volturine/data-forge-worker:'"$version"'#m' "$dst"
			;;
		docker/env/dev.env)
			perl -0pi -e 's/^DF_APP_VERSION=.*/DF_APP_VERSION='"$version"'/m' "$dst"
			;;
		backend/prod.env|backend/dev.env)
			perl -0pi -e 's/^APP_VERSION="[^"]+"/APP_VERSION="'"$version"'"/m' "$dst"
			;;
		ENV_VARIABLES.md)
			perl -0pi -e 's/\| `APP_VERSION`\s+\| `'"$current"'`/| `APP_VERSION`                | `'"$version"'`/' "$dst"
			perl -0pi -e 's#ghcr\.io/volturine/data-forge-api:'"$current"'#ghcr.io/volturine/data-forge-api:'"$version"'#g' "$dst"
			perl -0pi -e 's#ghcr\.io/volturine/data-forge-scheduler:'"$current"'#ghcr.io/volturine/data-forge-scheduler:'"$version"'#g' "$dst"
			perl -0pi -e 's#ghcr\.io/volturine/data-forge-worker:'"$current"'#ghcr.io/volturine/data-forge-worker:'"$version"'#g' "$dst"
			;;
		docs/prd/docker-release.md)
			perl -0pi -e 's#ghcr\.io/volturine/data-forge-api:'"$current"'#ghcr.io/volturine/data-forge-api:'"$version"'#g' "$dst"
			perl -0pi -e 's#ghcr\.io/volturine/data-forge-scheduler:'"$current"'#ghcr.io/volturine/data-forge-scheduler:'"$version"'#g' "$dst"
			perl -0pi -e 's#ghcr\.io/volturine/data-forge-worker:'"$current"'#ghcr.io/volturine/data-forge-worker:'"$version"'#g' "$dst"
			;;
		*)
			printf 'Unhandled release file: %s\n' "$src" >&2
			exit 1
			;;
	 esac
	
	if cmp -s "$src" "$dst"; then
		printf 'Expected version update in %s, but no change was produced.\n' "$src" >&2
		exit 1
	fi
}

for file in "${files[@]}"; do
	render "$file" "$tmp/$(basename "$file")"
done

if [[ "$mode" == "--dry-run" ]]; then
	printf 'Release dry run for v%s\n' "$version"
	printf 'Current branch: %s\n' "$branch"
	printf 'Current version: %s\n' "$current"
	printf '\n'
	for file in "${files[@]}"; do
		printf '--- %s ---\n' "$file"
		diff -u "$file" "$tmp/$(basename "$file")" || true
		printf '\n'
		done
	printf 'Commands that would run:\n'
	printf '  just verify\n'
	printf '  just test\n'
	printf '  git add %s\n' "${files[*]}"
	printf '  git commit -m "release: v%s"\n' "$version"
	printf '  git tag -a "v%s" -m "Release v%s"\n' "$version" "$version"
	printf '  git push origin %s --follow-tags\n' "$branch"
	exit 0
fi

for file in "${files[@]}"; do
	cp "$tmp/$(basename "$file")" "$file"
done

just verify
just test

git add "${files[@]}"
git commit -m "release: v$version"
git tag -a "v$version" -m "Release v$version"
git push origin "$branch" --follow-tags
