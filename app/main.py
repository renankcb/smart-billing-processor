from fastapi import FastAPI
from app.core.database import engine
from app.api.routes_upload import router as routes_upload
from app.api.routes_healthcheck import router as routes_healthcheck
from app.models import users, debts
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from app.consumers.file_processing_consumer import FileProcessingConsumer
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator
import sys
import threading

# Remove handlers padrão para evitar linhas não estruturadas
logger.remove()

# Adiciona um handler para enviar logs ao Logstash em JSON
logger.add(
    "tcp://logstash:5044",
    level="INFO",
    format="{time} {level} {message} {extra}",
    serialize=True  # Garante que os logs sejam JSON serializados
)

# Adiciona um handler para stdout em JSON (opcional para debugging local)
logger.add(
    sys.stdout,
    level="INFO",
    format="{time} {level} {message} {extra}",
    serialize=True
)

app = FastAPI()

Instrumentator().instrument(app).expose(app)

# Incluindo rotas
app.include_router(routes_upload, prefix="/upload", tags=["Upload"])
app.include_router(routes_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])

# Criar as tabelas no banco (apenas para desenvolvimento)
users.Base.metadata.create_all(bind=engine)
debts.Base.metadata.create_all(bind=engine)

def initialize_consumers():
    """
    Inicializa os consumidores e declara as filas, exchanges e bindings.
    """
    connection_params = RabbitMQConnectionParams(
        host="rabbitmq",
        port=5672,
        username="guest",
        password="guest"
    )

    # Inicializa o FileProcessingConsumer
    file_processing_consumer = FileProcessingConsumer(connection_params)
    file_processing_consumer.declare_infrastructure()

    # Inicia o consumidor em uma thread separada para não bloquear o FastAPI
    threading.Thread(target=file_processing_consumer.start_consuming, daemon=True).start()

# Inicializa os consumidores ao iniciar o sistema
initialize_consumers()
