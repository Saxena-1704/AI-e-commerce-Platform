import asyncio

from fastmcp import Client

from backend.app.mcp.server import mcp


async def main():

    async with Client(mcp) as client:

        print("\n=== AVAILABLE TOOLS ===")

        tools = await client.list_tools()

        for tool in tools:
            print(tool.name)

        print("\n=== SEARCH CATALOG ===")

        result = await client.call_tool(
            "search_catalog",
            {
                "query": "laptop",
                "limit": 5,
                "offset": 0,
            },
        )

        print(result.data)

        print("\n=== LOOKUP CATALOG ===")

        result = await client.call_tool(
            "lookup_catalog",
            {
                "ids": ["7", "8", "9"],
            },
        )

        print(result.data)

        print("\n=== GET PRODUCT ===")

        result = await client.call_tool(
            "get_product",
            {
                "id": "7",
            },
        )

        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())