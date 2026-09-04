import asyncio
import os

from dotenv import load_dotenv

from app.discovery import discover_merchant, get_mcp_endpoint
from app.auth import login
from app.mcp import get_mcp_tools
from app.agent import create_buyer_agent


load_dotenv()

MERCHANT_URL = os.getenv("MERCHANT_API_URL")


async def main():

    print("1. Discovering merchant...")

    profile = await discover_merchant(MERCHANT_URL)

    print("✓ UCP profile discovered")

    print("\n2. Discovering MCP endpoint...")

    mcp_endpoint = get_mcp_endpoint(profile)

    print(f"✓ MCP endpoint: {mcp_endpoint}")

    print("\n3. Authenticating buyer...")

    jwt = await login()

    print("✓ Buyer authenticated")

    print("\n4. Discovering MCP tools...")

    tools = await get_mcp_tools(mcp_endpoint, jwt)

    print("✓ Tools discovered:")

    for tool in tools:
        print(f"- {tool.name}")

    print("\n5. Creating buyer agent...")

    agent = create_buyer_agent(tools)

    print("✓ Buyer agent ready")

    print("\n========================================")
    print("        UCP AI BUYER")
    print("========================================")
    print("Type 'exit' to quit.\n")

    while True:

        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            result = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_input,
                        }
                    ]
                }
            )

            response = result["messages"][-1].content

            print(f"\nBuyer: {response}\n")

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())