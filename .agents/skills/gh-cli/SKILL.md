---
name: gh-cli
description: GitHub CLI workflow for inspecting and managing repositories, pull requests, issues, Actions runs, releases, and GitHub API operations with `gh`. Use when the user wants work done through the GitHub CLI, asks for GitHub automation from the terminal, or needs `gh api` for endpoints not covered by built-in `gh` subcommands.
---

# GH CLI

Use `gh` as the primary interface for GitHub work.

Prefer explicit, inspectable commands and machine-readable output.

## Runtime Inputs

- Repository context, preferably as `OWNER/REPO`
- Optional issue number, PR number, branch, workflow name, run id, tag, or release id
- Optional GitHub host for GitHub Enterprise (`--hostname`)

If repository context is ambiguous, resolve it before acting.

## First Checks

1. Confirm `gh` is installed: `gh --version`
2. Confirm auth: `gh auth status`
3. Confirm repo context:
   - current repo: `gh repo view`
   - explicit repo: add `--repo OWNER/REPO`

Prefer `--repo OWNER/REPO` whenever the working directory might not match the target repository.

## Workflow

1. Identify the target repo, object type, and requested action.
2. Start with read-only inspection unless the user explicitly asked for a mutation.
3. Prefer structured output with `--json`, `--jq`, or `--template`.
4. Use `gh api` when a built-in subcommand cannot express the needed operation.
5. After any mutation, fetch the updated object and report the resulting state.

## Common Tasks

### Repository inspection

- repo summary: `gh repo view --repo OWNER/REPO`
- clone: `gh repo clone OWNER/REPO`
- fork: `gh repo fork OWNER/REPO`
- list repos for owner: `gh repo list OWNER --limit 100`

Prefer JSON when downstream reasoning depends on exact fields:

- `gh repo view --repo OWNER/REPO --json name,description,defaultBranchRef,url`

### Pull requests

Inspect first:

- list: `gh pr list --repo OWNER/REPO`
- view: `gh pr view <number> --repo OWNER/REPO`
- diff: `gh pr diff <number> --repo OWNER/REPO`
- checks: `gh pr checks <number> --repo OWNER/REPO`

Mutate only when asked:

- create: `gh pr create --repo OWNER/REPO ...`
- checkout: `gh pr checkout <number> --repo OWNER/REPO`
- comment: `gh pr comment <number> --repo OWNER/REPO --body '...'`
- review: `gh pr review <number> --repo OWNER/REPO --approve|--comment|--request-changes --body '...'`
- merge: `gh pr merge <number> --repo OWNER/REPO --merge|--squash|--rebase`

Use JSON for structured status checks:

- `gh pr view <number> --repo OWNER/REPO --json title,state,mergeStateStatus,reviewDecision,headRefName,baseRefName,commits,statusCheckRollup`

### Issues

- list: `gh issue list --repo OWNER/REPO`
- view: `gh issue view <number> --repo OWNER/REPO`
- create: `gh issue create --repo OWNER/REPO ...`
- comment: `gh issue comment <number> --repo OWNER/REPO --body '...'`
- edit: `gh issue edit <number> --repo OWNER/REPO ...`
- close: `gh issue close <number> --repo OWNER/REPO`
- reopen: `gh issue reopen <number> --repo OWNER/REPO`

### Actions and workflows

- list workflows: `gh workflow list --repo OWNER/REPO`
- view workflow: `gh workflow view <workflow> --repo OWNER/REPO`
- run workflow: `gh workflow run <workflow> --repo OWNER/REPO ...`
- list runs: `gh run list --repo OWNER/REPO`
- view run: `gh run view <run-id> --repo OWNER/REPO`
- watch run: `gh run watch <run-id> --repo OWNER/REPO`
- download logs: `gh run view <run-id> --repo OWNER/REPO --log`
- rerun: `gh run rerun <run-id> --repo OWNER/REPO`
- cancel: `gh run cancel <run-id> --repo OWNER/REPO`

For diagnostics, prefer JSON over scraping tables:

- `gh run list --repo OWNER/REPO --json databaseId,displayTitle,event,headBranch,status,conclusion,workflowName,createdAt`

### Releases

- list: `gh release list --repo OWNER/REPO`
- view: `gh release view <tag> --repo OWNER/REPO`
- create: `gh release create <tag> --repo OWNER/REPO ...`
- upload asset: `gh release upload <tag> <file> --repo OWNER/REPO`
- download assets: `gh release download <tag> --repo OWNER/REPO`
- delete: `gh release delete <tag> --repo OWNER/REPO`

### Search

- search PRs: `gh search prs --owner OWNER --state open --limit 100`
- search issues: `gh search issues --owner OWNER --limit 100`
- search code: `gh search code 'query' --repo OWNER/REPO --limit 100`

### Raw API access

Use `gh api` for endpoints not covered elsewhere.

Patterns:

- GET endpoint: `gh api repos/OWNER/REPO/pulls/NUMBER`
- explicit method: `gh api --method POST repos/OWNER/REPO/issues/NUMBER/comments -f body='...'`
- preview headers: `gh api -H 'Accept: application/vnd.github+json' ...`
- paginate: `gh api --paginate repos/OWNER/REPO/pulls`
- GraphQL: `gh api graphql -f query='query { viewer { login } }'`

Prefer these flags:

- `--jq` for extracting a narrow field
- `--template` for human-readable summaries
- `--include` when headers matter
- `--silent` only when the output is intentionally discarded

Read `references/command-patterns.md` when you need request-shaping examples or GraphQL patterns.

## Rules

- Do not push, merge, close, delete, edit, comment, trigger workflows, or create releases unless the user explicitly asked for that mutation.
- Follow repo-level git rules too: never push to remote unless explicitly asked.
- Prefer `--repo OWNER/REPO` over relying on the current directory.
- Prefer `--json` or `gh api` JSON responses over parsing columnar text.
- When a command could affect the wrong repo, show or verify the resolved repo first.
- When using `gh api`, specify the HTTP method explicitly for non-GET requests.
- After mutations, re-fetch the object to confirm the final state.

## Output

Report:

1. Target repo and object
2. Exact `gh` command or command family used
3. Key result or state transition
4. Any follow-up action, URL, or risk
