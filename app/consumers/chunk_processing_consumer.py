from loguru import logger
from app.consumers.base_consumer import BaseConsumer
from app.services.chunk_processing_service import ChunkProcessingService
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.schemas.chunk import ChunkMessage
from app.core.database import async_session_factory


class ChunkProcessingConsumer(BaseConsumer):
    """
    Consumidor responsável por processar chunks de arquivos.
    """

    def __init__(self, connection_params: RabbitMQConnectionParams):
        super().__init__(
            queue_name="chunk_processing_queue",
            exchange_name="chunk_exchange",
            routing_key="chunk.process",
            connection_params=connection_params,
        )
        self.chunk_processing_service = ChunkProcessingService(session_factory=async_session_factory)

    async def process_message(self, message: dict):
        """
        Processa a mensagem de chunk.

        Args:
            message (dict): Mensagem contendo o chunk e metadados.
        """

        try:
            validated_message = ChunkMessage(**message)
            await self.chunk_processing_service.process_chunk(
                validated_message.file_id,
                [row.dict() for row in validated_message.chunk],
            )

        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            raise
