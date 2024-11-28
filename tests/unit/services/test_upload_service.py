import os
import pytest
from unittest.mock import AsyncMock, patch, mock_open
from fastapi import UploadFile
from app.services.upload_service import save_and_enqueue_file

TEMP_DIR = "/tmp"

@pytest.fixture
def mock_file():
    """Mock do arquivo de upload."""
    return AsyncMock(spec=UploadFile, filename="test.csv")

@pytest.mark.asyncio
@patch("app.services.upload_service.RabbitMQ.publish_to_queue")
@patch("builtins.open", new_callable=mock_open)
async def test_save_and_enqueue_file_success(mock_open, mock_publish_to_queue, mock_file):
    """Teste para salvar e enfileirar um arquivo com sucesso."""
    # Simula conteúdo do arquivo
    mock_file.read.return_value = b"mock,file,content"

    result = await save_and_enqueue_file(mock_file)

    # Verifica se o arquivo foi salvo no diretório temporário
    mock_open.assert_called_once_with(os.path.join(TEMP_DIR, mock_file.filename), "wb")
    mock_open.return_value.write.assert_called_once_with(b"mock,file,content")

    # Verifica se a mensagem foi publicada na fila
    mock_publish_to_queue.assert_called_once_with(
        exchange="file_exchange",
        routing_key="file.process",
        message={"file_path": os.path.join(TEMP_DIR, mock_file.filename), "file_name": mock_file.filename},
    )

    # Verifica a resposta
    assert result == f"File {mock_file.filename} uploaded and enqueued successfully."

@pytest.mark.asyncio
@patch("app.services.upload_service.RabbitMQ.publish_to_queue")
async def test_save_and_enqueue_file_failure(mock_publish_to_queue, mock_file):
    """Teste para tratar falha no salvamento ou enfileiramento."""
    mock_file.read.side_effect = Exception("Unexpected error")

    with pytest.raises(ValueError, match="Error during file processing: Unexpected error"):
        await save_and_enqueue_file(mock_file)

    # Publicação na fila não deve ser chamada
    mock_publish_to_queue.assert_not_called()
