from backend.app.database import SessionLocal

from backend.app.services.checkout_service import (
    create_checkout as create_checkout_service,
    complete_checkout as complete_checkout_service,
)

from backend.app.mcp.auth import get_authenticated_user_id


_checkout_sessions = {}


def register_checkout_tools(mcp):

    @mcp.tool()
    def create_checkout() -> dict:

        user_id = get_authenticated_user_id()

        db = SessionLocal()

        try:
            result = create_checkout_service(
                user_id=user_id,
                db=db,
            )

            result["user_id"] = user_id

            _checkout_sessions[result["checkout_id"]] = result

            return result

        finally:
            db.close()

    @mcp.tool()
    def complete_checkout(checkout_id: str) -> dict:

        user_id = get_authenticated_user_id()

        checkout = _checkout_sessions.get(checkout_id)

        if not checkout:
            raise ValueError(
                "Checkout session not found or expired."
            )

        db = SessionLocal()

        try:
            result = complete_checkout_service(
                user_id=user_id,
                checkout=checkout,
                db=db,
            )

            _checkout_sessions.pop(checkout_id, None)

            return result

        finally:
            db.close()