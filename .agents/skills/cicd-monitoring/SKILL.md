---
name: cicd-monitoring
description: Monitor and diagnose CI/CD runs, especially GitHub Actions hangs, stuck jobs, flaky checks, and CI/local drift. Use when a user asks to inspect workflow status, identify where a run stalled, compare failing and passing runs, or report actionable CI findings.
---

# CI/CD Monitoring

Use this skill for read-only inspection of CI/CD state unless the user explicitly asks for a mutation such as rerun or cancel.

Prefer GitHub Actions inspection through `gh` first. If `gh` auth is broken and the repository is public, fall back to the public GitHub REST API with `curl`.

## Inputs to resolve first

- Repository, preferably `OWNER/REPO`
- Branch, PR number, workflow name, run id, or commit SHA
- Whether the user wants current status, historical diagnosis, or a comparison across runs

If the repo is ambiguous, resolve it before inspecting runs.

## First checks

1. Confirm `gh` availability: `gh --version`
2. Confirm auth: `gh auth status`
3. Confirm repo context:
   - `gh repo view OWNER/REPO --json nameWithOwner,defaultBranchRef,url`
   - If `gh repo view` syntax differs in the installed version, use `gh repo view OWNER/REPO --json ...`
4. If `gh` auth is invalid and the repo is public, switch to `curl https://api.github.com/repos/OWNER/REPO/...`

## Default workflow

1. Identify the exact run to inspect.
   - If the user gave a run id, use it directly.
   - If the user gave a SHA, branch, PR, or workflow, resolve the newest matching run first.
2. Inspect run-level state.
3. Inspect job-level state.
4. Inspect step-level state for the suspicious job.
5. If needed, fetch logs.
6. Compare against the last known good or last similar failed run.
7. Report the exact failing or stalled boundary, not just “CI is stuck”.

## GitHub Actions commands

Prefer structured output.

### Resolve recent runs

```bash
gh run list --repo OWNER/REPO \
  --limit 20 \
  --json databaseId,workflowName,headSha,headBranch,event,status,conclusion,createdAt,displayTitle
```

Filter by SHA when needed:

```bash
gh run list --repo OWNER/REPO \
  --limit 50 \
  --json databaseId,headSha,workflowName,status,conclusion,createdAt \
  --jq '.[] | select(.headSha=="FULL_SHA")'
```

### Inspect a run

```bash
gh run view RUN_ID --repo OWNER/REPO
```

For logs:

```bash
gh run view RUN_ID --repo OWNER/REPO --log
```

### Inspect jobs for a run

Use `gh api` when job details are needed in JSON:

```bash
gh api repos/OWNER/REPO/actions/runs/RUN_ID/jobs
```

Useful extraction pattern:

```bash
gh api repos/OWNER/REPO/actions/runs/RUN_ID/jobs \
  --jq '.jobs[] | {id, name, status, conclusion, started_at, completed_at}'
```

### Public API fallback

For public repos when `gh` auth is unusable:

```bash
curl -fsSL 'https://api.github.com/repos/OWNER/REPO/actions/runs?branch=BRANCH&per_page=20'
curl -fsSL 'https://api.github.com/repos/OWNER/REPO/actions/runs/RUN_ID'
curl -fsSL 'https://api.github.com/repos/OWNER/REPO/actions/runs/RUN_ID/jobs?per_page=20'
```

Parse with `python3` or `jq`, not brittle text scraping.

## How to diagnose hangs

Treat hangs as a timeline problem.

### 1. Find the last confirmed progress boundary

Look for:
- last completed job
- last completed step in the stuck job
- first step still marked `in_progress`
- last meaningful log line emitted before silence

State findings as:
- run level: in progress / completed
- job level: which job is stuck
- step level: which exact step is still running
- log level: last emitted evidence

### 2. Distinguish startup vs test-runtime vs teardown hangs

Common categories:
- setup stall: dependency install, browser install, checkout, cache restore
- runtime stall: tests or build command still active but not finishing
- teardown stall: tests passed but process cleanup, artifact upload, or post-run hooks never finish

Signals:
- if jobs never reach the test command, it is not a test assertion issue
- if the test step is `in_progress` long after normal runtime, suspect a stuck process or hanging teardown
- if logs show tests passed but the job never completes, suspect cleanup/post-run behavior

### 3. Compare to a good run

Compare:
- total duration
- same workflow on nearby commits
- same job’s step durations
- whether the stuck step moved after a fix

A partial improvement matters. Example: if a warning count drops from 18 to 9, or the hang shifts from startup into runtime, say so explicitly.

### 4. Check for CI/local drift

Inspect repo-controlled sources of truth before blaming CI:
- workflow YAML
- shared env files
- harness scripts
- worker count / timeout settings
- Python, Node, Bun, Playwright versions
- artifact and log paths

Call out drift precisely, for example:
- CI overrides worker count differently from the repo harness
- CI uses a different Python version than local
- CI wraps the test command in a separate timeout layer not used locally

### 5. Report limitations honestly

Examples:
- `gh` auth invalid locally, used public API fallback instead
- public API rate-limited, could not continue polling
- logs truncated or missing, diagnosis based on jobs/steps only

## When logs are available

Search logs for:
- last printed test/spec name
- heartbeat lines
- teardown messages
- process-kill messages
- warnings near shutdown
- resource-tracker, semaphore, websocket, or disconnect errors

Prefer narrowing with search tools after saving logs locally.

## Output format

Report:

1. Target repo and run
2. Exact command family used (`gh run`, `gh api`, or public `curl` fallback)
3. Current or final state
4. Exact stuck boundary: job, step, and last useful signal
5. Most likely explanation
6. Next best action
7. Any tooling limitations

## Rules

- Read-only by default; rerun/cancel only if the user explicitly asks
- Prefer `gh` over raw API when authenticated
- Prefer JSON over scraped tables
- If falling back to public API, state rate-limit risk up front
- Do not claim CI is fixed unless the target run actually finishes successfully
- Distinguish “improved” from “resolved”
- When comparing runs, cite run ids and SHAs explicitly
