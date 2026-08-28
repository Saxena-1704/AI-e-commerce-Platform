from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    category_name = Column(String(100), nullable=False)

    url_slug = Column(String(120), nullable=False, unique=True, index=True)

    parent_cat_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True
    )

    status = Column(
        String(20),
        nullable=False,
        default="active"
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        nullable=True
    )