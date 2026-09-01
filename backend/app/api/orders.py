from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta

from backend.app.auth.security import get_db
from backend.app.models.cart import Cart
from backend.app.models.cart_item import CartItem
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.order_item import OrderItem
from backend.app.schemas.order import OrderResponse
from backend.app.auth.security import get_current_user


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED
)
def checkout(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1. Get customer's cart
    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == current_user.id,
            Cart.status.in_(["active", "checkout_pending"])
        )
        .first()
    )

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )

    if cart.status == "checkout_pending":
        pending = db.query(Order).filter(Order.user_id == current_user.id, Order.status == "pending_payment").order_by(Order.id.desc()).first()
        if pending and pending.expires_at and pending.expires_at < datetime.utcnow():
            pending.status = "cancelled"
            cart.status = "active"
            db.commit()
        elif pending:
            pending.items = db.query(OrderItem).filter(OrderItem.order_id == pending.id).all()
            return pending

    # 2. Get cart items
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # 3. Validate products and calculate subtotal
    subtotal = Decimal("0.00")

    validated_items = []

    for item in cart_items:

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )

        if product.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.product_name}' is not available"
            )

        if item.quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for '{product.product_name}'"
            )

        item_total = product.price * item.quantity

        subtotal += item_total

        validated_items.append({
            "product": product,
            "quantity": item.quantity,
            "price": product.price,
            "total": item_total
        })

    # 4. Calculate order amounts
    discount_amount = Decimal("0.00")
    shipping_amount = Decimal("0.00")
    tax_amount = Decimal("0.00")

    total_amount = (
        subtotal
        - discount_amount
        + shipping_amount
        + tax_amount
    )

    # 5. Generate order number
    order_number = (
        f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    )

    # 6. Create order
    order = Order(
        order_number=order_number,
        user_id=current_user.id,
        subtotal=subtotal,
        discount_amount=discount_amount,
        shipping_amount=shipping_amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status="pending_payment",
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )

    db.add(order)
    db.flush()

    # 7. Create order items
    for item in validated_items:

        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product"].id,
            product_name=item["product"].product_name,
            price=item["price"],
            quantity=item["quantity"],
            total_amount=item["total"]
        )

        db.add(order_item)

    # Keep the cart intact and lock it until payment is finalized.
    cart.status = "checkout_pending"

    # 8. Commit the pending order and locked cart.
    db.commit()
    db.refresh(order)

    # 11. Load order items
    order.items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    return order



@router.get(
    "/",
    response_model=list[OrderResponse]
)
def get_my_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    for order in orders:
        order.items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id == order.id)
            .all()
        )

    return orders


@router.get(
    "/{order_id}",
    response_model=OrderResponse
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    order.items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    return order
