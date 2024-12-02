import os
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from fastapi import UploadFile
from app.core.message_broker import MessageBroker
from app.services.upload_service import UploadService

class TestUploadService:
    @pytest.fixture
    def message_broker_mock(self):
        """Fixture to create a mock MessageBroker for each test."""
        return AsyncMock(spec=MessageBroker)

    @pytest.fixture
    def upload_service(self, message_broker_mock, tmp_path):
        """Fixture to create UploadService with a temporary directory."""
        return UploadService(message_broker_mock, temp_dir=str(tmp_path))

    def test_ensure_temp_dir_exists(self, tmp_path):
        """Test that ensure_temp_dir_exists creates the directory if it doesn't exist."""
        # Create a mock directory path
        non_existent_dir = str(tmp_path / "new_temp_dir")
        
        # Create service with the non-existent directory
        message_broker_mock = AsyncMock(spec=MessageBroker)
        service = UploadService(message_broker_mock, temp_dir=non_existent_dir)
        
        # Verify the directory was created
        assert os.path.exists(non_existent_dir)

    def test_validate_file_format_valid_csv(self, upload_service):
        """Test validation of a valid CSV file."""
        file_mock = UploadFile(filename="test.csv", file=BytesIO(b"test content"))
        
        try:
            upload_service.validate_file_format(file_mock)
        except ValueError:
            pytest.fail("Valid CSV file should not raise an exception")

    def test_validate_file_format_invalid_file(self, upload_service):
        """Test validation of an invalid file format."""
        file_mock = UploadFile(filename="test.txt", file=BytesIO(b"test content"))
        
        with pytest.raises(ValueError, match="Only CSV files are allowed."):
            upload_service.validate_file_format(file_mock)

    @pytest.mark.asyncio
    async def test_save_file_success(self, upload_service, tmp_path):
        """Test successful file saving."""
        # Create a mock file
        file_content = b"test csv content"
        file_mock = UploadFile(filename="test.csv", file=BytesIO(file_content))
        
        # Mock file.read() to return content
        file_mock.read = AsyncMock(return_value=file_content)
        
        # Save the file
        file_path = await upload_service.save_file(file_mock)
        
        # Assertions
        assert os.path.exists(file_path)
        assert file_path.endswith("test.csv")
        with open(file_path, 'rb') as saved_file:
            assert saved_file.read() == file_content

    @pytest.mark.asyncio
    async def test_save_file_error(self, upload_service):
        """Test file saving with a simulated error."""
        # Create a mock file that will cause an error when read
        file_mock = UploadFile(filename="test.csv", file=BytesIO(b"test content"))
        file_mock.read = AsyncMock(side_effect=IOError("Simulated read error"))
        
        # Expect a ValueError to be raised
        with pytest.raises(ValueError, match="Error saving file: Simulated read error"):
            await upload_service.save_file(file_mock)

    @pytest.mark.asyncio
    async def test_enqueue_file_success(self, upload_service, message_broker_mock):
        """Test successful file enqueuing."""
        # Prepare test data
        file_id = str(uuid.uuid4())
        file_path = "/tmp/test.csv"
        file_name = "test.csv"
        
        # Mock the message broker's publish method
        message_broker_mock.publish_to_queue = AsyncMock()
        
        # Enqueue the file
        await upload_service.enqueue_file(file_id, file_path, file_name)
        
        # Verify publish_to_queue was called with correct arguments
        message_broker_mock.publish_to_queue.assert_called_once_with(
            exchange="file_exchange",
            routing_key="file.process",
            message={
                "file_id": file_id,
                "file_name": file_name,
                "file_path": file_path
            }
        )

    @pytest.mark.asyncio
    async def test_enqueue_file_error(self, upload_service, message_broker_mock):
        """Test file enqueuing with a simulated error."""
        # Prepare test data
        file_id = str(uuid.uuid4())
        file_path = "/tmp/test.csv"
        file_name = "test.csv"
        
        # Mock the message broker to raise an exception
        message_broker_mock.publish_to_queue = AsyncMock(
            side_effect=Exception("Enqueue error")
        )
        
        # Expect a ValueError to be raised
        with pytest.raises(ValueError, match="Error enqueuing message: Enqueue error"):
            await upload_service.enqueue_file(file_id, file_path, file_name)

    @pytest.mark.asyncio
    async def test_save_and_enqueue_file_success(self, upload_service, message_broker_mock):
        """Test complete file save and enqueue process."""
        # Create a mock file
        file_content = b"test csv content"
        file_mock = UploadFile(filename="test.csv", file=BytesIO(file_content))
        file_mock.read = AsyncMock(return_value=file_content)
        
        # Mock the dependent methods
        upload_service.save_file = AsyncMock(return_value="/tmp/test.csv")
        upload_service.enqueue_file = AsyncMock()
        
        # Call the method
        result = await upload_service.save_and_enqueue_file(file_mock)
        
        # Assertions
        assert "uploaded and enqueued successfully" in result
        assert "test.csv" in result
        
        # Verify method calls
        upload_service.validate_file_format(file_mock)
        upload_service.save_file.assert_called_once_with(file_mock)
        upload_service.enqueue_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_and_enqueue_file_invalid_format(self, upload_service):
        """Test save and enqueue with an invalid file format."""
        # Create a mock file with invalid format
        file_mock = UploadFile(filename="test.txt", file=BytesIO(b"test content"))
        
        # Expect a ValueError to be raised
        with pytest.raises(ValueError, match="Only CSV files are allowed."):
            await upload_service.save_and_enqueue_file(file_mock)