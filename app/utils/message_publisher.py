import aio_pika
import json
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from datetime import datetime, date
from uuid import UUID
from loguru import logger


class MessagePublisher:
    """
    Serviço dedicado para publicar mensagens no RabbitMQ.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        self.connection_params = connection_params

    async def publish(self, exchange: str, routing_key: str, message: dict):
        """
        Publica uma mensagem no RabbitMQ.

        Args:
            exchange (str): Nome da exchange.
            routing_key (str): Chave de roteamento.
            message (dict): Mensagem a ser publicada.
        """
        connection = await self.connection_params.get_connection()
        async with connection:
            channel = await connection.channel()
            exchange_instance = await channel.get_exchange(exchange)

            try:
                # Serializa a mensagem com tratamento de datetime
                message_body = json.dumps(message, default=self._json_serializer)
                await exchange_instance.publish(
                    aio_pika.Message(
                        body=message_body.encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key=routing_key,
                )
                logger.info(f"Message published to exchange '{exchange}' with routing key '{routing_key}'")
            except Exception as e:
                logger.error(f"Failed to publish message to exchange '{exchange}': {e}")
                raise

    @staticmethod
    def _json_serializer(obj):
        """
        Serializador customizado para lidar com tipos não suportados pelo JSON, como datetime e UUID.
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()  # Converte datetime para string no formato ISO
        if isinstance(obj, UUID):
            return str(obj)  # Converte UUID para string
        raise TypeError(f"Type {type(obj)} not serializable")
