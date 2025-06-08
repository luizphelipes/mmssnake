from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Obter URL do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")

# Ajustar a URL para psycopg2 + SSL
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# Adicionar parâmetros SSL diretamente na URL (se necessário)
# if not DATABASE_URL.endswith("?sslmode=require"):
#     DATABASE_URL += "?sslmode=require"  # Apenas se o servidor exigir SSL

# Configurar engine sem o parâmetro 'ssl' inválido
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=540,
    pool_size=5,
    max_overflow=10
)

Session = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

def initialize_database():
    from models.base import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Banco inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
        raise

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()