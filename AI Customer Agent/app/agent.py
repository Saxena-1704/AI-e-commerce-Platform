import os

from langchain_groq import ChatGroq
from langchain.agents import create_agent

from app.discovery import discover_merchant, get_mcp_endpoint
from app.mcp import get_mcp_tools
from app.prompt import system_prompt


def create_buyer_agent(tools):

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=os.environ["GROQ_API_KEY"],
    )

    

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )


async def create_authenticated_buyer_agent(jwt: str):
    """Run the same discovery flow as the CLI for an already logged-in buyer."""
    merchant_url = os.environ["MERCHANT_API_URL"]
    profile = await discover_merchant(merchant_url)
    mcp_endpoint = get_mcp_endpoint(profile)
    tools = await get_mcp_tools(mcp_endpoint, jwt)
    return create_buyer_agent(tools), mcp_endpoint, [tool.name for tool in tools]
