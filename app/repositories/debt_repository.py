from app.models.debts import Debt
from sqlalchemy.dialects.postgresql import insert


class DebtRepository:
    def __init__(self, session):
        self.session = session

    async def insert_debts(self, debts):
        """Insere dívidas em lote."""
        if not debts:
            return

        # Use o insert do dialect PostgreSQL
        stmt = insert(Debt).values(debts)

        # Adicione a cláusula ON CONFLICT DO NOTHING
        stmt = stmt.on_conflict_do_nothing(index_elements=["debt_id"])

        # Execute a query
        await self.session.execute(stmt)
