import asyncio
from fastapi import FastAPI
from app.core.database import engine
from app.api.routes_upload import router as routes_upload
from app.api.routes_healthcheck import router as routes_healthcheck
from app.models import users, debts
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.consumers.file_processing_consumer import FileProcessingConsumer
from app.consumers.chunk_processing_consumer import ChunkProcessingConsumer
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator
import sys

# Configuração de logging
logger.remove()
logger.add(
    "tcp://logstash:5044",
    level="INFO",
    format="{time} {level} {message} {extra}",
    serialize=True,
)
logger.add(
    sys.stdout,
    level="INFO",
    format="{time} {level} {message} {extra}",
    serialize=True,
)

# Instância FastAPI
app = FastAPI()

Instrumentator().instrument(app).expose(app)

# Incluindo rotas
app.include_router(routes_upload, prefix="/upload", tags=["Upload"])
app.include_router(routes_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])

# Criar tabelas no banco de dados (apenas para desenvolvimento)
users.Base.metadata.create_all(bind=engine)
debts.Base.metadata.create_all(bind=engine)

async def initialize_consumers():
    """
    Inicializa os consumidores e declara as filas, exchanges e bindings.
    """
    connection_params = RabbitMQConnectionParams(
        host="rabbitmq",
        port=5672,
        username="guest",
        password="guest",
    )

    # Inicializa o FileProcessingConsumer
    file_processing_consumer = FileProcessingConsumer(connection_params)
    await file_processing_consumer.declare_infrastructure()

    # Inicializa o ChunkProcessingConsumer
    chunk_processing_consumer = ChunkProcessingConsumer(connection_params, prefetch_count=5)
    await chunk_processing_consumer.declare_infrastructure()

    # Criação de tarefas para os consumidores
    asyncio.create_task(file_processing_consumer.start_consuming())
    asyncio.create_task(chunk_processing_consumer.start_consuming())


@app.on_event("startup")
async def startup_event():
    """
    Evento executado ao iniciar o aplicativo. Inicializa os consumidores.
    """
    await initialize_consumers()
