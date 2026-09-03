from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.cart import Cart
from backend.app.models.cart_item import CartItem
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.order_item import OrderItem


def create_checkout(
    user_id: int,
    db: Session,
) -> dict:
    """
    Create a checkout session from the authenticated user's cart.

    Does NOT create an Order.
    """

    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.status.in_(["active", "checkout_pending"]),
        )
        .first()
    )

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    cart_items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    subtotal = Decimal("0.00")
    items = []

    for item in cart_items:

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found",
            )

        if product.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.product_name}' is not available",
            )

        if item.quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for '{product.product_name}'",
            )

        item_total = product.price * item.quantity
        subtotal += item_total

        items.append(
            {
                "product_id": product.id,
                "product_name": product.product_name,
                "quantity": item.quantity,
                "unit_price": product.price,
                "total": item_total,
            }
        )

    discount_amount = Decimal("0.00")
    shipping_amount = Decimal("0.00")
    tax_amount = Decimal("0.00")

    total_amount = (
        subtotal
        - discount_amount
        + shipping_amount
        + tax_amount
    )

    checkout_id = (
        f"CHK-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    )

    return {
    "checkout_id": checkout_id,
    "user_id": user_id,
    "status": "ready_for_complete",
    "items": items,
    "subtotal": subtotal,
    "discount_amount": discount_amount,
    "shipping_amount": shipping_amount,
    "tax_amount": tax_amount,
    "total_amount": total_amount,
    "expires_at": datetime.utcnow() + timedelta(minutes=30),
}


def complete_checkout(
    user_id: int,
    checkout: dict,
    db: Session,
) -> dict:
    """
    Complete checkout and create the Order.

    Payment is NOT processed here.
    """

    if checkout.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Checkout does not belong to this customer",
        )

    if checkout.get("status") != "ready_for_complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkout is not ready for completion",
        )

    # Check checkout expiry
    expires_at = checkout.get("expires_at")

    if expires_at and datetime.utcnow() > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkout session has expired",
        )

    # Get cart
    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.status.in_(["active", "checkout_pending"]),
        )
        .first()
    )

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    # Match the REST checkout behavior for a cart that is already locked by
    # an unpaid order: expire the old order and reopen the cart, or reuse the
    # still-valid pending order instead of creating a duplicate.
    if cart.status == "checkout_pending":
        pending = (
            db.query(Order)
            .filter(
                Order.user_id == user_id,
                Order.status == "pending_payment",
            )
            .order_by(Order.id.desc())
            .first()
        )

        if pending and pending.expires_at and pending.expires_at < datetime.utcnow():
            try:
                pending.status = "cancelled"
                cart.status = "active"
                db.commit()
            except SQLAlchemyError:
                db.rollback()
                raise
        elif pending:
            return {
                "checkout_id": checkout["checkout_id"],
                "checkout_status": "completed",
                "order": {
                    "id": pending.id,
                    "order_number": pending.order_number,
                    "user_id": pending.user_id,
                    "status": pending.status,
                    "subtotal": pending.subtotal,
                    "discount_amount": pending.discount_amount,
                    "shipping_amount": pending.shipping_amount,
                    "tax_amount": pending.tax_amount,
                    "total_amount": pending.total_amount,
                },
            }

    cart_items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    # Revalidate stock
    for item in cart_items:

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found",
            )

        if product.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.product_name}' is not available",
            )

        if item.quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for '{product.product_name}'",
            )

    # Generate required order number
    order_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"

    # Create order
    order = Order(
        order_number=order_number,
        user_id=user_id,
        subtotal=checkout["subtotal"],
        discount_amount=checkout["discount_amount"],
        shipping_amount=checkout["shipping_amount"],
        tax_amount=checkout["tax_amount"],
        total_amount=checkout["total_amount"],
        status="pending_payment",
        expires_at=checkout["expires_at"],
    )

    try:
        db.add(order)
        db.flush()

        # Create order items
        for item in cart_items:

            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.product_name,
                price=product.price,
                quantity=item.quantity,
                total_amount=product.price * item.quantity,
            )

            db.add(order_item)

        # Prevent the same cart from being reused
        cart.status = "checkout_pending"

        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(order)

    return {
        "checkout_id": checkout["checkout_id"],
        "checkout_status": "completed",
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "user_id": order.user_id,
            "status": order.status,
            "subtotal": order.subtotal,
            "discount_amount": order.discount_amount,
            "shipping_amount": order.shipping_amount,
            "tax_amount": order.tax_amount,
            "total_amount": order.total_amount,
        },
    }
