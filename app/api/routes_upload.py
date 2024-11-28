from fastapi import APIRouter, UploadFile, HTTPException, status
from loguru import logger
from app.services.upload_service import save_and_enqueue_file

router = APIRouter()

@router.post("/")
async def upload_csv(file: UploadFile):
    """
    Endpoint para upload de arquivos CSV.

    Args:
        file (UploadFile): Arquivo enviado pelo cliente.

    Returns:
        dict: Mensagem de sucesso ou erro.
    """
    logger.info(f"Received file upload request: {file.filename}")
    
    if not file.filename.endswith(".csv"):
        logger.warning(f"Rejected file upload: {file.filename}. Invalid file format.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed.",
        )

    try:
        result = await save_and_enqueue_file(file)
        logger.info(f"File upload completed successfully: {file.filename}")
        return {"message": result}
    except ValueError as e:
        logger.error(f"Validation error during file upload: {file.filename}. Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {file.filename}. Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file upload.",
        )
