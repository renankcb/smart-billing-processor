import os
import csv
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO

from app.services.file_processor_service import FileProcessorService
from app.schemas.chunk import ChunkRow

class TestFileProcessorService:
    @pytest.fixture
    def file_processor_service(self):
        """Fixture to create a FileProcessorService instance."""
        return FileProcessorService()

    @pytest.fixture
    def valid_csv_content(self):
        """
        Fixture providing a valid CSV content with sample data.
        """
        return """name,governmentId,email,debtAmount,debtDueDate,debtId
Elijah Santos,9558,janet95@example.com,7811,2024-01-19,ea23f2ca-663a-4266-a742-9da4c9f4fcb3
Samuel Orr,5486,linmichael@example.com,5662,2023-02-25,acc1794e-b264-4fab-8bb7-3400d4c4734d
Leslie Morgan,9611,russellwolfe@example.net,6177,2022-10-17,9f5a2b0c-967e-4443-a03d-9d7cdcb2216f"""

    @pytest.fixture
    def mixed_csv_content(self):
        """
        Fixture providing a CSV content with both valid and invalid rows.
        """
        return """name,governmentId,email,debtAmount,debtDueDate,debtId
Elijah Santos,9558,janet95@example.com,7811,2024-01-19,ea23f2ca-663a-4266-a742-9da4c9f4fcb3
Invalid User,,invalid-email,INVALID,2023-13-45,invalid-uuid
Samuel Orr,5486,linmichael@example.com,5662,2023-02-25,acc1794e-b264-4fab-8bb7-3400d4c4734d"""

    def test_process_file_successful_processing(self, file_processor_service, valid_csv_content, tmp_path):
        """
        Test successful file processing with valid CSV data.
        """
        # Create a temporary CSV file
        file_path = tmp_path / "valid_test.csv"
        file_path.write_text(valid_csv_content)

        # Process the file
        chunks = list(file_processor_service.process_file(str(file_path), chunk_size=2))

        # Assertions
        assert len(chunks) == 2  # 3 rows, chunk_size=2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1
        
        # Verify each processed row has a generated debt_id
        for chunk in chunks:
            for row in chunk:
                assert 'debtId' in row
                assert row['name'] in ['Elijah Santos', 'Samuel Orr', 'Leslie Morgan']

    def test_process_file_with_invalid_rows(self, file_processor_service, mixed_csv_content, tmp_path):
        """
        Test processing a file with a mix of valid and invalid rows.
        """
        # Create a temporary CSV file with mixed content
        file_path = tmp_path / "mixed_test.csv"
        file_path.write_text(mixed_csv_content)

        # Mock the _log_invalid_rows method
        with patch.object(file_processor_service, '_log_invalid_rows') as mock_log_invalid:
            # Process the file
            chunks = list(file_processor_service.process_file(str(file_path)))

            # Assertions
            assert len(chunks) == 1  # Only valid rows
            assert len(chunks[0]) == 2  # 2 valid rows
            
            # Verify invalid rows logging
            mock_log_invalid.assert_called_once()
            logged_rows = mock_log_invalid.call_args[0][1]
            assert len(logged_rows) == 1
            assert logged_rows[0]['line_number'] == 2  # Invalid row

    def test_process_file_custom_chunk_size(self, file_processor_service, valid_csv_content, tmp_path):
        """
        Test processing with different chunk sizes.
        """
        # Create a temporary CSV file
        file_path = tmp_path / "chunk_test.csv"
        file_path.write_text(valid_csv_content)

        # Process with different chunk sizes
        chunks_default = list(file_processor_service.process_file(str(file_path)))
        chunks_custom = list(file_processor_service.process_file(str(file_path), chunk_size=1))

        # Assertions
        assert len(chunks_default) == 1  # Default chunk_size is 200
        assert len(chunks_custom) == 3  # chunk_size=1
        assert all(len(chunk) == 1 for chunk in chunks_custom)

    def test_process_file_empty_file(self, file_processor_service, tmp_path):
        """
        Test processing an empty CSV file.
        """
        # Create an empty CSV file
        file_path = tmp_path / "empty_test.csv"
        file_path.write_text("name,governmentId,email,debtAmount,debtDueDate,debtId\n")

        # Process the file
        chunks = list(file_processor_service.process_file(str(file_path)))

        # Assertions
        assert len(chunks) == 0  # No chunks generated

    def test_process_file_non_existent_file(self, file_processor_service):
        """
        Test processing a non-existent file.
        """
        with pytest.raises(ValueError, match="Error processing file"):
            list(file_processor_service.process_file("/path/to/non_existent_file.csv"))

    def test_process_file_permission_error(self, file_processor_service, tmp_path):
        """
        Test handling of file permission errors.
        """
        # Create a file with no read permissions
        file_path = tmp_path / "no_permission.csv"
        file_path.write_text("test content")
        file_path.chmod(0o000)  # Remove all permissions

        with pytest.raises(ValueError, match="Error processing file"):
            list(file_processor_service.process_file(str(file_path)))