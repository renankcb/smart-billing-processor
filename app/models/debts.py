from sqlalchemy import Column, Integer, Index, Numeric, Date, UUID, ForeignKey, TIMESTAMP, DateTime, func
from app.core.database import Base

class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Para rastreamento
    debt_amount = Column(Numeric(10, 2), nullable=False)
    debt_due_date = Column(DateTime, nullable=False)  # Alterado de Date para DateTime para maior precisão
    debt_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("idx_user_debt", "user_id", "debt_id"),  # Índice composto para buscas rápidas
    )