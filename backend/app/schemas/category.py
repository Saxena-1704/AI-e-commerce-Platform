from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CategoryCreate(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=100)
    url_slug: str = Field(..., min_length=1, max_length=120)
    parent_cat_id: Optional[int] = None


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100
    )

    url_slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=120
    )

    parent_cat_id: Optional[int] = None

    status: Optional[str] = Field(
        None,
        max_length=20
    )


class CategoryResponse(BaseModel):
    id: int
    category_name: str
    url_slug: str
    parent_cat_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True