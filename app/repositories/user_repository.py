from sqlalchemy import select
from app.models.users import User
from typing import List
from sqlalchemy.dialects.postgresql import insert


class UserRepository:
    def __init__(self, session):
        self.session = session

    async def get_existing_users(self, user_ids):
        """Retorna IDs de usuários já existentes no banco."""
        query = select(User.id).where(User.id.in_(user_ids))
        result = await self.session.execute(query)
        return {row[0] for row in result}

    async def insert_users(self, users):
        """Insere usuários em lote."""
        if not users:
            return

        # Use o insert do dialect PostgreSQL
        stmt = insert(User).values(users)

        # Adicione a cláusula ON CONFLICT DO NOTHING
        stmt = stmt.on_conflict_do_nothing(index_elements=["government_id"])

        # Execute a query
        await self.session.execute(stmt)
