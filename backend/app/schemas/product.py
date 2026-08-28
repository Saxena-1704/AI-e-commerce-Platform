from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class ProductCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)

    url_slug: str = Field(..., min_length=1, max_length=220)

    category_id: int = Field(..., gt=0)

    description: Optional[str] = None

    price: Decimal = Field(..., ge=0)

    stock_quantity: int = Field(..., ge=0)


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200
    )

    url_slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=220
    )

    category_id: Optional[int] = Field(
        None,
        gt=0
    )

    description: Optional[str] = None

    price: Optional[Decimal] = Field(
        None,
        ge=0
    )

    stock_quantity: Optional[int] = Field(
        None,
        ge=0
    )

    status: Optional[str] = Field(
        None,
        max_length=20
    )


class ProductResponse(BaseModel):
    id: int
    product_name: str
    url_slug: str
    category_id: int
    description: Optional[str]
    price: Decimal
    stock_quantity: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True