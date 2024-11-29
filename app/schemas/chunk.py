from pydantic import BaseModel, EmailStr
from datetime import date
from uuid import UUID
from typing import List


class ChunkRow(BaseModel):
    name: str
    governmentId: int  # Altere para corresponder ao cabeçalho do CSV
    email: EmailStr
    debtAmount: float  # Altere para corresponder ao cabeçalho do CSV
    debtDueDate: date  # Altere para corresponder ao cabeçalho do CSV
    debtId: UUID  # Altere para corresponder ao cabeçalho do CSV


class ChunkMessage(BaseModel):
    file_id: UUID
    chunk: List[ChunkRow]
