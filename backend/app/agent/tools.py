import os

import httpx
from langchain_core.tools import tool


MERCHANT_API_BASE_URL = os.getenv(
    "MERCHANT_API_BASE_URL",
    "http://localhost:8000",
).rstrip("/")


def get_merchant_api_tools(auth_token: str):
    """Build read-only tools backed by the existing merchant APIs."""

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }

    async def get_json(path: str):
        try:
            async with httpx.AsyncClient(
                base_url=MERCHANT_API_BASE_URL,
                timeout=10.0,
            ) as client:
                response = await client.get(
                    path,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Merchant API request failed with status "
                f"{exc.response.status_code}."
            ) from exc

        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(
                "Merchant API request could not be completed."
            ) from exc

    @tool
    async def get_merchant_overview() -> dict:
        """Get the merchant dashboard summary from the existing overview API."""
        return await get_json("/merchant/overview")

    @tool
    async def list_products() -> list:
        """List products from the existing products API."""
        return await get_json("/products/")

    @tool
    async def get_product(product_id: int) -> dict:
        """Get one product by ID from the existing products API."""
        return await get_json(f"/products/{product_id}")

    @tool
    async def get_all_merchant_orders() -> list:
        """
        Fetch all ecommerce orders for the authenticated merchant.

        Use this tool when the merchant asks about:
        - products that generated the most revenue
        - units sold
        - best-selling products
        - product-level sales
        - product revenue

        The tool returns all orders with their order items.

        For revenue and units sold, only paid orders should be used.
        Revenue should be calculated from order item total_amount.
        Units sold should be calculated from order item quantity.
        """
        return await get_json("/merchant/orders")

    return [
        get_merchant_overview,
        list_products,
        get_product,
        get_all_merchant_orders,
    ]