#!/usr/bin/env python3
"""
Script de teste para o endpoint de produtos modificado
Demonstra como adicionar produtos únicos e múltiplos produtos
"""

import requests
import json

# Configuração
BASE_URL = "http://localhost:5000/api"
HEADERS = {"Content-Type": "application/json"}

def test_single_product():
    """Testa adicionar um produto único"""
    print("=== Testando Produto Único ===")
    
    product_data = {
        "sku": "TEST001",
        "service_id": 123,
        "api": "machinesmm",
        "base_quantity": 1000,
        "type": "followers"
    }
    
    response = requests.post(f"{BASE_URL}/products", 
                           json=product_data, 
                           headers=HEADERS)
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    print()

def test_multiple_products():
    """Testa adicionar múltiplos produtos"""
    print("=== Testando Múltiplos Produtos ===")
    
    products_data = [
        {
            "sku": "TEST002",
            "service_id": 456,
            "api": "worldsmm",
            "base_quantity": 500,
            "type": "likes"
        },
        {
            "sku": "TEST003",
            "service_id": 789,
            "api": "smmclouduk",
            "base_quantity": 200,
            "type": "views"
        },
        {
            "sku": "TEST004",
            "service_id": 101,
            "api": "machinesmm",
            "base_quantity": 300,
            "type": "stories"
        }
    ]
    
    response = requests.post(f"{BASE_URL}/products", 
                           json=products_data, 
                           headers=HEADERS)
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    print()

def test_validation_errors():
    """Testa validação de erros"""
    print("=== Testando Validação de Erros ===")
    
    # Produto com campos faltando
    invalid_product = {
        "sku": "TEST005",
        "service_id": 123,
        # "api" faltando
        "base_quantity": 1000,
        "type": "followers"
    }
    
    response = requests.post(f"{BASE_URL}/products", 
                           json=invalid_product, 
                           headers=HEADERS)
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    print()

def test_duplicate_sku():
    """Testa SKU duplicado"""
    print("=== Testando SKU Duplicado ===")
    
    # Primeiro, adicionar um produto
    product_data = {
        "sku": "TEST006",
        "service_id": 123,
        "api": "machinesmm",
        "base_quantity": 1000,
        "type": "followers"
    }
    
    response = requests.post(f"{BASE_URL}/products", 
                           json=product_data, 
                           headers=HEADERS)
    print(f"Primeiro produto - Status: {response.status_code}")
    
    # Tentar adicionar o mesmo SKU novamente
    response = requests.post(f"{BASE_URL}/products", 
                           json=product_data, 
                           headers=HEADERS)
    
    print(f"SKU duplicado - Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    print()

def test_mixed_validation():
    """Testa validação mista com produtos válidos e inválidos"""
    print("=== Testando Validação Mista ===")
    
    mixed_products = [
        {
            "sku": "TEST007",
            "service_id": 123,
            "api": "machinesmm",
            "base_quantity": 1000,
            "type": "followers"
        },
        {
            "sku": "TEST008",
            "service_id": 456,
            # "api" faltando
            "base_quantity": 500,
            "type": "likes"
        },
        {
            "sku": "TEST009",
            "service_id": 789,
            "api": "smmclouduk",
            "base_quantity": 200,
            "type": "views"
        }
    ]
    
    response = requests.post(f"{BASE_URL}/products", 
                           json=mixed_products, 
                           headers=HEADERS)
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    print()

def list_products():
    """Lista todos os produtos"""
    print("=== Listando Produtos ===")
    
    response = requests.get(f"{BASE_URL}/products")
    
    print(f"Status: {response.status_code}")
    products = response.json()
    print(f"Total de produtos: {len(products)}")
    for product in products:
        print(f"- {product['sku']}: {product['type']} ({product['api']})")
    print()

if __name__ == "__main__":
    print("🚀 Testando Endpoint de Produtos Modificado")
    print("=" * 50)
    
    try:
        # Testar produto único
        test_single_product()
        
        # Testar múltiplos produtos
        test_multiple_products()
        
        # Testar validação de erros
        test_validation_errors()
        
        # Testar SKU duplicado
        test_duplicate_sku()
        
        # Testar validação mista
        test_mixed_validation()
        
        # Listar produtos
        list_products()
        
        print("✅ Todos os testes concluídos!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor.")
        print("Certifique-se de que o servidor está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}") 