from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

class BoletoService:
    """
    Serviço responsável pela geração de boletos.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def generate_boleto(self, user_id: str, debt_id: str):
        """
        Gera um boleto para a dívida informada.

        Args:
            user_id (str): Identificador do usuário.
            debt_id (str): Identificador da dívida.
        """

        # Implementar aqui geraçao de boleto, armazenamento na tabela de boletos e envio para fila de notificaçao
        async with self.session_factory() as session:
            async with session.begin():
                logger.info(f"Boleto gerado para usuario: {user_id}, Debt ID: {debt_id}")
