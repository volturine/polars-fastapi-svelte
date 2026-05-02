# Command Patterns

Use these patterns when the built-in `gh` subcommands are not enough or when structured output matters.

## Structured output

Prefer JSON fields that match the decision you need to make.

Examples:

```bash
gh pr view 123 --repo OWNER/REPO \
  --json title,state,mergeStateStatus,reviewDecision,statusCheckRollup


gh issue view 456 --repo OWNER/REPO \
  --json title,state,labels,assignees,author,url


gh run list --repo OWNER/REPO \
  --json databaseId,workflowName,status,conclusion,headBranch,createdAt
```

Use `--jq` when only a narrow slice is needed:

```bash
gh pr view 123 --repo OWNER/REPO --json url --jq '.url'
gh repo view --repo OWNER/REPO --json defaultBranchRef --jq '.defaultBranchRef.name'
```

## API requests

Use `gh api` for endpoints with no convenient top-level command.

### REST GET

```bash
gh api repos/OWNER/REPO/branches
gh api repos/OWNER/REPO/contents/path/to/file
```

### REST mutation

Always set the method explicitly for non-GET requests.

```bash
gh api --method POST repos/OWNER/REPO/issues/123/comments \
  -f body='Looks good to me'


gh api --method PATCH repos/OWNER/REPO/pulls/123 \
  -f title='New title'
```

### Nested or typed fields

Use `-f` for form fields and `-F` when GitHub CLI should interpret values like files or typed literals.

```bash
gh api --method POST repos/OWNER/REPO/issues \
  -f title='Bug report' \
  -f body='Details here'
```

### Pagination

```bash
gh api --paginate repos/OWNER/REPO/pulls
```

Paginated output is easiest to process as JSON lines or with `jq` after collection.

## GraphQL

Use GraphQL when a single request can replace multiple REST calls.

```bash
gh api graphql \
  -f query='query($owner:String!, $repo:String!, $number:Int!) {
    repository(owner:$owner, name:$repo) {
      pullRequest(number:$number) {
        title
        state
        reviewDecision
        url
      }
    }
  }' \
  -F owner=OWNER \
  -F repo=REPO \
  -F number=123
```

Prefer GraphQL when you need nested related objects such as review state, labels, latest commits, or linked metadata in one round trip.

## Actions diagnostics

These commands are useful for workflow failures:

```bash
gh run view 123456 --repo OWNER/REPO --json jobs

gh run view 123456 --repo OWNER/REPO --log
```

If the user wants a summary, fetch the run first, then summarize specific failed jobs and steps instead of dumping the entire log.

## Enterprise and alternate hosts

For GitHub Enterprise, add `--hostname HOSTNAME` consistently:

```bash
gh auth status --hostname github.example.com
gh repo view --repo OWNER/REPO --hostname github.example.com
```

## Safety checklist

Before any mutation, confirm:

1. target repo
2. target object id or tag
3. requested state change
4. whether a dry inspection step should run first
