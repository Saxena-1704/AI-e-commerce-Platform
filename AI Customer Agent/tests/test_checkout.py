import asyncio
import os
from fastmcp import Client


async def main():
    headers = {
        "Authorization": f"Bearer {os.environ['MCP_JWT']}"
    }

    async with Client(
        "https://d6d1-49-43-161-175.ngrok-free.app/ucp/mcp/",
        headers=headers,
    ) as client:

        print("Tools:")
        tools = await client.list_tools()
        print([tool.name for tool in tools])

        print("\nCalling create_checkout...")

        result = await client.call_tool(
            "create_checkout"
        )

        print("Result:")
        print(result.data)


asyncio.run(main())