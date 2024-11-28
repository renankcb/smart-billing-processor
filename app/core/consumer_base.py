import pika
import logging
from app.core.rabbitmq import RabbitMQ

logger = logging.getLogger(__name__)


class ConsumerBase:
    def __init__(self, queue_name, exchange_name, routing_key, dlq_name=None, retry_queue_name=None):
        """
        Inicializa o consumidor com configurações padrão.

        Args:
            queue_name (str): Nome da fila principal.
            exchange_name (str): Nome da exchange.
            routing_key (str): Routing key para a fila principal.
            dlq_name (str): Nome da Dead Letter Queue (DLQ).
            retry_queue_name (str): Nome da fila de retry.
        """
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.dlq_name = dlq_name or f"{queue_name}_dlq"
        self.retry_queue_name = retry_queue_name or f"{queue_name}_retry"

    def get_channel(self):
        """
        Obtém um canal de conexão ao RabbitMQ.

        Returns:
            BlockingChannel: Canal de conexão ao RabbitMQ.
        """
        return RabbitMQ.get_channel()

    def setup_queue(self):
        """
        Configura a fila, exchange, retry e DLQ associadas.

        Args:
            channel (BlockingChannel): Canal do RabbitMQ.
        """
        logger.info(f"Setting up queue {self.queue_name} with retry and DLQ...")

        channel = RabbitMQ.get_channel()

        # Configurar DLQ
        channel.queue_declare(queue=self.dlq_name, durable=True)
        logger.info(f"DLQ {self.dlq_name} created.")

        # Configurar fila de retry
        retry_arguments = {
            "x-dead-letter-exchange": self.exchange_name,
            "x-dead-letter-routing-key": self.routing_key,
            "x-message-ttl": 10000,  # Tempo de vida (em ms) para retry
        }
        channel.queue_declare(queue=self.retry_queue_name, durable=True, arguments=retry_arguments)
        logger.info(f"Retry queue {self.retry_queue_name} created.")

        # Configurar exchange
        channel.exchange_declare(exchange=self.exchange_name, exchange_type="direct", durable=True)
        logger.info(f"Exchange {self.exchange_name} created.")

        # Configurar fila principal com política de DLQ
        main_arguments = {
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": self.dlq_name,
        }
        channel.queue_declare(queue=self.queue_name, durable=True, arguments=main_arguments)
        logger.info(f"Queue {self.queue_name} created.")

        # Associar fila à exchange
        channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=self.routing_key)
        logger.info(f"Queue {self.queue_name} bound to exchange {self.exchange_name} with routing key {self.routing_key}.")

    def start_consuming(self):
        """
        Inicia o consumo das mensagens na fila.

        Args:
            channel (BlockingChannel): Canal do RabbitMQ.
        """
        channel = RabbitMQ.get_channel()

        logger.info(f"Starting to consume from queue {self.queue_name}...")
        channel.basic_consume(queue=self.queue_name, on_message_callback=self.process_message)
        channel.start_consuming()

    def process_message(self, channel, method, properties, body):
        """
        Deve ser implementado pelas subclasses para processar mensagens.

        Args:
            channel (BlockingChannel): Canal do RabbitMQ.
            method (Basic.Deliver): Método de entrega.
            properties (BasicProperties): Propriedades da mensagem.
            body (bytes): Corpo da mensagem.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def handle_failure(self, channel, method, body):
        """
        Envia a mensagem para a fila de retry ou a DLQ após falhas.

        Args:
            channel (BlockingChannel): Canal do RabbitMQ.
            method (Basic.Deliver): Método de entrega.
            body (bytes): Corpo da mensagem.
        """
        retries = method.headers.get("x-retries", 0)
        if retries < 2:
            headers = {"x-retries": retries + 1}
            channel.basic_publish(
                exchange="",
                routing_key=self.retry_queue_name,
                body=body,
                properties=pika.BasicProperties(headers=headers),
            )
            logger.warning(f"Retrying message. Attempt {retries + 1}.")
        else:
            channel.basic_publish(
                exchange="",
                routing_key=self.dlq_name,
                body=body,
            )
            logger.error(f"Message sent to DLQ after {retries + 1} attempts.")

        channel.basic_ack(delivery_tag=method.delivery_tag)
