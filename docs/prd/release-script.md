# PRD: Release Script

## Overview

Create a release script that automates the maintainer steps for cutting a production release: version bumping, validation, git tagging, and pushing the tag that triggers binary and Docker publishing workflows.

The release script must match the current product contract:

- one production compose file: `docker/docker-compose.yml`
- one production env template: `docker/env/prod.env`
- published fixed-role images: `api`, `scheduler`, `worker`
- GitHub Actions builds binaries and publishes GHCR images on tag push

## Problem Statement

The current release path is still partially manual and version drift is easy:

- version fields live in multiple files
- release validation depends on maintainers remembering the right commands
- Docker publishing now exists, but the release process does not describe it consistently
- docs can drift from the actual fixed-role production topology

## Goals

| # | Goal | Success Metric |
|---|------|----------------|
| G-1 | Single-command maintainer release | `just release 1.0.0` performs the local release preparation steps |
| G-2 | Validation before tagging | `just verify` and `just test` must pass before commit/tag creation |
| G-3 | Consistent versions | Backend, frontend, docs, and Docker env references are updated together |
| G-4 | Correct artifact trigger | Pushed tag causes GitHub Actions to publish binaries and fixed-role Docker images |
| G-5 | Safe dry run | Maintainer can preview changes without modifying git state |

## Non-Goals

- customer deployment automation beyond published release artifacts
- Kubernetes manifests or Helm charts
- publishing local smoke-test images to GHCR
- alternate production compose/env variants

## User Stories

### US-1: Cut A Release

> As a maintainer, I want one command that prepares and publishes a release correctly.

**Acceptance Criteria:**

1. `just release 1.0.0` validates the version format.
2. The script checks that the working tree is clean.
3. The script runs `just verify` and `just test` before creating release git objects.
4. The script updates all required version references.
5. The script creates a release commit named `release: v1.0.0`.
6. The script creates an annotated tag `v1.0.0`.
7. The script pushes the branch and tag to origin.
8. Tag push triggers:
   - `.github/workflows/build.yml`
   - `.github/workflows/docker-publish.yml`

### US-2: Preview A Release

> As a maintainer, I want to see the exact release changes before executing them.

**Acceptance Criteria:**

1. `just release 1.0.0 --dry-run` shows files that would change.
2. `just release 1.0.0 --dry-run` shows the git commit and tag actions that would run.
3. No files are modified.
4. No commit, tag, or push is created.

### US-3: Keep Docker Release Contract Intact

> As a maintainer, I want the release flow to preserve the customer-facing Docker contract.

**Acceptance Criteria:**

1. The release updates `docker/env/prod.env` image tags for the released version.
2. The release does not introduce another production compose file.
3. The release does not introduce another production env file.
4. The release assumes customer install is `docker compose pull && docker compose up -d` using published images.

## Technical Design

### Script

Create `scripts/release.sh` and expose it through `Justfile`.

Expected flow:

1. Validate `X.Y.Z` semver input.
2. Confirm a clean worktree.
3. Run `just verify`.
4. Run `just test`.
5. Update release version references.
6. Show or apply the diff.
7. Create commit and annotated tag.
8. Push branch and tag.

### Files To Update

The release script should update version references in the files that define shipped artifacts and customer-facing defaults:

- `backend/pyproject.toml`
- `frontend/package.json`
- `docker/env/prod.env`
- any release docs that intentionally carry explicit example tags

The script should not do broad blind replacement across the repository.

### GitHub Actions Contract

After tag push:

- `build.yml` builds binaries and creates the GitHub release
- `docker-publish.yml` publishes multi-arch images:
  - `ghcr.io/volturine/data-forge-api:X.Y.Z`
  - `ghcr.io/volturine/data-forge-scheduler:X.Y.Z`
  - `ghcr.io/volturine/data-forge-worker:X.Y.Z`

### Maintainer Local Smoke Tests

The release script does not publish local-only Docker images.

Pre-release Docker smoke remains:

```bash
just docker-prod
curl http://localhost:8000/health/ready
just docker-prod-down
```

That smoke test must continue using:

- `docker/docker-compose.yml`
- `docker/env/prod.env`

with shell overrides for local image names and placeholder secrets.

## File Deliverables

| File | Purpose |
|------|---------|
| `scripts/release.sh` | Maintainer release automation |
| `Justfile` | `release` and dry-run entrypoints |
| `CHANGELOG.md` | Release history, if changelog automation is adopted |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Version mismatch across release files | Medium | High | Update only explicit known files and fail if expected fields are missing |
| Tag pushed after incomplete validation | Low | High | Run `just verify` and `just test` before commit/tag creation |
| Docs drift from actual Docker contract | Medium | Medium | Keep release script PRD aligned to `docker-release.md` and current workflows |

## Acceptance Criteria

- [ ] `just release 1.0.0 --dry-run` previews release changes without side effects
- [ ] `just release 1.0.0` runs verification and tests before commit/tag creation
- [ ] release command updates version references consistently
- [ ] release command creates commit `release: v1.0.0`
- [ ] release command creates annotated tag `v1.0.0`
- [ ] pushed tag triggers both binary and Docker publish workflows
- [ ] released Docker artifacts match the fixed-role production topology
