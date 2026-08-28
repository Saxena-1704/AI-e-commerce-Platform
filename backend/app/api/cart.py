from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from backend.app.auth.security import get_db
from backend.app.models.cart import Cart
from backend.app.models.cart_item import CartItem
from backend.app.models.product import Product
from backend.app.schemas.cart import (
    CartItemAdd,
    CartItemUpdate,
    CartResponse
)
from backend.app.auth.security import get_current_user


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


def get_or_create_cart(
    user_id: int,
    db: Session
):
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .first()
    )

    if not cart:
        cart = Cart(user_id=user_id)

        db.add(cart)
        db.commit()
        db.refresh(cart)

    return cart


def build_cart_response(
    cart: Cart,
    db: Session
):
    items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    total = Decimal("0.00")

    for item in items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if product:
            total += product.price * item.quantity

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "status": cart.status,
        "items": items,
        "total": total,
        "created_at": cart.created_at,
        "updated_at": cart.updated_at
    }


@router.get(
    "/",
    response_model=CartResponse
)
def get_cart(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    cart = get_or_create_cart(
        current_user.id,
        db
    )

    return build_cart_response(
        cart,
        db
    )


@router.post(
    "/items",
    response_model=CartResponse
)
def add_to_cart(
    item_data: CartItemAdd,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    cart = get_or_create_cart(
        current_user.id,
        db
    )

    # Check that product exists
    product = (
        db.query(Product)
        .filter(Product.id == item_data.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check product is active
    if product.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not available"
        )

    # Check stock
    if item_data.quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock available"
        )

    # Check if product already exists in cart
    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id
        )
        .first()
    )

    if cart_item:
        new_quantity = cart_item.quantity + item_data.quantity

        if new_quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stock available"
            )

        cart_item.quantity = new_quantity

    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity
        )

        db.add(cart_item)

    db.commit()

    return build_cart_response(
        cart,
        db
    )


@router.put(
    "/items/{item_id}",
    response_model=CartResponse
)
def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    cart = get_or_create_cart(
        current_user.id,
        db
    )

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    product = (
        db.query(Product)
        .filter(Product.id == cart_item.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if item_data.quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock available"
        )

    cart_item.quantity = item_data.quantity

    db.commit()

    return build_cart_response(
        cart,
        db
    )


@router.delete(
    "/items/{item_id}",
    response_model=CartResponse
)
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    cart = get_or_create_cart(
        current_user.id,
        db
    )

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    db.delete(cart_item)
    db.commit()

    return build_cart_response(
        cart,
        db
    )