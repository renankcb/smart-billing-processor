import aio_pika
import json
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from loguru import logger


class MessagePublisher:
    """
    Serviço dedicado para publicar mensagens no RabbitMQ.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        self.connection_params = connection_params

    async def publish(self, exchange: str, routing_key: str, message: dict):
        """
        Publica uma mensagem em uma exchange com uma routing key.

        Args:
            exchange (str): Nome da exchange.
            routing_key (str): Chave de roteamento para a fila.
            message (dict): Mensagem a ser publicada.
        """
        try:
            connection = await self.connection_params.get_connection()
            async with connection:
                channel = await connection.channel()

                # Obter a exchange existente (ou declare-a previamente na inicialização)
                current_exchange = await channel.get_exchange(exchange)

                # Publicar a mensagem
                await current_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(message).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # Tornar a mensagem persistente
                    ),
                    routing_key=routing_key,
                )
            logger.info(f"Message published to exchange '{exchange}' with routing key '{routing_key}'.")
        except Exception as e:
            logger.error(f"Failed to publish message to exchange '{exchange}': {e}")
            raise
