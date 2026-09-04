from backend.app.database import SessionLocal

from backend.app.services.checkout_service import (
    create_checkout as create_checkout_service,
    complete_checkout as complete_checkout_service,
)

from backend.app.mcp.auth import get_authenticated_user_id


_checkout_sessions = {}


def _checkout_response(
    checkout: dict,
    status: str | None = None,
) -> dict:
    return {
        "ucp": {
            "version": "2026-08-25",
            "capabilities": {
                "dev.ucp.shopping.checkout": [
                    {
                        "version": "2026-08-25"
                    }
                ]
            },
            "payment_handlers": {},
        },

        "id": checkout["checkout_id"],

        "status": status or checkout["status"],

        "currency": "INR",

        "line_items": [
            {
                "id": f"li_{item['product_id']}",

                "item": {
                    "id": str(item["product_id"]),
                    "title": item["product_name"],
                    "price": int(
                        item["unit_price"] * 100
                    ),
                },

                "quantity": item["quantity"],

                "totals": [
                    {
                        "type": "subtotal",
                        "amount": int(
                            item["total"] * 100
                        ),
                    },
                    {
                        "type": "total",
                        "amount": int(
                            item["total"] * 100
                        ),
                    },
                ],
            }

            for item in checkout["items"]
        ],

        "totals": [
            {
                "type": "subtotal",
                "amount": int(
                    checkout["subtotal"] * 100
                ),
            },
            {
                "type": "total",
                "amount": int(
                    checkout["total_amount"] * 100
                ),
            },
        ],

        "expires_at": (
            checkout["expires_at"].isoformat()
            + "Z"
        ),
    }


def register_checkout_tools(mcp):

    # ============================================================
    # CREATE CHECKOUT
    # ============================================================

    @mcp.tool()
    def create_checkout(
        checkout: dict,
        meta: dict | None = None,
    ) -> dict:
        """
        Create a UCP checkout session from the authenticated
        user's current cart.

        The checkout object is accepted for UCP compatibility.
        The actual cart is determined server-side.
        """

        user_id = get_authenticated_user_id()

        db = SessionLocal()

        try:

            result = create_checkout_service(
                user_id=user_id,
                db=db,
            )

            result["user_id"] = user_id

            _checkout_sessions[
                result["checkout_id"]
            ] = result

            return _checkout_response(
                result,
                "incomplete",
            )

        finally:
            db.close()


    # ============================================================
    # COMPLETE CHECKOUT
    # ============================================================

    @mcp.tool()
    def complete_checkout(
        id: str,
        checkout: dict,
        meta: dict | None = None,
    ) -> dict:
        """
        Complete an existing UCP checkout session.
        """

        user_id = get_authenticated_user_id()

        checkout_session = _checkout_sessions.get(id)

        if not checkout_session:
            raise ValueError(
                "Checkout session not found or expired."
            )

        db = SessionLocal()

        try:

            result = complete_checkout_service(
                user_id=user_id,
                checkout=checkout_session,
                db=db,
            )

            _checkout_sessions.pop(id, None)

            response = _checkout_response(
                checkout_session,
                "completed",
            )

            response["order"] = result["order"]

            return response

        finally:
            db.close()


    # ============================================================
    # GET CHECKOUT
    # ============================================================

    @mcp.tool()
    def get_checkout(
        id: str,
        meta: dict | None = None,
    ) -> dict:
        """
        Retrieve an existing checkout session.
        """

        checkout = _checkout_sessions.get(id)

        if not checkout:
            raise ValueError(
                "Checkout session not found or expired."
            )

        return _checkout_response(
            checkout,
            "incomplete",
        )


    # ============================================================
    # UPDATE CHECKOUT
    # ============================================================

    @mcp.tool()
    def update_checkout(
        id: str,
        checkout: dict,
        meta: dict | None = None,
    ) -> dict:
        """
        Update an existing checkout.

        Checkout updates are currently not supported because
        this checkout is backed directly by the authenticated
        user's cart.
        """

        current = _checkout_sessions.get(id)

        if not current:
            raise ValueError(
                "Checkout session not found or expired."
            )

        raise ValueError(
            "Checkout updates are not supported "
            "for this cart-backed checkout."
        )


    # ============================================================
    # CANCEL CHECKOUT
    # ============================================================

    @mcp.tool()
    def cancel_checkout(
        id: str,
        meta: dict | None = None,
    ) -> dict:
        """
        Cancel an existing checkout session.
        """

        checkout = _checkout_sessions.pop(
            id,
            None,
        )

        if not checkout:
            raise ValueError(
                "Checkout session not found or expired."
            )

        return _checkout_response(
            checkout,
            "canceled",
        )