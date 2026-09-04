import secrets
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent import create_authenticated_buyer_agent
from app.auth import login_with_credentials


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "web"
app = FastAPI(title="ShopAI Customer Agent")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Demo-friendly, process-local sessions. Tokens never go to the browser.
sessions: dict[str, dict] = {}


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "customer-agent"}


@app.post("/api/login")
async def api_login(payload: LoginRequest, response: Response):
    try:
        jwt = await login_with_credentials(payload.email, payload.password)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid buyer login") from exc

    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {"jwt": jwt, "email": payload.email}
    response.set_cookie(
        "shopai_session",
        session_id,
        httponly=True,
        samesite="lax",
        max_age=3600,
    )
    return {"authenticated": True, "email": payload.email}


@app.post("/api/logout", status_code=status.HTTP_204_NO_CONTENT)
async def api_logout(response: Response, shopai_session: str | None = Cookie(default=None)):
    if shopai_session:
        sessions.pop(shopai_session, None)
    response.delete_cookie("shopai_session")


@app.post("/api/chat")
async def api_chat(payload: ChatRequest, shopai_session: str | None = Cookie(default=None)):
    session = sessions.get(shopai_session or "")
    if not session:
        raise HTTPException(status_code=401, detail="Log in as a buyer first")

    try:
        agent, endpoint, tool_names = await create_authenticated_buyer_agent(session["jwt"])
        result = await agent.ainvoke({"messages": [{"role": "user", "content": payload.message}]})
        content = result["messages"][-1].content
        if isinstance(content, list):
            content = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and isinstance(block.get("text"), str)
            ).strip()
        return {"response": content, "mcp_endpoint": endpoint, "tools": tool_names}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Customer agent is temporarily unavailable") from exc
