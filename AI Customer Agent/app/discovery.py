import httpx


async def discover_merchant(merchant_url: str) -> dict:
    """
    Fetch the merchant's UCP profile.
    """

    profile_url = f"{merchant_url.rstrip('/')}/.well-known/ucp"

    async with httpx.AsyncClient() as client:
        response = await client.get(profile_url)
        response.raise_for_status()

        return response.json()


def get_mcp_endpoint(profile: dict) -> str:
    """
    Extract the MCP endpoint from the UCP profile.
    """

    services = profile["ucp"]["services"]

    for service_implementations in services.values():
        for implementation in service_implementations:
            if implementation.get("transport") == "mcp":
                return implementation["endpoint"]

    raise ValueError("No MCP endpoint found in UCP profile")