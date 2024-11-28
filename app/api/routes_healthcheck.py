from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.core.database import engine
import pika

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
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq")  
        )
        if connection.is_open:
            health_status["rabbitmq"] = True
        connection.close()
    except Exception as e:
        health_status["rabbitmq"] = False

    if all(health_status.values()):
        return {"status": "healthy", "details": health_status}
    else:
        return {"status": "unhealthy", "details": health_status}
