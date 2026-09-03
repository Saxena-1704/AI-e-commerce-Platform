UCP_PROFILE = {
    "ucp": {
        "version": "2026-08-25",

        "services": {
            "dev.ucp.shopping": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/overview",
                    "transport": "mcp",
                    "endpoint": "https://d6d1-49-43-161-175.ngrok-free.app/ucp/mcp"
                }
            ]
        },

        "capabilities": {
            "dev.ucp.shopping.catalog.search": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/shopping/catalog/search"
                }
            ],

            "dev.ucp.shopping.catalog.lookup": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/shopping/catalog/lookup"
                }
            ],

            "dev.ucp.shopping.cart": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/shopping/cart"
                }
            ],

            "dev.ucp.shopping.checkout": [
                {
                    "version": "2026-08-25",
                    "spec": "https://ucp.dev/2026-08-25/specification/shopping/checkout"
                }
            ]
        }
    }
}