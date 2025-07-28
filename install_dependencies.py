#!/usr/bin/env python3
"""
Script para verificar e instalar dependências PostgreSQL.
Execute este script para garantir que todas as dependências estão corretas.
"""

import subprocess
import sys
import os

def check_package(package_name):
    """Verifica se um pacote está instalado."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Instala um pacote usando pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("=" * 60)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS POSTGRESQL")
    print("=" * 60)
    
    # Verificar dependências básicas
    dependencies = [
        ("sqlalchemy", "SQLAlchemy"),
        ("psycopg2", "psycopg2-binary"),
        ("dotenv", "python-dotenv"),
        ("flask", "Flask")
    ]
    
    all_ok = True
    
    for module_name, package_name in dependencies:
        print(f"\nVerificando {package_name}...")
        
        if check_package(module_name):
            print(f"✅ {package_name} já está instalado")
        else:
            print(f"❌ {package_name} não está instalado")
            print(f"Instalando {package_name}...")
            
            if install_package(package_name):
                print(f"✅ {package_name} instalado com sucesso")
            else:
                print(f"❌ Falha ao instalar {package_name}")
                all_ok = False
    
    # Teste específico do PostgreSQL
    print(f"\n" + "=" * 60)
    print("TESTE ESPECÍFICO DO POSTGRESQL")
    print("=" * 60)
    
    try:
        import psycopg2
        print("✅ psycopg2 importado com sucesso")
        
        # Testar se o SQLAlchemy consegue usar o driver
        from sqlalchemy import create_engine
        test_url = "postgresql://test:test@localhost:5432/test"
        engine = create_engine(test_url, echo=False)
        print("✅ SQLAlchemy consegue criar engine PostgreSQL")
        
    except ImportError as e:
        print(f"❌ Erro ao importar psycopg2: {e}")
        all_ok = False
    except Exception as e:
        print(f"⚠️  SQLAlchemy não consegue usar PostgreSQL (normal se não estiver rodando): {e}")
    
    print(f"\n" + "=" * 60)
    print("RESULTADO")
    print("=" * 60)
    
    if all_ok:
        print("✅ Todas as dependências estão corretas!")
        print("✅ Sistema pronto para usar PostgreSQL")
    else:
        print("❌ Algumas dependências falharam")
        print("❌ Verifique os erros acima")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 