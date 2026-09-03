from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.cart import Cart
from backend.app.models.cart_item import CartItem
from backend.app.models.product import Product
from backend.app.models.order import Order


def get_or_create_cart(user_id: int, db: Session) -> Cart:
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .first()
    )

    if not cart:
        cart = Cart(user_id=user_id, status="active")
        db.add(cart)
        db.commit()
        db.refresh(cart)

    return cart


def ensure_cart_editable(cart: Cart, db: Session):
    if cart.status != "checkout_pending":
        return

    pending = (
        db.query(Order)
        .filter(
            Order.user_id == cart.user_id,
            Order.status == "pending_payment"
        )
        .order_by(Order.id.desc())
        .first()
    )

    if (
        pending
        and pending.expires_at
        and pending.expires_at < datetime.utcnow()
    ):
        pending.status = "cancelled"
        cart.status = "active"
        db.commit()
        return

    raise HTTPException(
        status_code=409,
        detail="Cart is locked while payment is pending"
    )


def build_cart(cart: Cart, db: Session) -> dict:
    items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    result_items = []
    total = Decimal("0.00")

    for item in items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if not product:
            continue

        item_total = product.price * item.quantity
        total += item_total

        result_items.append({
            "id": item.id,
            "product_id": product.id,
            "product_name": product.product_name,
            "quantity": item.quantity,
            "unit_price": product.price,
            "total": item_total,
        })

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "status": cart.status,
        "items": result_items,
        "total": total,
    }


def add_item(
    user_id: int,
    product_id: int,
    quantity: int,
    db: Session,
) -> dict:

    cart = get_or_create_cart(user_id, db)
    ensure_cart_editable(cart, db)

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if product.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not available",
        )

    if quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock available",
        )

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
        .first()
    )

    if cart_item:
        new_quantity = cart_item.quantity + quantity

        if new_quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stock available",
            )

        cart_item.quantity = new_quantity

    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity,
        )
        db.add(cart_item)

    cart.updated_at = datetime.utcnow()

    db.commit()

    return build_cart(cart, db)


def update_item(
    user_id: int,
    item_id: int,
    quantity: int,
    db: Session,
) -> dict:

    cart = get_or_create_cart(user_id, db)
    ensure_cart_editable(cart, db)

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    product = (
        db.query(Product)
        .filter(Product.id == cart_item.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock available",
        )

    cart_item.quantity = quantity
    cart.updated_at = datetime.utcnow()

    db.commit()

    return build_cart(cart, db)


def remove_item(
    user_id: int,
    item_id: int,
    db: Session,
) -> dict:

    cart = get_or_create_cart(user_id, db)
    ensure_cart_editable(cart, db)

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    db.delete(cart_item)

    cart.updated_at = datetime.utcnow()

    db.commit()

    return build_cart(cart, db)


def get_cart(
    user_id: int,
    db: Session,
) -> dict:

    cart = get_or_create_cart(user_id, db)

    return build_cart(cart, db)