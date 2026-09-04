from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_mcp_tools(mcp_endpoint: str, jwt: str):

    client = MultiServerMCPClient(
        {
            "merchant": {
                "transport": "streamable_http",
                "url": mcp_endpoint,
                "headers": {
                    "Authorization": f"Bearer {jwt}",
                },
            }
        }
    )

    return await client.get_tools()