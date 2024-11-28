from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL do banco de dados
DATABASE_URL = "postgresql+psycopg2://admin:admin@postgres:5432/boletos"

# Criar o engine
engine = create_engine(DATABASE_URL)

# Criar uma fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos do SQLAlchemy
Base = declarative_base()
