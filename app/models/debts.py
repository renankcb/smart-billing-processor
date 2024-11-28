from sqlalchemy import Column, Integer, String, Numeric, Date, UUID, ForeignKey, TIMESTAMP
from app.core.database import Base
from datetime import datetime

class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    debt_amount = Column(Numeric(10, 2), nullable=False)
    debt_due_date = Column(Date, nullable=False)
    debt_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
