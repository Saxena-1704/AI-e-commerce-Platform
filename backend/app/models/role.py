from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from backend.app.database import Base


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True)