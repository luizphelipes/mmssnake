#!/usr/bin/env python3
"""
Script de teste para validar conexão com PostgreSQL.
Execute este script para verificar se a configuração PostgreSQL está funcionando.
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório atual ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_postgresql_connection():
    """Testa a conexão com PostgreSQL usando a configuração atual."""
    
    print("=" * 60)
    print("TESTE DE CONEXÃO POSTGRESQL")
    print("=" * 60)
    
    # Importar módulos necessários
    try:
        from database import validate_postgresql_connection, parse_postgresql_url
    except ImportError as e:
        print(f"❌ Erro ao importar módulos: {e}")
        return False
    
    # Obter URL do banco de dados
    database_url = os.getenv("DATABASE_URL", "sqlite:///mmssnake.db")
    print(f"URL do banco de dados: {database_url}")
    
    # Verificar se é PostgreSQL
    if not (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
        print("ℹ️  URL não é PostgreSQL. Teste não aplicável.")
        return True
    
    # Normalizar URL se necessário
    if database_url.startswith("postgres://"):
        original_url = database_url
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        print(f"ℹ️  URL normalizada: {original_url} → {database_url}")
    
    # Extrair informações da URL
    url_info = parse_postgresql_url(database_url)
    if url_info:
        print(f"\nInformações da conexão:")
        print(f"  Host: {url_info['host']}")
        print(f"  Porta: {url_info['port']}")
        print(f"  Database: {url_info['database']}")
        if url_info.get('query_params'):
            print(f"  Parâmetros: {url_info['query_params']}")
        print(f"  Usuário: {url_info['username']}")
        print(f"  Senha configurada: {'Sim' if url_info['has_password'] else 'Não'}")
    
    # Testar conexão
    print(f"\nTestando conexão...")
    is_connected, error_details = validate_postgresql_connection(database_url)
    
    if is_connected:
        print("✅ Conexão PostgreSQL estabelecida com sucesso!")
        return True
    else:
        print("❌ Falha na conexão PostgreSQL:")
        print(f"   {error_details}")
        
        # Sugestões específicas baseadas no erro
        if "Can't load plugin" in error_details:
            print("\n💡 Sugestão: Verifique se o psycopg2-binary está instalado:")
            print("   pip install psycopg2-binary")
        elif "Not an executable object" in error_details:
            print("\n💡 Sugestão: Erro de execução SQL. Verifique a versão do SQLAlchemy:")
            print("   pip install --upgrade SQLAlchemy")
        elif "authentication failed" in error_details:
            print("\n💡 Sugestão: Verifique as credenciais do PostgreSQL")
        elif "connection refused" in error_details:
            print("\n💡 Sugestão: Verifique se o PostgreSQL está rodando")
        elif "database" in error_details and "does not exist" in error_details:
            print("\n💡 Sugestão: Crie o database especificado")
        
        return False

def test_database_initialization():
    """Testa a inicialização do banco de dados."""
    
    print(f"\n" + "=" * 60)
    print("TESTE DE INICIALIZAÇÃO DO BANCO DE DADOS")
    print("=" * 60)
    
    try:
        from database import initialize_database
        initialize_database()
        print("✅ Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando testes de banco de dados...\n")
    
    # Testar conexão PostgreSQL
    connection_ok = test_postgresql_connection()
    
    # Testar inicialização do banco
    initialization_ok = test_database_initialization()
    
    print(f"\n" + "=" * 60)
    print("RESULTADO DOS TESTES")
    print("=" * 60)
    
    if connection_ok and initialization_ok:
        print("✅ Todos os testes passaram!")
        print("✅ Sistema pronto para uso.")
        sys.exit(0)
    else:
        print("❌ Alguns testes falharam.")
        print("❌ Verifique a configuração do banco de dados.")
        sys.exit(1) 