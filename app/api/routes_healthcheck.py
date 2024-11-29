from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
import aio_pika

router = APIRouter()

@router.get("/")
async def health_check():
    """
    Verifica a saúde do sistema:
    - Conectividade com o banco de dados.
    - Conectividade com o RabbitMQ.
    """
    health_status = {
        "database": False,
        "rabbitmq": False
    }

    # Verificar conexão com o banco de dados
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        health_status["database"] = True
    except Exception as e:
        health_status["database"] = False

    # Verificar conexão com o RabbitMQ
    try:
        connection_params = RabbitMQConnectionParams(
            host="rabbitmq",
            port=5672,
            username="guest",
            password="guest"
        )
        connection = await connection_params.get_connection()
        async with connection:
            channel = await connection.channel()
            # Declaração de uma fila temporária apenas para validar a conectividade
            queue = await channel.declare_queue(exclusive=True)
            if queue:
                health_status["rabbitmq"] = True
    except Exception as e:
        health_status["rabbitmq"] = False

    if all(health_status.values()):
        return {"status": "healthy", "details": health_status}
    else:
        return {"status": "unhealthy", "details": health_status}
