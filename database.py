from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError, InvalidRequestError
import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def validate_postgresql_connection(database_url):
    """
    Valida a conexão com PostgreSQL e retorna detalhes do erro se houver.
    """
    try:
        # Normalizar URL para usar postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # Tentar criar engine temporário para testar conexão
        test_engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=1,
            max_overflow=0
        )
        
        # Testar conexão usando text() para a query
        with test_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        
        test_engine.dispose()
        return True, None
        
    except ImportError as e:
        error_msg = f"Driver PostgreSQL não disponível: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
        
    except OperationalError as e:
        error_code = getattr(e.orig, 'pgcode', 'UNKNOWN')
        error_msg = getattr(e.orig, 'pgerror', str(e))
        
        if "authentication failed" in str(e).lower():
            error_details = f"Erro de autenticação PostgreSQL (código {error_code}): {error_msg}"
        elif "connection refused" in str(e).lower():
            error_details = f"PostgreSQL não está acessível (código {error_code}): {error_msg}"
        elif "database" in str(e).lower() and "does not exist" in str(e).lower():
            error_details = f"Database PostgreSQL não existe (código {error_code}): {error_msg}"
        elif "role" in str(e).lower() and "does not exist" in str(e).lower():
            error_details = f"Usuário PostgreSQL não existe (código {error_code}): {error_msg}"
        else:
            error_details = f"Erro de conexão PostgreSQL (código {error_code}): {error_msg}"
        
        logger.error(error_details)
        return False, error_details
        
    except Exception as e:
        error_details = f"Erro inesperado ao conectar com PostgreSQL: {str(e)}"
        logger.error(error_details)
        return False, error_details

def parse_postgresql_url(database_url):
    """
    Extrai informações da URL do PostgreSQL para diagnóstico.
    """
    try:
        # Normalizar URL
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # Remover prefixo postgresql://
        clean_url = database_url.replace('postgresql://', '')
        
        # Separar credenciais e host
        if '@' in clean_url:
            credentials, rest = clean_url.split('@', 1)
            if ':' in credentials:
                username, password = credentials.split(':', 1)
            else:
                username, password = credentials, ''
        else:
            username, password = '', ''
            rest = clean_url
        
        # Separar host e database (incluindo parâmetros de query)
        if '/' in rest:
            host_part, database_part = rest.split('/', 1)
            
            # Remover parâmetros de query do database
            if '?' in database_part:
                database, query_params = database_part.split('?', 1)
            else:
                database = database_part
                query_params = ''
            
            if ':' in host_part:
                host, port = host_part.split(':', 1)
            else:
                host, port = host_part, '5432'
        else:
            host, port = rest, '5432'
            database = ''
            query_params = ''
        
        return {
            'username': username,
            'host': host,
            'port': port,
            'database': database,
            'query_params': query_params,
            'has_password': bool(password)
        }
    except Exception:
        return None

# Obter URL do banco de dados do .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mmssnake.db")

# Verificar se é uma URL PostgreSQL
if DATABASE_URL and (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")):
    logger.info("Detectada configuração PostgreSQL. Validando conexão...")
    
    # Normalizar URL para usar postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        logger.info("URL normalizada para postgresql://")
    
    # Extrair informações da URL para diagnóstico
    url_info = parse_postgresql_url(DATABASE_URL)
    if url_info:
        logger.info(f"Tentando conectar ao PostgreSQL: {url_info['host']}:{url_info['port']}/{url_info['database']}")
    
    # Validar conexão
    is_connected, error_details = validate_postgresql_connection(DATABASE_URL)
    
    if not is_connected:
        logger.error("=" * 80)
        logger.error("ERRO DE CONEXÃO POSTGRESQL")
        logger.error("=" * 80)
        logger.error(f"Detalhes do erro: {error_details}")
        
        if url_info:
            logger.error("Informações da conexão:")
            logger.error(f"  Host: {url_info['host']}")
            logger.error(f"  Porta: {url_info['port']}")
            logger.error(f"  Database: {url_info['database']}")
            if url_info['query_params']:
                logger.error(f"  Parâmetros: {url_info['query_params']}")
            logger.error(f"  Usuário: {url_info['username']}")
            logger.error(f"  Senha configurada: {'Sim' if url_info['has_password'] else 'Não'}")
        
        logger.error("Soluções possíveis:")
        logger.error("1. Verificar se o PostgreSQL está rodando")
        logger.error("2. Verificar se as credenciais estão corretas")
        logger.error("3. Verificar se o database existe")
        logger.error("4. Verificar se o usuário tem permissões adequadas")
        logger.error("5. Verificar se a porta está acessível")
        logger.error("6. Verificar se o driver psycopg2 está instalado")
        logger.error("7. Verificar se a URL usa postgresql:// em vez de postgres://")
        logger.error("=" * 80)
        
        logger.warning("FALLBACK: Usando SQLite como banco de dados alternativo")
        DATABASE_URL = "sqlite:///mmssnake.db"
    else:
        logger.info("Conexão PostgreSQL estabelecida com sucesso!")
else:
    logger.info("Usando SQLite como banco de dados padrão")

# Se não houver DATABASE_URL configurado, usar SQLite local
if not DATABASE_URL or DATABASE_URL == "":
    DATABASE_URL = "sqlite:///mmssnake.db"

logger.info(f"URL final do banco de dados: {DATABASE_URL}")

# Configurar engine
try:
    engine = create_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        pool_recycle=540,
        pool_size=5,
        max_overflow=10
    )
    logger.info("Engine do banco de dados configurado com sucesso")
except Exception as e:
    logger.error(f"Erro ao configurar engine do banco de dados: {e}")
    raise

Session = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

def initialize_database():
    from models.base import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()