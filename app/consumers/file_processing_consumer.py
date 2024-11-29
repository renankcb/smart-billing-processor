from loguru import logger
from app.services.file_processor_service import FileProcessorService
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.consumers.base_consumer import BaseConsumer
from app.utils.message_publisher import MessagePublisher
from typing import List


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
        self.publisher = MessagePublisher(connection_params)

    async def process_message(self, message: dict):
        """
        Processa a mensagem para dividir o arquivo em chunks.

        Args:
            message (dict): Mensagem contendo informações do arquivo.
        """
        file_id = message.get("file_id")
        file_path = message.get("file_path")

        logger.info(f"Processing file {file_path} with ID {file_id}")

        try:
            chunks = self.file_processor_service.process_file(file_path)
            for chunk in chunks:
                await self.publish_chunks(file_id, chunk)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise

    async def publish_chunks(self, file_id: str, chunk: List[dict]):
        """
        Publica os chunks gerados na fila `chunk_processing_queue`.

        Args:
            file_id (str): Identificador do arquivo original.
            chunk (List[dict]): Chunk gerado pelo serviço de processamento.
        """
        message = {"file_id": file_id, "chunk": chunk}
        await self.publisher.publish(
            exchange="chunk_exchange",
            routing_key="chunk.process",
            message=message,
        )
        logger.info(f"Chunk with {len(chunk)} rows enqueued successfully.")
