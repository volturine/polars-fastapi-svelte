---
name: perplexity
description: Live web research workflow backed by Perplexity tooling. Use when Claude needs current facts, issue reports, release notes, comparisons, or multi-source synthesis from the public web that cannot be answered reliably from the repo or official docs alone.
---

# Perplexity

Use web research for freshness and breadth, not as a replacement for reading the target project or official docs.

Stay narrow and source-driven.

## Runtime Inputs

- Working directory where the MCP server will run
- MCP command: `npx -y @perplexity-ai/mcp-server`
- Required secret: an environment variable containing your Perplexity API key
- Default env var name: `PERPLEXITY_API_KEY`
- Optional env: `PERPLEXITY_TIMEOUT_MS=<milliseconds>`

Do not store secrets in the skill, in project files, or in command history when avoidable. Set the API key at runtime, then verify protocol access and optionally verify a live request.

## Automation

- MCP check: `PERPLEXITY_API_KEY=... python3 <skill-dir>/scripts/check_perplexity_mcp.py <workdir>`
- MCP check with custom env var: `MY_PERPLEXITY_KEY=... python3 <skill-dir>/scripts/check_perplexity_mcp.py --api-key-env-var MY_PERPLEXITY_KEY <workdir>`
- Live request check: `PERPLEXITY_API_KEY=... python3 <skill-dir>/scripts/check_perplexity_request.py <workdir> <query>`
- Live request check with custom env var: `MY_PERPLEXITY_KEY=... python3 <skill-dir>/scripts/check_perplexity_request.py --api-key-env-var MY_PERPLEXITY_KEY <workdir> <query>`

Read `references/operations.md` for the complete operation map.

Treat this skill as four possible operations: search, quick answer, reasoning, and deep research. Choose the cheapest one that answers the question.

Verification levels:

1. Protocol ready: `check_perplexity_mcp.py` passes after `initialize` and `tools/list`
2. Upstream ready: `check_perplexity_request.py` passes with a real search request

If level 1 passes and level 2 fails, the MCP server is configured correctly but the Perplexity account, quota, or upstream API access is not.

## Workflow

1. Write the exact question to answer.
2. Choose the lightest research mode that fits: search, quick answer, reasoning, or deep research.
3. Filter by recency or domain when freshness or trust matters.
4. Synthesize only the parts that affect the user's task.

## Capabilities

- Search for relevant sources quickly.
- Answer factual questions with citations.
- Compare options or analyze tradeoffs with web-grounded reasoning.
- Run deeper multi-source research only when the question warrants the latency.

## Rules

- Prefer primary sources for claims that affect implementation.
- Call out uncertainty, disagreement, or stale sources.
- Separate facts from recommendations.
- Do not use this skill when the answer should come from the codebase itself.
- Never hardcode API keys in the skill, target project, or wrapper scripts.
- Prefer custom environment variable names when sharing terminals, recordings, or reusable shell profiles.

## Output

Return the answer with source-backed takeaways, the date sensitivity if relevant, and the concrete implication for the task.
