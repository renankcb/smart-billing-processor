import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker
import aio_pika
import csv
import os
from uuid import uuid4
import json

from app.main import app
from app.core.database import Base
from app.models.users import User
from app.models.debts import Debt
from app.models.boletos import Boleto

# Configurações de teste
TEST_DB_URL = "postgresql+asyncpg://admin:admin@localhost:5432/boletos"
TEST_RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"

@pytest.fixture
async def test_db():
    """Cria um banco de dados de teste temporário"""
    engine = create_async_engine(TEST_DB_URL)
    
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    #     await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    yield async_session
    
    await engine.dispose()

@pytest.fixture
async def test_rabbitmq():
    """Configura conexão de teste com RabbitMQ"""
    connection = await aio_pika.connect_robust(TEST_RABBITMQ_URL)
    
    # Limpa e declara exchanges e filas
    async with connection.channel() as channel:
        # Declara exchanges como duráveis
        exchanges = {
            "file_exchange": await channel.declare_exchange(
                "file_exchange",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            ),
            "chunk_exchange": await channel.declare_exchange(
                "chunk_exchange",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            ),
            "boleto_exchange": await channel.declare_exchange(
                "boleto_exchange",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            ),
        }
        
        # Declara filas como duráveis
        queues = {
            name: await channel.declare_queue(
                name,
                durable=True,
                auto_delete=False
            )
            for name in [
                "file_processing_queue",
                "chunk_processing_queue",
                "boleto_generation_queue"
            ]
        }
        
        # Limpa as filas
        for queue in queues.values():
            await queue.purge()
    
    yield connection
    
    await connection.close()

@pytest.fixture
def test_client():
    """Cliente de teste FastAPI"""
    return TestClient(app)

@pytest.mark.asyncio
async def test_full_integration_flow(test_client, test_db, test_rabbitmq):
    """Testa o fluxo completo de processamento de arquivo"""
    
    # 1. Cria arquivo CSV de teste
    test_file = "test_debts.csv"
    test_data = [
        {
            "name": "Test User",
            "governmentId": 123456789,
            "email": "test@example.com",
            "debtAmount": 1000.00,
            "debtDueDate": "2024-12-31",
            "debtId": str(uuid4())  # Inclui o debtId que é necessário
        }
    ]
    
    # Cria o arquivo CSV com encoding e newline corretos
    with open(test_file, "w", encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=test_data[0].keys())
        writer.writeheader()
        writer.writerows(test_data)
    
    try:
        # 2. Faz upload do arquivo - ajustado para enviar como arquivo CSV
        with open(test_file, "rb") as f:
            files = {
                "file": (
                    "test_debts.csv",
                    f,
                    "application/vnd.ms-excel"  # MIME type correto para CSV
                )
            }
            response = test_client.post("/upload/", files=files)
        
        # Adiciona log para debug
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        
        assert response.status_code == 200
        
        # 3. Verifica processamento na fila de arquivos
        async with test_rabbitmq.channel() as channel:
            queue = await channel.declare_queue(
                "file_processing_queue",
                durable=True
            )
            
            # Aguarda mensagem
            await asyncio.sleep(3)
            message = await queue.get(timeout=5)
            
            if message:
                async with message.process():
                    body = json.loads(message.body.decode())
                    assert "file_id" in body
        
    finally:
        # Limpa o arquivo de teste
        if os.path.exists(test_file):
            os.remove(test_file)

@pytest.mark.asyncio
async def test_chunk_processing(test_db, test_rabbitmq):
    """Testa processamento específico de chunks"""
    
    chunk_data = {
        "file_id": str(uuid4()),
        "chunk": [
            {
                "name": "Test User",
                "governmentId": "123456789",
                "email": "test@example.com",
                "debtAmount": 1000.00,
                "debtDueDate": "2024-12-31",
                "debtId": str(uuid4())
            }
        ]
    }
    
    # Publica chunk na fila
    async with test_rabbitmq.channel() as channel:
        # Declara exchange como durável
        exchange = await channel.declare_exchange(
            "chunk_exchange",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # Publica mensagem
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(chunk_data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="chunk.process"
        )
    
    # Aguarda processamento
    await asyncio.sleep(2)
    
    try:
        # Verifica dados no banco
        async with test_db() as session:
            # Verifica se o usuário foi criado
            result = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE users.government_id = 123456789")
            )
            count = result.scalar()
            assert count == 1
            
    finally:
        # Limpa os dados após o teste
        async with test_db() as session:
            # Deleta o usuário de teste
            await session.execute(
                text("DELETE FROM users WHERE government_id = 123456789")
            )
            await session.commit()

@pytest.mark.asyncio
async def test_error_handling(test_client, test_rabbitmq):
    """Testa tratamento de erros no upload e processamento"""
    
    # Teste de upload com arquivo inválido
    with open("invalid.txt", "w") as f:
        f.write("invalid data")
    
    try:
        with open("invalid.txt", "rb") as f:
            response = test_client.post(
                "/upload/",
                files={"file": ("invalid.txt", f, "text/plain")}
            )
        assert response.status_code == 400  # Agora esperamos 400 para arquivo inválido
    finally:
        if os.path.exists("invalid.txt"):
            os.remove("invalid.txt")