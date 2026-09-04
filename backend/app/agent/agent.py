import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent

from .mcp_client import get_razorpay_tools
from .tools import get_merchant_api_tools
from .prompts import MERCHANT_AGENT_SYSTEM_PROMPT


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")


if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY must be set in the environment.")

if not GROQ_MODEL:
    raise ValueError("GROQ_MODEL must be set in the environment.")


async def create_merchant_agent(auth_token: str):

    razorpay_tools = await get_razorpay_tools()
    merchant_api_tools = get_merchant_api_tools(auth_token)

    selected_tool_names = {
        "fetch_all_orders",
        "fetch_order",
        "fetch_order_payments",
        "fetch_all_payments",
        "fetch_payment",
        "fetch_all_refunds",
        "fetch_refund",
        "fetch_specific_refund_for_payment",
        "fetch_all_settlements",
        "fetch_settlement_with_id",
        "fetch_settlement_recon_details",
    }

    selected_tools = [
        tool
        for tool in razorpay_tools
        if tool.name in selected_tool_names
    ]

    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
    )

    agent = create_agent(
        llm,
        [*selected_tools, *merchant_api_tools],
        system_prompt=MERCHANT_AGENT_SYSTEM_PROMPT,
    )

    return agent
