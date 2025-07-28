# Exemplos de Uso da API de Produtos

Este documento demonstra como usar o endpoint `POST /products` para adicionar produtos únicos e múltiplos produtos.

## Configuração

Certifique-se de que o servidor está rodando:
```bash
python app.py
```

## Exemplos com cURL

### 1. Adicionar um Produto Único

```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "FOLLOWERS1000",
    "service_id": 123,
    "api": "machinesmm",
    "base_quantity": 1000,
    "type": "followers"
  }'
```

**Resposta esperada:**
```json
{
  "message": "Produto adicionado com sucesso"
}
```

### 2. Adicionar Múltiplos Produtos

```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '[
    {
      "sku": "FOLLOWERS1000",
      "service_id": 123,
      "api": "machinesmm",
      "base_quantity": 1000,
      "type": "followers"
    },
    {
      "sku": "LIKES500",
      "service_id": 456,
      "api": "worldsmm",
      "base_quantity": 500,
      "type": "likes"
    },
    {
      "sku": "VIEWS200",
      "service_id": 789,
      "api": "smmclouduk",
      "base_quantity": 200,
      "type": "views"
    }
  ]'
```

**Resposta esperada:**
```json
{
  "message": "3 produtos adicionados com sucesso",
  "added_products": [
    {
      "sku": "FOLLOWERS1000",
      "service_id": 123,
      "api": "machinesmm",
      "base_quantity": 1000,
      "type": "followers"
    },
    {
      "sku": "LIKES500",
      "service_id": 456,
      "api": "worldsmm",
      "base_quantity": 500,
      "type": "likes"
    },
    {
      "sku": "VIEWS200",
      "service_id": 789,
      "api": "smmclouduk",
      "base_quantity": 200,
      "type": "views"
    }
  ]
}
```

### 3. Testar Validação de Erros

```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '[
    {
      "sku": "VALID001",
      "service_id": 123,
      "api": "machinesmm",
      "base_quantity": 1000,
      "type": "followers"
    },
    {
      "sku": "INVALID001",
      "service_id": 456,
      "base_quantity": 500,
      "type": "likes"
    }
  ]'
```

**Resposta esperada (erro):**
```json
{
  "error": "Erros de validação encontrados",
  "details": [
    "Produto 2: Campos obrigatórios ausentes: api"
  ]
}
```

### 4. Testar SKU Duplicado

```bash
# Primeiro, adicionar um produto
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "DUPLICATE001",
    "service_id": 123,
    "api": "machinesmm",
    "base_quantity": 1000,
    "type": "followers"
  }'

# Depois, tentar adicionar o mesmo SKU novamente
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "DUPLICATE001",
    "service_id": 456,
    "api": "worldsmm",
    "base_quantity": 500,
    "type": "likes"
  }'
```

**Resposta esperada (erro):**
```json
{
  "error": "Erros de validação encontrados",
  "details": [
    "Produto 1: SKU DUPLICATE001 já existe"
  ]
}
```

### 5. Listar Todos os Produtos

```bash
curl -X GET http://localhost:5000/api/products
```

**Resposta esperada:**
```json
[
  {
    "sku": "FOLLOWERS1000",
    "service_id": 123,
    "api": "machinesmm",
    "base_quantity": 1000,
    "type": "followers"
  },
  {
    "sku": "LIKES500",
    "service_id": 456,
    "api": "worldsmm",
    "base_quantity": 500,
    "type": "likes"
  }
]
```

## Exemplos com Python

### Usando requests

```python
import requests
import json

# Configuração
BASE_URL = "http://localhost:5000/api"
HEADERS = {"Content-Type": "application/json"}

# Adicionar múltiplos produtos
products_data = [
    {
        "sku": "PYTHON001",
        "service_id": 123,
        "api": "machinesmm",
        "base_quantity": 1000,
        "type": "followers"
    },
    {
        "sku": "PYTHON002",
        "service_id": 456,
        "api": "worldsmm",
        "base_quantity": 500,
        "type": "likes"
    }
]

response = requests.post(f"{BASE_URL}/products", 
                       json=products_data, 
                       headers=HEADERS)

print(f"Status: {response.status_code}")
print(f"Resposta: {json.dumps(response.json(), indent=2)}")
```

## Campos Obrigatórios

Todos os produtos devem conter os seguintes campos:

- `sku`: Código único do produto (string)
- `service_id`: ID do serviço na API SMM (integer)
- `api`: Nome da API a ser usada (string)
  - Valores válidos: `machinesmm`, `worldsmm`, `smmclouduk`
- `base_quantity`: Quantidade base por unidade (integer)
- `type`: Tipo de serviço (string)
  - Valores válidos: `followers`, `likes`, `views`, `stories`

## Códigos de Status HTTP

- `201 Created`: Produto(s) adicionado(s) com sucesso
- `400 Bad Request`: Erros de validação
- `409 Conflict`: SKU já existe (quando adicionando produto único)
- `500 Internal Server Error`: Erro interno do servidor

## Executar Testes

Para executar os testes automatizados:

```bash
python test_products_endpoint.py
```

Este script testa todos os cenários mencionados acima e demonstra o funcionamento do endpoint modificado. 