from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.cart import Cart
from backend.app.models.cart_item import CartItem
from backend.app.models.order import Order
from backend.app.models.order_item import OrderItem
from backend.app.models.payment import Payment
from backend.app.models.product import Product


def finalize_payment(db: Session, payment: Payment, provider_payment_id: str | None = None):
    order = db.query(Order).filter(Order.id == payment.order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if payment.status == "paid":
        # This also commits a freshly-reserved webhook event when a distinct
        # successful event (for example, order.paid after payment.captured)
        # arrives after the payment was already finalized.
        db.commit()
        return order
    if order.status == "paid":
        payment.status = "paid"
        payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
        db.commit()
        return order
    # A client-side verification failure is not proof that Razorpay did not
    # capture the payment.  A later captured webhook must still be able to
    # reconcile that payment and consume stock exactly once.
    if order.status not in ("pending_payment", "payment_failed"):
        raise HTTPException(status_code=409, detail="Order is not payable")

    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if not product or product.status != "active" or product.stock_quantity < item.quantity:
            raise HTTPException(status_code=409, detail=f"Insufficient stock for '{item.product_name}'")
        product.stock_quantity -= item.quantity

    cart = db.query(Cart).filter(Cart.user_id == order.user_id).with_for_update().first()
    if cart:
        for cart_item in db.query(CartItem).filter(CartItem.cart_id == cart.id).all():
            if any(i.product_id == cart_item.product_id and i.quantity == cart_item.quantity for i in items):
                db.delete(cart_item)
        cart.status = "active"

    payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
    payment.status = "paid"
    order.status = "paid"
    db.commit()
    db.refresh(order)
    return order


def fail_payment(db: Session, payment: Payment):
    if payment.status == "paid":
        return
    payment.status = "failed"
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if order and order.status == "pending_payment":
        order.status = "payment_failed"
        cart = db.query(Cart).filter(Cart.user_id == order.user_id).first()
        if cart:
            cart.status = "active"
    db.commit()
