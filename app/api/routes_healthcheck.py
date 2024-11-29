from fastapi import APIRouter
from app.core.database import async_engine
from app.core.rabbitmq_connection_params import RabbitMQConnectionParams
from sqlalchemy.sql import text

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
        async with async_engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))  # Use text() para executar a consulta
            if result.scalar() == 1:
                health_status["database"] = True
    except Exception as e:
        health_status["database"] = False
        print(f"Database connection error: {e}")

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
        print(f"RabbitMQ connection error: {e}")

    # Retorno do status de saúde
    if all(health_status.values()):
        return {"status": "healthy", "details": health_status}
    else:
        return {"status": "unhealthy", "details": health_status}