from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class PaymentResponse(BaseModel):
    id: int
    order_id: int

    provider: str
    provider_order_id: Optional[str]
    provider_payment_id: Optional[str]

    amount: Decimal
    currency: str

    status: str
    payment_method: Optional[str]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str        