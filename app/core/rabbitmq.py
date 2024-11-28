import time
import pika
from pika.exceptions import AMQPConnectionError
import json
from loguru import logger


class RabbitMQ:
    _connection = None
    _channel = None

    @staticmethod
    def get_channel():
        if RabbitMQ._channel is None or RabbitMQ._channel.is_closed:
            for attempt in range(5):
                try:
                    connection = pika.BlockingConnection(
                        pika.ConnectionParameters(host="rabbitmq")
                    )
                    RabbitMQ._channel = connection.channel()
                    break
                except AMQPConnectionError as e:
                    logger.error("Connection attempt %d/5 failed: %s", attempt + 1, str(e))
                    if attempt < 4:
                        time.sleep(5)  # Retry delay
                    else:
                        raise
        return RabbitMQ._channel

    @staticmethod
    def setup_queue(channel, exchange, queue, routing_key, dlq=None, retry_queue=None, retry_ttl=None):
        """
        Configura uma fila com suporte a retry e DLQ.

        Args:
            channel: Canal do RabbitMQ.
            exchange: Nome da exchange.
            queue: Nome da fila principal.
            routing_key: Routing key para a fila principal.
            dlq: Nome da Dead Letter Queue.
            retry_queue: Nome da Retry Queue.
            retry_ttl: Tempo de retry em milissegundos (opcional).
        """
        channel.exchange_declare(exchange=exchange, exchange_type="direct", durable=True)

        if dlq:
            channel.queue_declare(queue=dlq, durable=True)
            channel.queue_bind(exchange=exchange, queue=dlq, routing_key=f"{routing_key}.dlq")

        if retry_queue:
            channel.queue_declare(queue=retry_queue, durable=True, arguments={
                "x-message-ttl": retry_ttl,
                "x-dead-letter-exchange": exchange,
                "x-dead-letter-routing-key": routing_key,
            })
            channel.queue_bind(exchange=exchange, queue=retry_queue, routing_key=f"{routing_key}.retry")

        channel.queue_declare(queue=queue, durable=True, arguments={
            "x-dead-letter-exchange": exchange,
            "x-dead-letter-routing-key": f"{routing_key}.retry",
        })
        channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)

        logger.info(f"Queue setup completed: {queue}")

    @staticmethod
    def publish_to_queue(exchange, routing_key, message):
        """
        Publica uma mensagem em uma fila através de uma exchange.

        Args:
            exchange: Nome da exchange.
            routing_key: Routing key para a fila.
            message: Mensagem a ser publicada (dict ou str).
        """
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
            channel = connection.channel()

            if not isinstance(message, (str, bytes)):
                message = json.dumps(message)

            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"Message published to {exchange}:{routing_key} | Message: {message}")
            connection.close()
        except Exception as e:
            logger.error(f"Failed to publish message to {exchange}:{routing_key} | Error: {e}")
            raise
