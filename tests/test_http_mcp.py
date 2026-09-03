import asyncio

from fastmcp import Client


async def main():
    async with Client("http://localhost:8000/ucp/mcp/") as client:
        tools = await client.list_tools()

        print("\nAvailable MCP tools:\n")

        for tool in tools:
            print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())