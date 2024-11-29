from loguru import logger
from app.repositories.user_repository import UserRepository
from app.repositories.debt_repository import DebtRepository
from app.schemas.chunk import ChunkRow
from typing import List
from uuid import UUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class ChunkProcessingService:
    """
    Serviço responsável por processar e armazenar chunks de usuários e dívidas.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def process_chunk(self, file_id: UUID, chunk: List[dict]):
        """
        Processa um chunk de dados e insere no banco.

        Args:
            file_id (UUID): ID do arquivo que originou os chunks.
            chunk (List[dict]): Chunk contendo os dados validados.
        """
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    user_repo = UserRepository(session)
                    debt_repo = DebtRepository(session)

                    # Validar e mapear dados
                    valid_rows = []
                    invalid_rows = []

                    for row in chunk:
                        try:
                            validated_row = ChunkRow(**row)
                            valid_rows.append(validated_row)
                        except Exception as e:
                            logger.error(f"Invalid row: {row} - {e}")
                            invalid_rows.append(row)

                    if invalid_rows:
                        logger.warning(f"{len(invalid_rows)} invalid rows detected and skipped.")

                    if not valid_rows:
                        logger.warning("No valid rows to process in this chunk.")
                        return

                    # Mapear usuários
                    users = {
                        row.governmentId: {
                            "id": row.governmentId,
                            "name": row.name,
                            "government_id": row.governmentId,
                            "email": row.email
                        }
                        for row in valid_rows
                    }

                    # Mapear dívidas
                    debts = [
                        {
                            "file_id": file_id,
                            "user_id": row.governmentId,
                            "debt_amount": row.debtAmount,
                            "debt_due_date": row.debtDueDate,
                            "debt_id": row.debtId
                        }
                        for row in valid_rows
                    ]

                    # Inserir usuários com ON CONFLICT DO NOTHING
                    try:
                        await user_repo.insert_users(list(users.values()))
                        logger.info("Users inserted successfully with conflict handling.")
                    except IntegrityError as ie:
                        logger.error(f"Integrity error while inserting users: {ie}")
                        raise

                    # Inserir dívidas com ON CONFLICT DO NOTHING
                    try:
                        await debt_repo.insert_debts(debts)
                        logger.info("Debts inserted successfully with conflict handling.")
                    except IntegrityError as ie:
                        logger.error(f"Integrity error while inserting debts: {ie}")
                        raise

                    logger.info(f"Chunk with {len(valid_rows)} valid rows processed successfully.")
        except SQLAlchemyError as sae:
            logger.error(f"Database error while processing chunk: {sae}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while processing chunk: {e}")
            raise