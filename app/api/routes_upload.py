from fastapi import APIRouter, UploadFile, HTTPException, status, Depends
from loguru import logger
from app.services.upload_service import UploadService
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.core.rabbitmq_broker import RabbitMQBroker

router = APIRouter()

# Dependência para injetar o serviço
def get_upload_service() -> UploadService:
    """
    Configura a instância do UploadService com o RabbitMQBroker.
    """
    # Configura os parâmetros de conexão do RabbitMQ
    connection_params = RabbitMQConnectionParams(
        host="rabbitmq", 
        port=5672,
        username="guest",
        password="guest",
    )

    # Cria o RabbitMQBroker
    rabbitmq_broker = RabbitMQBroker(connection_params)

    # Retorna o UploadService configurado
    return UploadService(message_broker=rabbitmq_broker)


@router.post("/")
async def upload_csv(
    file: UploadFile,
    upload_service: UploadService = Depends(get_upload_service),
):
    """
    Endpoint para upload de arquivos CSV.

    Args:
        file (UploadFile): Arquivo enviado pelo cliente.

    Returns:
        dict: Mensagem de sucesso ou erro.
    """
    logger.info(
        "File upload request received.",
        extra={"file_name": file.filename, "operation": "upload_csv"},
    )

    # Validação do formato do arquivo
    if not file.filename.endswith(".csv"):
        logger.warning(
            "File upload rejected. Invalid format.",
            extra={
                "file_name": file.filename,
                "operation": "upload_csv",
                "reason": "Invalid format",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed.",
        )

    try:
        # Salva e enfileira o arquivo usando o serviço
        result = await upload_service.save_and_enqueue_file(file)
        logger.info(
            "File upload completed successfully.",
            extra={
                "file_name": file.filename,
                "operation": "upload_csv",
                "status": "success",
            },
        )
        return {"message": result}

    except ValueError as e:
        logger.error(
            "Validation error during file upload.",
            extra={
                "file_name": file.filename,
                "operation": "upload_csv",
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(
            "Unexpected error during file upload.",
            extra={
                "file_name": file.filename,
                "operation": "upload_csv",
                "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file upload.",
        )
