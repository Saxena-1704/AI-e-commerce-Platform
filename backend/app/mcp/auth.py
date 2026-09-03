from contextvars import ContextVar

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.auth.security import get_current_user
from backend.app.database import SessionLocal


_authenticated_user_id: ContextVar[int | None] = ContextVar(
    "mcp_authenticated_user_id",
    default=None,
)


def get_authenticated_user_id() -> int:
    user_id = _authenticated_user_id.get()
    if user_id is None:
        raise RuntimeError("No authenticated MCP user")
    return user_id


class MCPAuthMiddleware:
    """Validate the existing application JWT before handling MCP requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope["headers"]}
        authorization = headers.get(b"authorization", b"").decode("latin-1")
        scheme, _, token = authorization.partition(" ")

        if scheme.lower() != "bearer" or not token:
            await JSONResponse(
                {"detail": "Not authenticated"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )(scope, receive, send)
            return

        db = SessionLocal()
        try:
            user = get_current_user(
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=token,
                ),
                db=db,
            )
        except HTTPException as exc:
            await JSONResponse(
                {"detail": exc.detail},
                status_code=exc.status_code,
                headers={"WWW-Authenticate": "Bearer"},
            )(scope, receive, send)
            return
        finally:
            db.close()

        reset = _authenticated_user_id.set(user.id)
        try:
            await self.app(scope, receive, send)
        finally:
            _authenticated_user_id.reset(reset)
