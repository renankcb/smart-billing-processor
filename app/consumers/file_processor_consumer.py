from app.core.consumer_base import ConsumerBase
import logging

logger = logging.getLogger(__name__)


class FileProcessorConsumer(ConsumerBase):
    def __init__(self):
        super().__init__(
            queue_name="file_processing_queue",
            exchange_name="file_processing_exchange",
            routing_key="file_processing_key",
        )

    def setup_and_initialize(self):
        """
        Configura e inicializa o consumidor.
        """
        try:
            logger.info("Initializing FileProcessorConsumer...")
            self.setup_queue()
            self.start_consuming()
        except Exception as e:
            logger.error(f"Error initializing FileProcessorConsumer: {e}")
            raise

    def process_message(self, channel, method, properties, body):
        """
        Processa a mensagem recebida da fila.

        Args:
            channel (BlockingChannel): Canal do RabbitMQ.
            method (Basic.Deliver): Método de entrega do RabbitMQ.
            properties (BasicProperties): Propriedades da mensagem.
            body (bytes): Corpo da mensagem.
        """
        try:
            logger.info(f"Processing message: {body.decode('utf-8')}")
            # Adicionar lógica de processamento aqui
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Message processed successfully.")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.handle_failure(channel, method, body)
