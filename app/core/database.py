from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL do banco de dados para uso com AsyncEngine
DATABASE_URL = "postgresql+asyncpg://admin:admin@postgres:5432/boletos"

# Cria o engine assíncrono
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Factory para criar sessões assíncronas
async_session_factory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base para os modelos do SQLAlchemy
Base = declarative_base()

# Função para inicializar tabelas no banco de dados
async def init_db():
    """
    Cria as tabelas no banco de dados com base nos modelos, caso ainda não existam.
    Isso é útil para ambiente de desenvolvimento e evita sobrescrever tabelas existentes.
    """
    async with async_engine.begin() as conn:
        # Criação de tabelas baseadas nos modelos
        await conn.run_sync(Base.metadata.create_all)
