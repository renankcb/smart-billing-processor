import pytest
from unittest.mock import Mock, patch
from app.core.consumer_base import ConsumerBase


class MockConsumer(ConsumerBase):
    def process_message(self, message):
        if "fail" in message:
            raise ValueError("Simulated processing error")


@pytest.fixture
def mock_consumer():
    return MockConsumer("test_queue", "test_retry_queue", "test_dlq", max_retries=3)


@patch("core.consumer_base.pika.BlockingConnection")
def test_consumer_retry_logic(mock_connection, mock_consumer):
    mock_channel = Mock()
    mock_connection.return_value.channel.return_value = mock_channel

    message = {"fail": True}
    mock_consumer._on_message(mock_channel, Mock(), Mock(headers={"x-retry-count": 0}), str(message).encode())

    # Verificar se a mensagem foi reenfileirada para a fila de retry
    mock_channel.basic_publish.assert_called_with(
        exchange="",
        routing_key="test_retry_queue",
        body=str(message).encode(),
        properties=Mock(),
    )


@patch("core.consumer_base.pika.BlockingConnection")
def test_consumer_dlq_logic(mock_connection, mock_consumer):
    mock_channel = Mock()
    mock_connection.return_value.channel.return_value = mock_channel

    properties = Mock(headers={"x-retry-count": 3})
    message = {"fail": True}
    mock_consumer._on_message(mock_channel, Mock(), properties, str(message).encode())

    # Verificar se a mensagem foi enviada para a DLQ
    mock_channel.basic_publish.assert_called_with(
        exchange="",
        routing_key="test_dlq",
        body=str(message).encode(),
    )
