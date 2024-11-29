import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.api.routes_upload import router
from app.services.upload_service import UploadService
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/upload")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
@patch("app.routes.routes_upload.get_upload_service")
async def test_upload_csv_success(mock_get_service, client):
    mock_service = AsyncMock(spec=UploadService)
    mock_service.save_and_enqueue_file.return_value = "File uploaded and enqueued successfully with ID 12345"
    mock_get_service.return_value = mock_service

    with open("test.csv", "wb") as f:
        f.write(b"column1,column2\nvalue1,value2")

    with open("test.csv", "rb") as file:
        response = client.post("/upload/", files={"file": file})

    assert response.status_code == 200
    assert response.json() == {"message": "File uploaded and enqueued successfully with ID 12345"}


@pytest.mark.asyncio
@patch("app.routes.routes_upload.get_upload_service")
async def test_upload_csv_invalid_format(mock_get_service, client):
    mock_service = AsyncMock(spec=UploadService)
    mock_get_service.return_value = mock_service

    with open("test.txt", "wb") as f:
        f.write(b"invalid content")

    with open("test.txt", "rb") as file:
        response = client.post("/upload/", files={"file": file})

    assert response.status_code == 400
    assert response.json() == {"detail": "Only CSV files are allowed."}
