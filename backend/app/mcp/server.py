from fastmcp import FastMCP

from backend.app.mcp.tools.catalog import register_catalog_tools
from backend.app.mcp.tools.cart import register_cart_tools
from backend.app.mcp.tools.checkout import register_checkout_tools
from backend.app.mcp.tools.payment import register_payment_tools


mcp = FastMCP(
    name="AI Ecommerce UCP Server"
)


register_catalog_tools(mcp)
register_cart_tools(mcp)
register_checkout_tools(mcp)
register_payment_tools(mcp)