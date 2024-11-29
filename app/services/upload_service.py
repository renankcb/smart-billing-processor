import os
import uuid
from loguru import logger
from fastapi import UploadFile
from app.core.message_broker import MessageBroker

TEMP_DIR = "/tmp"


class UploadService:
    """
    Serviço responsável por salvar arquivos temporariamente e enfileirar mensagens para processamento.
    """

    def __init__(self, message_broker: MessageBroker, temp_dir: str = TEMP_DIR):
        self.message_broker = message_broker
        self.temp_dir = temp_dir
        self.ensure_temp_dir_exists()

    def ensure_temp_dir_exists(self):
        """Garante que o diretório temporário existe."""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    async def save_file(self, file: UploadFile) -> str:
        """
        Salva o arquivo em um diretório temporário.

        Args:
            file (UploadFile): Arquivo enviado pelo cliente.

        Returns:
            str: Caminho completo do arquivo salvo.
        """
        file_path = os.path.join(self.temp_dir, file.filename)
        try:
            with open(file_path, "wb") as temp_file:
                temp_file.write(await file.read())
            logger.info(f"File saved at {file_path}")
            return file_path
        except Exception as e:
            logger.error(
                "Failed to save file",
                extra={"file_name": file.filename, "error": str(e)},
            )
            raise ValueError(f"Error saving file: {str(e)}")

    async def enqueue_file(self, file_id: str, file_path: str, file_name: str):
        """
        Enfileira uma mensagem para processamento do arquivo.

        Args:
            file_id (str): Identificador único do arquivo.
            file_path (str): Caminho do arquivo salvo.
            file_name (str): Nome original do arquivo.
        """
        message = {
            "file_id": file_id,
            "file_name": file_name,
            "file_path": file_path,
        }
        try:
            await self.message_broker.publish_to_queue(
                exchange="file_exchange",
                routing_key="file.process",
                message=message,
            )
            logger.info(f"Message enqueued for file {file_name} with ID {file_id}")
        except Exception as e:
            logger.error(
                "Failed to enqueue message",
                extra={"file_id": file_id, "file_name": file_name, "error": str(e)},
            )
            raise ValueError(f"Error enqueuing message: {str(e)}")

    async def save_and_enqueue_file(self, file: UploadFile) -> str:
        """
        Salva o arquivo temporariamente e enfileira uma mensagem para processamento.

        Args:
            file (UploadFile): Arquivo enviado pelo cliente.

        Returns:
            str: Mensagem de status.

        Raises:
            ValueError: Se houver erro no processo.
        """
        file_id = str(uuid.uuid4())  # Gera um identificador único para o arquivo
        file_path = await self.save_file(file)
        await self.enqueue_file(file_id, file_path, file.filename)
        return f"File {file.filename} uploaded and enqueued successfully with ID {file_id}."
