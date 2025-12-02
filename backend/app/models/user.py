"""User model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from app.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    # Fix relationship — points back correctly
    organization = relationship("Organization", back_populates="users")

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt (truncate >72 bytes)."""
        safe = password[:72]
        return pwd_context.hash(safe)

    def verify_password(self, password: str) -> bool:
        safe = password[:72]
        return pwd_context.verify(safe, self.hashed_password)
