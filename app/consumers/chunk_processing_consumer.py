from loguru import logger
import json
from app.consumers.base_consumer import BaseConsumer
from app.services.chunk_processing_service import ChunkProcessingService
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams


class ChunkProcessingConsumer(BaseConsumer):
    """
    Consumidor responsável por processar chunks de arquivos.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams, prefetch_count=1):
        super().__init__(
            queue_name="chunk_processing_queue",
            exchange_name="chunk_exchange",
            routing_key="chunk.process",
            connection_params=connection_params,
        )
        self.chunk_processing_service = ChunkProcessingService()
        self.prefetch_count = prefetch_count

    async def process_message(self, message: dict):
        """
        Processa a mensagem de chunk.

        Args:
            message (dict): Mensagem contendo o chunk e metadados.
        """
        try:
            file_id = message.get("file_id")
            chunk = message.get("chunk")

            logger.info(f"Processing chunk for file {file_id} with {len(chunk)} rows.")

            # Processa o chunk usando o serviço
            await self.chunk_processing_service.process_chunk(file_id, chunk)

        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            raise
