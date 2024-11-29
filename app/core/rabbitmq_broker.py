import pika
import json
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.core.message_broker import MessageBroker


class RabbitMQBroker(MessageBroker):
    """
    Implementação da interface MessageBroker para RabbitMQ.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        self.connection_params = connection_params

    def publish_to_queue(self, exchange: str, routing_key: str, message: dict):
        """
        Publica uma mensagem em uma fila do RabbitMQ.

        Args:
            exchange (str): Nome da exchange.
            routing_key (str): Chave de roteamento para a fila.
            message (Dict): Mensagem a ser publicada.
        """
        connection = pika.BlockingConnection(self.connection_params.get_connection())
        channel = connection.channel()

        # Declaração da exchange para garantir que ela exista
        # channel.exchange_declare(exchange=exchange, exchange_type="direct", durable=True)

        # Publicação da mensagem
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),  # Tornar a mensagem persistente
        )
        connection.close()
