import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.upload_service import UploadService


@pytest.fixture
def rabbitmq_mock():
    return MagicMock()


@pytest.fixture
def upload_service(rabbitmq_mock):
    return UploadService(rabbitmq=rabbitmq_mock)


@pytest.mark.asyncio
async def test_save_file(upload_service, tmpdir):
    upload_service.temp_dir = tmpdir
    file_mock = AsyncMock()
    file_mock.filename = "test.csv"
    file_mock.read.return_value = b"sample data"

    file_path = await upload_service.save_file(file_mock)

    assert file_path == f"{tmpdir}/test.csv"
    assert os.path.exists(file_path)


def test_enqueue_file(upload_service, rabbitmq_mock):
    file_id = "12345"
    file_path = "/tmp/test.csv"
    file_name = "test.csv"

    upload_service.enqueue_file(file_id, file_path, file_name)

    rabbitmq_mock.publish_to_queue.assert_called_once_with(
        exchange="file_exchange",
        routing_key="file.process",
        message={
            "file_id": file_id,
            "file_name": file_name,
            "file_path": file_path,
        },
    )
