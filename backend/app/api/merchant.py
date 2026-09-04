from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.auth.security import get_db, get_current_admin
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.payment import Payment
from backend.app.models.order_item import OrderItem
from backend.app.schemas.order import OrderResponse


router = APIRouter(
    prefix="/merchant",
    tags=["Merchant Dashboard"]
)


@router.get("/overview")
def get_merchant_overview(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    # Total active products
    total_products = (
        db.query(func.count(Product.id))
        .filter(Product.status == "active")
        .scalar()
    )

    # Low-stock products
    low_stock_products = (
        db.query(func.count(Product.id))
        .filter(
            Product.status == "active",
            Product.stock_quantity <= 5
        )
        .scalar()
    )

    # Total orders
    total_orders = (
        db.query(func.count(Order.id))
        .scalar()
    )

    # Revenue from successfully paid orders only
    revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.status == "paid")
        .scalar()
    )

    # Successful payments
    successful_payments = (
        db.query(func.count(Payment.id))
        .filter(Payment.status == "paid")
        .scalar()
    )

    # Failed payments
    failed_payments = (
        db.query(func.count(Payment.id))
        .filter(Payment.status == "failed")
        .scalar()
    )

    return {
        "revenue": float(revenue),
        "total_orders": total_orders,
        "total_products": total_products,
        "low_stock_products": low_stock_products,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments
    }



@router.get(
    "/orders",
    response_model=list[OrderResponse]
)
def get_all_orders(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    orders = (
        db.query(Order)
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