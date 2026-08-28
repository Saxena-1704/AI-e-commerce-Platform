from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: Decimal
    quantity: int
    total_amount: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int

    subtotal: Decimal
    discount_amount: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    status: str

    items: list[OrderItemResponse]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True