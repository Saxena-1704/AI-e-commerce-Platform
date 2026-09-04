from datetime import datetime

from fastapi import HTTPException

from backend.app.database import SessionLocal
from backend.app.models.order import Order
from backend.app.models.payment import Payment
from backend.app.payment_gateway import razorpay_client
from backend.app.mcp.auth import get_authenticated_user_id
from backend.app.config import FRONTEND_BASE_URL
from backend.app.payment_session import create_payment_session


def register_payment_tools(mcp):

    @mcp.tool()
    def create_payment(order_id: int) -> dict:
        """
        Create or reuse a payment for the authenticated user's order.

        Returns a browser payment URL that can be opened by the
        human using the Buyer Agent.
        """

        user_id = get_authenticated_user_id()

        db = SessionLocal()

        try:
            # =========================================================
            # Find and validate the order
            # =========================================================

            order = (
                db.query(Order)
                .filter(
                    Order.id == order_id,
                    Order.user_id == user_id,
                )
                .first()
            )

            if not order:
                raise HTTPException(
                    status_code=404,
                    detail="Order not found",
                )

            # =========================================================
            # Check payment expiry
            # =========================================================

            if order.expires_at:

                if order.expires_at < datetime.utcnow():

                    order.status = "cancelled"
                    db.commit()

                    raise HTTPException(
                        status_code=409,
                        detail="Order payment window has expired",
                    )

            # =========================================================
            # Validate order status
            # =========================================================

            if order.status not in (
                "pending_payment",
                "payment_failed",
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Order is not awaiting payment",
                )

            # =========================================================
            # Reset failed payment for a new attempt
            # =========================================================

            if order.status == "payment_failed":

                order.status = "pending_payment"
                db.commit()

            # =========================================================
            # Reuse an existing active payment
            # =========================================================

            existing = (
                db.query(Payment)
                .filter(
                    Payment.order_id == order.id,
                    Payment.status == "created",
                )
                .first()
            )

            if existing:

                # Create a short-lived browser payment session.
                session_token = create_payment_session(
                    payment_id=existing.id,
                    user_id=user_id,
                )

                # The token is placed in the URL fragment (#).
                # It is therefore not sent to the server as part
                # of the initial HTTP request.
                payment_url = (
                    f"{FRONTEND_BASE_URL.rstrip('/')}"
                    f"/payment.html"
                    f"?payment_id={existing.id}"
                    f"#payment_token={session_token}"
                )

                return {
                    "payment_id": existing.id,
                    "order_id": order.id,
                    "razorpay_order_id": existing.provider_order_id,
                    "amount": int(existing.amount * 100),
                    "currency": existing.currency,
                    "razorpay_key_id": razorpay_client.auth[0],
                    "status": "created",
                    "payment_url": payment_url,
                }

            # =========================================================
            # Calculate payment attempt number
            # =========================================================

            attempt = (
                db.query(Payment)
                .filter(
                    Payment.order_id == order.id
                )
                .count()
                + 1
            )

            # =========================================================
            # Create Razorpay order
            # =========================================================

            razorpay_order = razorpay_client.order.create(
                {
                    "amount": int(
                        order.total_amount * 100
                    ),
                    "currency": "INR",
                    "receipt": order.order_number,
                }
            )

            # =========================================================
            # Create internal payment record
            # =========================================================

            payment = Payment(
                order_id=order.id,
                attempt_number=attempt,
                provider="razorpay",
                provider_order_id=razorpay_order["id"],
                amount=order.total_amount,
                currency="INR",
                status="created",
            )

            db.add(payment)
            db.commit()
            db.refresh(payment)

            # =========================================================
            # Create browser payment session
            # =========================================================

            session_token = create_payment_session(
                payment_id=payment.id,
                user_id=user_id,
            )

            # =========================================================
            # Create payment URL
            # =========================================================

            payment_url = (
                f"{FRONTEND_BASE_URL.rstrip('/')}"
                f"/payment.html"
                f"?payment_id={payment.id}"
                f"#payment_token={session_token}"
            )

            # =========================================================
            # Return payment information to Buyer Agent
            # =========================================================

            return {
                "payment_id": payment.id,
                "order_id": order.id,
                "razorpay_order_id": payment.provider_order_id,
                "amount": int(payment.amount * 100),
                "currency": payment.currency,
                "razorpay_key_id": razorpay_client.auth[0],
                "status": "created",
                "payment_url": payment_url,
            }

        finally:
            db.close()

    @mcp.tool()
    def get_payment_status(order_id: int) -> dict:
        """
        Get the authoritative payment status for the authenticated user's order.
        """

        user_id = get_authenticated_user_id()
        db = SessionLocal()

        try:
            payment = (
                db.query(Payment)
                .join(Order)
                .filter(
                    Order.id == order_id,
                    Order.user_id == user_id,
                )
                .order_by(Payment.id.desc())
                .first()
            )

            if not payment:
                raise HTTPException(
                    status_code=404,
                    detail="Payment not found for order",
                )

            verified = payment.status == "paid"
            if verified:
                message = "Payment completed successfully."
            elif payment.status == "created":
                message = "Payment is awaiting completion."
            elif payment.status == "failed":
                message = "Payment failed."
            else:
                message = f"Payment status: {payment.status}."

            return {
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "razorpay_order_id": payment.provider_order_id,
                "status": payment.status,
                "verified": verified,
                "message": message,
            }

        finally:
            db.close()
