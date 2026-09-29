from dotenv import load_dotenv
import os

load_dotenv()

base_url = os.getenv("BASE_URL")

if not base_url:
    raise ValueError("BASE_URL is not set in .env")

mcp_endpoint = f"{base_url.rstrip('/')}/ucp/mcp"

UCP_PROFILE = {
    "ucp": {
        "version": "2026-08-25",

        "services": {
            "dev.ucp.shopping": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/overview",
                    "transport": "mcp",
                    "schema": "https://ucp.dev/2026-08-25/services/shopping/mcp.openrpc.json",
                    "endpoint": mcp_endpoint
                }
            ]
        },

        "capabilities": {
            "dev.ucp.shopping.catalog.search": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/shopping/catalog/search",
                    "schema": "https://ucp.dev/2026-08-25/schemas/shopping/catalog_search.json"
                }
            ],

            "dev.ucp.shopping.catalog.lookup": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/shopping/catalog/lookup",
                    "schema": "https://ucp.dev/2026-08-25/schemas/shopping/catalog_lookup.json"
                }
            ],

            "dev.ucp.shopping.cart": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/shopping/cart",
                    "schema": "https://ucp.dev/2026-08-25/schemas/shopping/cart.json"
                }
            ],

            "dev.ucp.shopping.checkout": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/shopping/checkout",
                    "schema": "https://ucp.dev/2026-08-25/schemas/shopping/checkout.json"
                }
            ]
        },

        "payment_handlers": {}
    }
}
