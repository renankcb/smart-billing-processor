import pika
import json
import logging
from app.services.file_processor_service import FileProcessorService
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.consumers.base_consumer import BaseConsumer

logging.basicConfig(level=logging.INFO)


class FileProcessingConsumer(BaseConsumer):
    """
    Consumidor responsável por processar mensagens de arquivos prontos e dividi-los em chunks.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        super().__init__(
            queue_name="file_processing_queue",
            exchange_name="file_exchange",
            routing_key="file.process",
            connection_params=connection_params,
        )
        self.file_processor_service = FileProcessorService()

    def process_message(self, message: dict):
        """
        Processa a mensagem para dividir o arquivo em chunks.

        Args:
            message (dict): Mensagem contendo informações do arquivo.
        """
        file_id = message.get("file_id")
        file_path = message.get("file_path")

        logging.info(f"### Processing file {file_path} with ID {file_id}")

        try:
            chunks = self.file_processor_service.process_file(file_path)
            self.publish_chunks(file_id, chunks)

        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
            raise

    def publish_chunks(self, file_id: str, chunks):
        """
        Publica os chunks gerados na fila `chunk_processing_queue`.

        Args:
            file_id (str): Identificador do arquivo original.
            chunks (iterable): Chunks gerados pelo serviço de processamento.
        """
        connection = pika.BlockingConnection(self.connection_params.get_connection())
        channel = connection.channel()

        # Declaração da fila para garantir existência
        # channel.exchange_declare(exchange="chunk_exchange", exchange_type="direct", durable=True)
        # channel.queue_declare(queue="chunk_processing_queue", durable=True)

        for chunk in chunks:
            message = {"file_id": file_id, "chunk": chunk}
            channel.basic_publish(
                exchange="chunk_exchange",
                routing_key="chunk.process",
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),  # Persistência
            )
        connection.close()
        logging.info(f"Chunks for file {file_id} enqueued successfully.")
