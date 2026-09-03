from fastmcp import FastMCP

from backend.app.mcp.tools.catalog import register_catalog_tools


mcp = FastMCP(
    name="AI Ecommerce UCP Server"
)


register_catalog_tools(mcp)