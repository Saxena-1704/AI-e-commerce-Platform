import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.auth.security import get_current_user, get_db
from backend.app.config import RAZORPAY_WEBHOOK_SECRET
from backend.app.models.order import Order
from backend.app.models.payment import Payment
from backend.app.models.payment_webhook_event import PaymentWebhookEvent
from backend.app.payment_gateway import razorpay_client
from backend.app.schemas.payment import PaymentVerifyRequest
from backend.app.services.payment_service import fail_payment, finalize_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


def payment_response(payment: Payment):
    return {"payment_id": payment.id, "order_id": payment.order_id,
            "razorpay_order_id": payment.provider_order_id, "amount": payment.amount,
            "currency": payment.currency, "razorpay_key_id": razorpay_client.auth[0]}


@router.post("/create/{order_id}", status_code=status.HTTP_201_CREATED)
def create_payment(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.expires_at and order.expires_at < datetime.utcnow():
        order.status = "cancelled"
        db.commit()
        raise HTTPException(status_code=409, detail="Order payment window has expired")
    if order.status not in ("pending_payment", "payment_failed"):
        raise HTTPException(status_code=409, detail="Order is not awaiting payment")
    if order.status == "payment_failed":
        order.status = "pending_payment"
        db.commit()
    existing = db.query(Payment).filter(Payment.order_id == order.id, Payment.status == "created").first()
    if existing:
        return payment_response(existing)
    attempt = (db.query(Payment).filter(Payment.order_id == order.id).count() or 0) + 1
    razorpay_order = razorpay_client.order.create({"amount": int(order.total_amount * 100), "currency": "INR", "receipt": order.order_number})
    payment = Payment(order_id=order.id, attempt_number=attempt, provider="razorpay",
                      provider_order_id=razorpay_order["id"], amount=order.total_amount,
                      currency="INR", status="created")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment_response(payment)


@router.post("/verify")
def verify_payment(payment_data: PaymentVerifyRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    payment = db.query(Payment).filter(Payment.provider_order_id == payment_data.razorpay_order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    order = db.query(Order).filter(Order.id == payment.order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if payment.status == "paid":
        return {"message": "Payment already verified", "payment_id": payment.id, "order_id": order.id, "status": "paid"}
    try:
        razorpay_client.utility.verify_payment_signature({"razorpay_order_id": payment_data.razorpay_order_id,
            "razorpay_payment_id": payment_data.razorpay_payment_id, "razorpay_signature": payment_data.razorpay_signature})
    except Exception as exc:
        fail_payment(db, payment)
        raise HTTPException(status_code=400, detail="Payment verification failed") from exc
    finalize_payment(db, payment, payment_data.razorpay_payment_id)
    return {"message": "Payment verified successfully", "payment_id": payment.id, "order_id": order.id, "status": "paid"}


@router.post("/fail/{order_id}")
def mark_payment_failed(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    payment = db.query(Payment).join(Order).filter(Payment.order_id == order_id, Order.user_id == current_user.id, Payment.status == "created").first()
    if payment:
        fail_payment(db, payment)
    else:
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
        if order and order.status == "pending_payment":
            order.status = "payment_failed"
            db.commit()
    return {"status": "payment_failed", "order_id": order_id}


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    event_id = request.headers.get("x-razorpay-event-id") or request.headers.get("X-Razorpay-Event-Id")
    if not RAZORPAY_WEBHOOK_SECRET or not signature or not event_id:
        raise HTTPException(status_code=400, detail="Invalid webhook headers")
    try:
        razorpay_client.utility.verify_webhook_signature(body.decode("utf-8"), signature, RAZORPAY_WEBHOOK_SECRET)
        payload = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature or payload") from exc
    if db.query(PaymentWebhookEvent).filter(PaymentWebhookEvent.event_id == event_id).first():
        return {"status": "already_processed"}
    event_type = payload.get("event", "")
    event_payload = payload.get("payload", {})
    entity = (event_payload.get("payment", {}).get("entity", {}) or
              event_payload.get("order", {}).get("entity", {}))
    provider_order_id = entity.get("order_id")
    payment = db.query(Payment).filter(Payment.provider_order_id == provider_order_id).first() if provider_order_id else None
    # Reserve the event ID before applying its side effect.  The unique
    # constraint makes duplicate delivery safe even when two requests race
    # past the existence check above.
    db.add(PaymentWebhookEvent(event_id=event_id, event_type=event_type))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"status": "already_processed"}
    if payment and event_type in ("payment.captured", "order.paid"):
        # `order.paid` contains a Razorpay order entity, not a payment entity.
        provider_payment_id = entity.get("id") if event_type == "payment.captured" else None
        finalize_payment(db, payment, provider_payment_id)
    elif payment and event_type == "payment.failed":
        fail_payment(db, payment)
    else:
        db.commit()
    return {"status": "processed"}
