import asyncio

from .agent import create_merchant_agent


async def main():

    agent = await create_merchant_agent()

    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Show me all payments and summarize successful versus failed payments.",
                }
            ]
        }
    )

    final_response = response["messages"][-1].content

    print("\n================ FINAL RESPONSE ================\n")
    print(final_response)


if __name__ == "__main__":
    asyncio.run(main())