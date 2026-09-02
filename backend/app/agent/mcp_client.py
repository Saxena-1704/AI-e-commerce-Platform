import base64
import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient


load_dotenv()


TEST_API_KEY = os.getenv("RAZORPAY_TEST_API_KEY")
TEST_KEY_SECRET = os.getenv("RAZORPAY_TEST_KEY_SECRET")


if not TEST_API_KEY or not TEST_KEY_SECRET:
    raise ValueError(
        "TEST_API_KEY and TEST_KEY_SECRET must be set in the environment."
    )


token = base64.b64encode(
    f"{TEST_API_KEY}:{TEST_KEY_SECRET}".encode()
).decode()


async def get_razorpay_tools():
    client = MultiServerMCPClient(
        {
            "razorpay": {
                "transport": "streamable_http",
                "url": "https://mcp.razorpay.com/mcp",
                "headers": {
                    "Authorization": f"Basic {token}"
                },
            }
        }
    )

    tools = await client.get_tools()

    return tools