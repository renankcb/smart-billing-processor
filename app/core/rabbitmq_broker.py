import aio_pika
import json
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.utils.message_publisher import MessagePublisher


class RabbitMQBroker:
    """
    Implementação do broker para RabbitMQ com aio_pika.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        self.publisher = MessagePublisher(connection_params)

    async def publish_to_queue(self, exchange: str, routing_key: str, message: dict):
        """
        Publica uma mensagem em uma fila do RabbitMQ.

        Args:
            exchange (str): Nome da exchange.
            routing_key (str): Chave de roteamento para a fila.
            message (dict): Mensagem a ser publicada.
        """
        await self.publisher.publish(exchange, routing_key, message)
