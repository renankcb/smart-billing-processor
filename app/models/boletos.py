from sqlalchemy import Column, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Boleto(Base):
    __tablename__ = "boletos"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    debt_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    generated_at = Column(TIMESTAMP, default=None)
    notified_at = Column(TIMESTAMP, default=None)