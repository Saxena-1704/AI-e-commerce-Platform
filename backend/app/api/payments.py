from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.security import get_db
from backend.app.models.order import Order
from backend.app.models.payment import Payment
from backend.app.auth.security import get_current_user
from backend.app.payment_gateway import razorpay_client
from backend.app.schemas.payment import PaymentVerifyRequest


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post(
    "/create/{order_id}",
    status_code=status.HTTP_201_CREATED
)
def create_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # 1. Find the customer's order
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

    # 2. Check whether payment already exists
    existing_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .first()
    )

    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already created for this order"
        )

    # 3. Convert rupees → paise
    amount_in_paise = int(order.total_amount * 100)

    # 4. Create Razorpay order
    razorpay_order = razorpay_client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": order.order_number
    })

    # 5. Save payment in our database
    payment = Payment(
        order_id=order.id,
        provider="razorpay",
        provider_order_id=razorpay_order["id"],
        amount=order.total_amount,
        currency="INR",
        status="created"
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    # 6. Return information needed by frontend
    return {
        "payment_id": payment.id,
        "order_id": order.id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": order.total_amount,
        "currency": "INR",
        "razorpay_key_id": razorpay_client.auth[0]
    }


@router.post("/verify")
def verify_payment(
    payment_data: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # 1. Find our payment using Razorpay Order ID
    payment = (
        db.query(Payment)
        .filter(
            Payment.provider_order_id == payment_data.razorpay_order_id
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # 2. Find the associated order
    order = (
        db.query(Order)
        .filter(
            Order.id == payment.order_id,
            Order.user_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # 3. Verify Razorpay signature
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": payment_data.razorpay_order_id,
            "razorpay_payment_id": payment_data.razorpay_payment_id,
            "razorpay_signature": payment_data.razorpay_signature
        })

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed"
        )

    # 4. Update our payment
    payment.provider_payment_id = payment_data.razorpay_payment_id
    payment.status = "paid"

    # 5. Update our order
    order.status = "paid"

    db.commit()
    db.refresh(payment)

    return {
        "message": "Payment verified successfully",
        "payment_id": payment.id,
        "order_id": order.id,
        "status": payment.status
    }