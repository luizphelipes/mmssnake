#!/usr/bin/env python3
"""
Script de diagnóstico específico para problemas de PostgreSQL.
Execute este script para diagnosticar problemas específicos de conexão.
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório atual ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def diagnose_postgresql_issues():
    """Diagnostica problemas específicos de PostgreSQL."""
    
    print("=" * 60)
    print("DIAGNÓSTICO POSTGRESQL")
    print("=" * 60)
    
    # 1. Verificar URL do banco de dados
    database_url = os.getenv("DATABASE_URL", "sqlite:///mmssnake.db")
    print(f"URL do banco de dados: {database_url}")
    
    if not (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
        print("ℹ️  URL não é PostgreSQL. Diagnóstico não aplicável.")
        return
    
    # 2. Verificar dependências
    print(f"\n" + "=" * 40)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS")
    print("=" * 40)
    
    try:
        import psycopg2
        print("✅ psycopg2 instalado")
    except ImportError:
        print("❌ psycopg2 não instalado")
        print("💡 Execute: pip install psycopg2-binary")
        return
    
    try:
        from sqlalchemy import create_engine, text
        print("✅ SQLAlchemy com text() disponível")
    except ImportError:
        print("❌ SQLAlchemy não disponível")
        return
    
    # 3. Testar criação de engine
    print(f"\n" + "=" * 40)
    print("TESTE DE CRIAÇÃO DE ENGINE")
    print("=" * 40)
    
    try:
        # Normalizar URL
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(database_url, echo=False)
        print("✅ Engine criado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao criar engine: {e}")
        return
    
    # 4. Testar conexão
    print(f"\n" + "=" * 40)
    print("TESTE DE CONEXÃO")
    print("=" * 40)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Query de teste executada com sucesso")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        
        # Análise específica do erro
        error_str = str(e).lower()
        if "authentication failed" in error_str:
            print("💡 Problema: Credenciais incorretas")
            print("   Verifique usuário e senha na URL")
        elif "connection refused" in error_str:
            print("💡 Problema: PostgreSQL não está rodando")
            print("   Verifique se o serviço está ativo")
        elif "database" in error_str and "does not exist" in error_str:
            print("💡 Problema: Database não existe")
            print("   Crie o database especificado")
        elif "not an executable object" in error_str:
            print("💡 Problema: Versão do SQLAlchemy")
            print("   Execute: pip install --upgrade SQLAlchemy")
        else:
            print("💡 Problema não identificado")
            print("   Verifique logs detalhados acima")
        return
    
    # 5. Testar versão do PostgreSQL
    print(f"\n" + "=" * 40)
    print("INFORMAÇÕES DO POSTGRESQL")
    print("=" * 40)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Versão PostgreSQL: {version}")
    except Exception as e:
        print(f"❌ Erro ao obter versão: {e}")
    
    # 6. Testar permissões
    print(f"\n" + "=" * 40)
    print("TESTE DE PERMISSÕES")
    print("=" * 40)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_user, current_database()"))
            user, database = result.fetchone()
            print(f"✅ Usuário atual: {user}")
            print(f"✅ Database atual: {database}")
    except Exception as e:
        print(f"❌ Erro ao verificar permissões: {e}")
    
    print(f"\n" + "=" * 60)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("=" * 60)
    print("✅ PostgreSQL está funcionando corretamente!")

if __name__ == "__main__":
    diagnose_postgresql_issues() 