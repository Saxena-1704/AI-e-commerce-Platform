from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from backend.app.database import Base


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(150), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
