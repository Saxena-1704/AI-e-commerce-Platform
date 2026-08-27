from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    role_id = Column(
        Integer,
        ForeignKey("user_roles.id"),
        nullable=False
    )

    full_name = Column(String(150), nullable=False)

    email = Column(
        String(255),
        nullable=False,
        unique=True
    )

    password_hash = Column(String, nullable=False)

    phone_number = Column(String(20), nullable=True)

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