import aio_pika
import json
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams


class RabbitMQBroker:
    """
    Implementação do broker para RabbitMQ com aio_pika.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        self.connection_params = connection_params

    async def publish_to_queue(self, exchange: str, routing_key: str, message: dict):
        """
        Publica uma mensagem em uma fila do RabbitMQ.

        Args:
            exchange (str): Nome da exchange.
            routing_key (str): Chave de roteamento para a fila.
            message (dict): Mensagem a ser publicada.
        """
        connection = await self.connection_params.get_connection()
        async with connection:
            channel = await connection.channel()

            # Declaração da exchange para garantir que ela exista
            # await channel.declare_exchange(exchange, aio_pika.ExchangeType.DIRECT, durable=True)

            # Publicação da mensagem
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # Tornar a mensagem persistente
                ),
                routing_key=routing_key,
            )
