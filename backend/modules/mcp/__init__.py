"""MCP module — only MCPRouter routes with mcp=True are exposed as tools."""

from modules.mcp.routes import router

__all__ = ['router']
