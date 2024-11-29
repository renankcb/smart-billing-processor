import asyncio
from fastapi import FastAPI
from app.core.database import init_db
from app.api.routes_upload import router as routes_upload
from app.api.routes_healthcheck import router as routes_healthcheck
from app.models import users, debts
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.consumers.file_processing_consumer import FileProcessingConsumer
from app.consumers.chunk_processing_consumer import ChunkProcessingConsumer
from app.consumers.boleto_generation_consumer import BoletoGenerationConsumer
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
# logger.add(
#     sys.stdout,
#     level="INFO",
#     format="{time} {level} {message} {extra}",
#     serialize=True,
# )

# Instância FastAPI
app = FastAPI()

Instrumentator().instrument(app).expose(app)

# Incluindo rotas
app.include_router(routes_upload, prefix="/upload", tags=["Upload"])
app.include_router(routes_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])

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

    # Inicializa Consumidores
    file_processing_consumer = FileProcessingConsumer(connection_params)
    chunk_processing_consumer = ChunkProcessingConsumer(connection_params)
    boleto_generation_consumer = BoletoGenerationConsumer(connection_params)

    # Declarar infraestrutura
    await file_processing_consumer.declare_infrastructure()
    await chunk_processing_consumer.declare_infrastructure()
    await boleto_generation_consumer.declare_infrastructure()

    # Iniciar consumidores de forma paralela
    asyncio.create_task(file_processing_consumer.start_consuming())
    asyncio.create_task(boleto_generation_consumer.start_consuming())
    num_consumers = 2
    for i in range(num_consumers):
        consumer = ChunkProcessingConsumer(connection_params)
        await consumer.declare_infrastructure()
        asyncio.create_task(consumer.start_consuming(prefetch_count=3))

    


@app.on_event("startup")
async def startup_event():
    """
    Evento executado ao iniciar o aplicativo. Inicializa os consumidores.
    """
    await initialize_consumers()

    # Inicializa BD caso nao tenha sido criado
    await init_db()
