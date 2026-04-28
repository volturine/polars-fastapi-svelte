# Operations

This skill stands in for the Perplexity MCP server.

Primary operations to mirror:

- `perplexity_search`: ranked web search results
- `perplexity_ask`: quick web-grounded answer
- `perplexity_reason`: comparison or analytical reasoning with citations
- `perplexity_research`: deeper multi-source research

Wrapper scripts in this skill:

- `scripts/check_perplexity_mcp.py`: run a real stdio MCP initialize plus tools-list check
- `scripts/check_perplexity_request.py`: make a real `perplexity_search` request to verify upstream access
