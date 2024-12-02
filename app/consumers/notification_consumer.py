from loguru import logger
from app.consumers.base_consumer import BaseConsumer
from app.services.notification_service import NotificationService
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams

class NotificationConsumer(BaseConsumer):
    """
    Consumidor responsável por notificar os usuários sobre boletos gerados.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        super().__init__(
            queue_name="notification_queue",
            exchange_name="notification_exchange",
            routing_key="notification.send",
            connection_params=connection_params,
        )
        self.notification_service = NotificationService()

    async def process_message(self, message: dict):
        """
        Processa a mensagem para notificar o usuário.

        Args:
            message (dict): Mensagem contendo informações do usuário e do boleto.
        """
        try:
            user_id = message.get("user_id")
            boleto_id = message.get("boleto_id")

            if not user_id or not boleto_id:
                raise ValueError("Message missing required fields: 'user_id' or 'boleto_id'.")

            logger.info(f"Notifying user {user_id} about boleto {boleto_id}")

            await self.notification_service.notify_user(user_id=user_id, boleto_id=boleto_id)

        except Exception as e:
            logger.error(f"Error notifying user: {e}")
            raise
