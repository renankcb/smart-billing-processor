import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.api.routes_upload import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/upload")

client = TestClient(app)

@pytest.fixture
def mock_save_and_enqueue_file():
    """Mock para a função save_and_enqueue_file."""
    with patch("app.services.upload_service.save_and_enqueue_file", new_callable=AsyncMock) as mock:
        yield mock

def test_upload_csv_success(mock_save_and_enqueue_file):
    """Teste de upload bem-sucedido."""
    mock_save_and_enqueue_file.return_value = "File uploaded successfully."

    response = client.post(
        "/upload/",
        files={"file": ("test.csv", b"mock,file,content", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "File uploaded successfully."}

def test_upload_csv_invalid_format(mock_save_and_enqueue_file):
    """Teste de upload com formato inválido."""
    response = client.post(
        "/upload/",
        files={"file": ("test.txt", b"mock,file,content", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are allowed."
    mock_save_and_enqueue_file.assert_not_called()

def test_upload_csv_unexpected_error(mock_save_and_enqueue_file):
    """Teste de erro inesperado no upload."""
    mock_save_and_enqueue_file.side_effect = Exception("Unexpected error")

    response = client.post(
        "/upload/",
        files={"file": ("test.csv", b"mock,file,content", "text/csv")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "An unexpected error occurred during file upload."
