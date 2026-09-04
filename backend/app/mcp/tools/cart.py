from backend.app.database import SessionLocal
from backend.app.services.cart_service import (
    get_cart as get_cart_service,
    add_item as add_item_service,
    update_item as update_item_service,
    remove_item as remove_item_service,
)
from backend.app.mcp.auth import get_authenticated_user_id


def register_cart_tools(mcp):

    def cart_response(cart: dict) -> dict:
        return {
            "ucp": {
                "version": "2026-08-25",
                "capabilities": {
                    "dev.ucp.shopping.cart": [{"version": "2026-08-25"}]
                },
                "payment_handlers": {},
            },
            "id": str(cart["id"]),
            "line_items": [
                {
                    "id": f"li_{item['id']}",
                    "item": {
                        "id": str(item["product_id"]),
                        "title": item["product_name"],
                        "price": int(item["unit_price"] * 100),
                    },
                    "quantity": item["quantity"],
                    "totals": [
                        {"type": "subtotal", "amount": int(item["total"] * 100)},
                        {"type": "total", "amount": int(item["total"] * 100)},
                    ],
                }
                for item in cart["items"]
            ],
            "currency": "INR",
            "totals": [{"type": "total", "amount": int(cart["total"] * 100)}],
        }

    @mcp.tool()
    def create_cart(meta: dict, cart: dict) -> dict:
        user_id = get_authenticated_user_id()
        db = SessionLocal()
        try:
            for line_item in cart.get("line_items", []):
                add_item_service(
                    user_id=user_id,
                    product_id=int(line_item["item"]["id"]),
                    quantity=line_item["quantity"],
                    db=db,
                )
            return cart_response(get_cart_service(user_id=user_id, db=db))
        finally:
            db.close()

    @mcp.tool()
    def get_cart(meta: dict, id: str) -> dict:
        db = SessionLocal()
        try:
            cart = get_cart_service(user_id=get_authenticated_user_id(), db=db)
            if str(cart["id"]) != id:
                raise ValueError("Cart not found.")
            return cart_response(cart)
        finally:
            db.close()

    @mcp.tool()
    def update_cart(meta: dict, id: str, cart: dict) -> dict:
        user_id = get_authenticated_user_id()
        db = SessionLocal()
        try:
            current = get_cart_service(user_id=user_id, db=db)
            if str(current["id"]) != id:
                raise ValueError("Cart not found.")
            for item in current["items"]:
                remove_item_service(user_id=user_id, item_id=item["id"], db=db)
            for line_item in cart.get("line_items", []):
                add_item_service(
                    user_id=user_id,
                    product_id=int(line_item["item"]["id"]),
                    quantity=line_item["quantity"],
                    db=db,
                )
            return cart_response(get_cart_service(user_id=user_id, db=db))
        finally:
            db.close()

    @mcp.tool()
    def cancel_cart(meta: dict, id: str) -> dict:
        user_id = get_authenticated_user_id()
        db = SessionLocal()
        try:
            current = get_cart_service(user_id=user_id, db=db)
            if str(current["id"]) != id:
                raise ValueError("Cart not found.")
            for item in current["items"]:
                remove_item_service(user_id=user_id, item_id=item["id"], db=db)
            response = cart_response(get_cart_service(user_id=user_id, db=db))
            response["status"] = "canceled"
            return response
        finally:
            db.close()

    @mcp.tool()
    def get_customer_cart() -> dict:
        """
        Get the current customer's shopping cart.
        """

        db = SessionLocal()

        try:
            return get_cart_service(
                user_id=get_authenticated_user_id(),
                db=db,
            )
        finally:
            db.close()

    @mcp.tool()
    def add_to_cart(
        product_id: int,
        quantity: int = 1,
    ) -> dict:
        """
        Add a product to the customer's shopping cart.
        """

        db = SessionLocal()

        try:
            return add_item_service(
                user_id=get_authenticated_user_id(),
                product_id=product_id,
                quantity=quantity,
                db=db,
            )
        finally:
            db.close()

    @mcp.tool()
    def update_cart_item(
        item_id: int,
        quantity: int,
    ) -> dict:
        """
        Update the quantity of an item in the customer's cart.
        """

        db = SessionLocal()

        try:
            return update_item_service(
                user_id=get_authenticated_user_id(),
                item_id=item_id,
                quantity=quantity,
                db=db,
            )
        finally:
            db.close()

    @mcp.tool()
    def remove_from_cart(
        item_id: int,
    ) -> dict:
        """
        Remove an item from the customer's cart.
        """

        db = SessionLocal()

        try:
            return remove_item_service(
                user_id=get_authenticated_user_id(),
                item_id=item_id,
                db=db,
            )
        finally:
            db.close()
