from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Obter URL do banco de dados do .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mmssnake.db")

# Forçar uso de SQLite se não houver suporte ao PostgreSQL
if DATABASE_URL and DATABASE_URL.startswith("postgres"):
    logger.warning("PostgreSQL não está disponível. Usando SQLite como fallback.")
    DATABASE_URL = "sqlite:///mmssnake.db"

# Se não houver DATABASE_URL configurado, usar SQLite local
if not DATABASE_URL or DATABASE_URL == "":
    DATABASE_URL = "sqlite:///mmssnake.db"

logger.info(f"Usando banco de dados: {DATABASE_URL}")

# Configurar engine
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