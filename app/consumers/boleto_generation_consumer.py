from loguru import logger
from app.consumers.base_consumer import BaseConsumer
from app.services.boleto_service import BoletoService
from app.core.database import async_session_factory
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams

class BoletoGenerationConsumer(BaseConsumer):
    """
    Consumidor responsável pela geração de boletos.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        super().__init__(
            queue_name="boleto_generation_queue",
            exchange_name="boleto_exchange",
            routing_key="boleto.generate",
            connection_params=connection_params,
        )
        self.boleto_service = BoletoService(session_factory=async_session_factory)

    async def process_message(self, message: dict):
        """
        Processa a mensagem para gerar boletos.

        Args:
            message (dict): Mensagem contendo informações da dívida e do usuário.
        """
        try:
            user_id = message.get("user_id")
            debt_id = message.get("debt_id")

            if not user_id or not debt_id:
                raise ValueError("Message missing required fields: 'user_id' or 'debt_id'.")

            logger.info(f"Generating boleto for User ID: {user_id}, Debt ID: {debt_id}")

            await self.boleto_service.generate_boleto(user_id=user_id, debt_id=debt_id)

        except Exception as e:
            logger.error(f"Error generating boleto: {e}")
            raise
