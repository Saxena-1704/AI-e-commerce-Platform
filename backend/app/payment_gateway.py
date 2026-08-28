import razorpay

from backend.app.config import (
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET
)


razorpay_client = razorpay.Client(
    auth=(
        RAZORPAY_KEY_ID,
        RAZORPAY_KEY_SECRET
    )
)