import os
from loguru import logger
from fastapi import UploadFile
from app.core.rabbitmq import RabbitMQ

TEMP_DIR = "/tmp"

async def save_and_enqueue_file(file: UploadFile) -> str:
    """
    Salva o arquivo CSV temporariamente e enfileira a mensagem para processamento.

    Args:
        file (UploadFile): Arquivo enviado pelo cliente.

    Returns:
        str: Mensagem de status.

    Raises:
        ValueError: Se houver algum problema com o arquivo.
    """
    try:
        file_path = os.path.join(TEMP_DIR, file.filename)
        
        with open(file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        logger.info(f"File saved successfully: {file_path}")

        # Envia mensagem para a fila indicando que o arquivo está pronto para processamento
        message = {"file_path": file_path, "filename": file.filename}
        RabbitMQ.publish_to_queue(
            exchange="file_exchange",
            routing_key="file.process",
            message={"file_path": file_path, "file_name": file.filename}
        )

        logger.info(f"File {file.filename} enqueued successfully for processing.")
        return f"File {file.filename} uploaded and enqueued successfully."
    except Exception as e:
        logger.error(f"Error during file processing for {file.filename}: {str(e)}")
        raise ValueError(f"Error during file processing: {str(e)}")
