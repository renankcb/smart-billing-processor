from fastapi import FastAPI
from app.core.database import engine
from app.api.routes_upload import router as routes_upload
from app.api.routes_healthcheck import router as routes_healthcheck
from app.consumers.file_processor_consumer import FileProcessorConsumer
from app.models import users, debts
from loguru import logger

app = FastAPI()

# Incluindo rotas
app.include_router(routes_upload, prefix="/upload", tags=["Upload"])
app.include_router(routes_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])

file_processor_consumer = FileProcessorConsumer()


@app.on_event("startup")
async def startup_event():
    """
    Lógica executada no início do sistema.
    """
    try:
        logger.info("Starting application...")

        # Instanciar e configurar o FileProcessorConsumer
        # file_processor_consumer.setup_and_initialize()

        logger.info("FileProcessorConsumer initialized.")
    except Exception as e:
        logger.error(f"Error during startup configuration: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Lógica executada ao desligar o sistema.
    """
    logger.info("Shutting down application...")


# Criar as tabelas no banco (apenas para desenvolvimento)
users.Base.metadata.create_all(bind=engine)
debts.Base.metadata.create_all(bind=engine)
