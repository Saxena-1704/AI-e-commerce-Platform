from backend.app.database import SessionLocal
from backend.app.services.cart_service import (
    get_cart,
    add_item,
    update_item,
    remove_item,
)
from backend.app.mcp.auth import get_authenticated_user_id


def register_cart_tools(mcp):

    @mcp.tool()
    def get_customer_cart() -> dict:
        """
        Get the current customer's shopping cart.
        """

        db = SessionLocal()

        try:
            return get_cart(
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
            return add_item(
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
            return update_item(
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
            return remove_item(
                user_id=get_authenticated_user_id(),
                item_id=item_id,
                db=db,
            )
        finally:
            db.close()
