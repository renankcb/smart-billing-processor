from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    government_id = Column(Integer, unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())