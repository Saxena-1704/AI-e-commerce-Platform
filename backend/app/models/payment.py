from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    provider = Column(
        String(50),
        nullable=False,
        default="razorpay"
    )

    provider_order_id = Column(
        String(100),
        nullable=True,
        unique=True
    )

    provider_payment_id = Column(
        String(100),
        nullable=True,
        unique=True
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    currency = Column(
        String(10),
        nullable=False,
        default="INR"
    )

    status = Column(
        String(30),
        nullable=False,
        default="created"
    )

    payment_method = Column(
        String(50),
        nullable=True
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