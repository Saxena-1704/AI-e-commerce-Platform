import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from backend.app.auth.security import get_current_admin


logger = logging.getLogger(__name__)


class MerchantAgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class MerchantAgentChatResponse(BaseModel):
    response: str


router = APIRouter(
    prefix="/merchant",
    tags=["Merchant Agent"],
)

security = HTTPBearer()


def _final_response_content(result) -> str:
    messages = result.get("messages") if isinstance(result, dict) else None
    if not messages:
        raise ValueError("Merchant agent returned no messages")

    content = messages[-1].content
    if isinstance(content, str):
        return content

    # LangChain may represent assistant content as content blocks. Convert
    # only the final response to text; never return the agent's message list
    # or tool outputs to the client.
    if isinstance(content, list):
        text_parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        ]
        response = "".join(text_parts).strip()
        if response:
            return response

    raise ValueError("Merchant agent returned an invalid final response")


@router.post(
    "/agent/chat",
    response_model=MerchantAgentChatResponse,
)
async def merchant_agent_chat(
    request: MerchantAgentChatRequest,
    current_admin=Depends(get_current_admin),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    del current_admin

    try:
        # Import lazily so agent-specific configuration or MCP availability
        # cannot prevent the rest of the API from starting.
        from backend.app.agent.agent import create_merchant_agent

        agent = await create_merchant_agent(credentials.credentials)
        result = await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": request.message}
                ]
            }
        )
        return {"response": _final_response_content(result)}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Merchant agent request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Merchant agent is temporarily unavailable",
        )
