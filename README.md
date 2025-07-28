# Sistema de Automação de Serviços Instagram

## Visão Geral

Este projeto é um sistema de automação para processar pedidos da plataforma e-commerce Yampi e fornecer serviços de Instagram, como adição de seguidores e likes a perfis. O sistema funciona como um intermediário que recebe webhooks da Yampi quando pedidos são pagos, processa os pedidos e executa os serviços solicitados através de APIs de terceiros de SMM (Social Media Marketing).

## Funcionalidades Principais

- **Processamento de Webhooks**: Recebe notificações da Yampi quando um pedido é pago
- **Validação de Perfis**: Verifica se o perfil do Instagram fornecido é válido e público
- **Serviços Automatizados**: Fornece serviços de seguidores, likes, views e stories para contas do Instagram
- **Execução Programada**: Verifica periodicamente pedidos pendentes e atualiza status
- **Gestão de Produtos**: Armazena e gerencia configurações de produtos/serviços
- **Sistema de Restrição de Brindes**: Controle rigoroso para produtos gratuitos (SKU: 9R628ZD4Y)
- **Verificação por IP**: Prevenção de abusos através de controle por endereço IP
- **Webhook Externo**: Encaminhamento de webhooks para sistemas externos

## Tecnologias Utilizadas

- **Framework Web**: Flask
- **ORM**: SQLAlchemy
- **Banco de Dados**: SQLite (padrão) / PostgreSQL (opcional)
- **Tarefas Agendadas**: Biblioteca `schedule`
- **Processamento de Requisições**: Requests
- **Deployment**: Docker & Docker Compose
- **Containerização**: Docker

## Configuração do Banco de Dados

### SQLite (Padrão)
O sistema usa SQLite por padrão, que é adequado para desenvolvimento e pequenas aplicações:

```bash
DATABASE_URL="sqlite:///mmssnake.db"
```

### PostgreSQL (Recomendado para Produção)
Para ambientes de produção, recomenda-se usar PostgreSQL:

```bash
# Exemplo de configuração PostgreSQL
DATABASE_URL="postgresql://usuario:senha@localhost:5432/mmssnake"
```

#### Configuração com Docker Compose
O arquivo `docker-compose.yml` inclui um serviço PostgreSQL opcional. Para ativá-lo:

1. Descomente as linhas do serviço `postgres` no `docker-compose.yml`
2. Descomente a linha `DATABASE_URL` do PostgreSQL no serviço `web`
3. Descomente as linhas `depends_on` e `volumes`

#### Tratamento de Erros PostgreSQL
O sistema inclui tratamento detalhado de erros para PostgreSQL:

- **Validação de Conexão**: Testa conectividade antes de usar
- **Diagnóstico Detalhado**: Identifica problemas específicos (autenticação, database inexistente, etc.)
- **Fallback Automático**: Usa SQLite se PostgreSQL não estiver disponível
- **Logs Informativos**: Fornece informações detalhadas sobre problemas de conexão

#### Teste de Conexão
Execute o script de teste para validar a configuração PostgreSQL:

```bash
python test_postgresql.py
```

Este script irá:
- Validar a conexão com PostgreSQL
- Verificar se o driver psycopg2 está instalado
- Testar a inicialização do banco de dados
- Fornecer diagnóstico detalhado em caso de erro

## Estrutura do Projeto

```
├── .env                  # Variáveis de ambiente (NÃO DEVE SER COMMITADO)
├── app.py                # Ponto de entrada da aplicação
├── database.py           # Configuração do banco de dados
├── test_postgresql.py    # Script de teste para PostgreSQL
├── models/               # Modelos de dados
│   └── base.py           # Definições das tabelas SQLAlchemy
├── routes/               # Rotas da API
│   ├── __init__.py       # Inicialização de blueprints
│   ├── payments.py       # Endpoints para gerenciamento de pagamentos
│   └── webhooks.py       # Endpoints para receber webhooks da Yampi
├── services/             # Serviços para lógica de negócio
│   ├── __init__.py
│   ├── instagram_service.py  # Interação com APIs do Instagram
│   ├── scheduler.py      # Agendador de tarefas periódicas
│   └── yampi_client.py   # Cliente para API da Yampi
├── utils.py              # Funções utilitárias
├── docker-compose.yml    # Configuração Docker Compose
├── Dockerfile            # Configuração Docker
├── Dockerfile.simple     # Dockerfile simplificado
├── easypanel.json        # Configuração do Easypanel
├── requirements.txt      # Dependências do projeto
└── .dockerignore         # Arquivos ignorados no build Docker
```

## Modelos de Dados

### ProductServices
Armazena informações sobre os serviços/produtos disponíveis:
- `sku`: Código único do produto (chave primária)
- `service_id`: ID do serviço na API do SMM
- `api`: Nome da API a ser usada (ex: 'machinesmm', 'worldsmm', 'smmclouduk')
- `base_quantity`: Quantidade base por unidade do produto
- `type`: Tipo de serviço (ex: 'followers', 'likes', 'views', 'stories')

### Payments
Armazena informações sobre pagamentos e pedidos:
- `id`: ID único do pagamento (chave primária)
- `order_id`: ID do pedido na Yampi
- `status_alias`: Status do pagamento (ex: 'paid', 'delivered', 'cancelled', 'shipment_exception')
- `customer_name`: Nome do cliente
- `email`: Email do cliente
- `phone_full_number`: Número de telefone
- `customer_ip`: Endereço IP do cliente (para controle de brindes)
- `item_sku`: SKU do item comprado
- `item_quantity`: Quantidade comprada
- `customization`: Nome de usuário do Instagram fornecido
- `finished`: Flag indicando se o pedido foi processado (0/1)
- `profile_status`: Status do perfil ('public', 'private', 'error', 'pending')

## Serviços

### YampiClient
Responsável pela comunicação com a API da Yampi:
- Atualização de status de pedidos
- Gerenciamento de credenciais da API
- Mapeamento de status (cancelled, delivered, shipment_exception, etc.)

### InstagramService
Gerencia a interação com o Instagram via APIs de terceiros:
- Verificação de privacidade de perfis
- Obtenção de informações de mídia do usuário
- Extração de IDs de posts para likes
- Extração de IDs de reels para views
- Pool de sessões para melhor performance

### Scheduler
Gerencia as tarefas periódicas:
- Verificação de perfis pendentes a cada 10 minutos
- Processamento de pagamentos pendentes a cada 2 minutos
- Atualização de pedidos entregues 5x por dia (9h, 15h, 19h, 21h, 23h)

## Exemplo de Uso com PostgreSQL

### 1. Configuração Inicial

Copie o arquivo de exemplo e configure as variáveis:

```bash
cp env.example .env
```

Edite o arquivo `.env` e configure o PostgreSQL:

```bash
# Para PostgreSQL local
DATABASE_URL="postgresql://usuario:senha@localhost:5432/mmssnake"

# Para PostgreSQL com Docker
DATABASE_URL="postgresql://mmssnake_user:mmssnake_password@postgres:5432/mmssnake"
```

### 2. Teste de Conexão

Execute o script de teste para verificar se tudo está funcionando:

```bash
python test_postgresql.py
```

### 3. Execução com Docker

Para usar PostgreSQL com Docker Compose:

```bash
# Edite docker-compose.yml e descomente as linhas do PostgreSQL
# Execute o sistema
docker-compose up -d
```

### 4. Logs de Erro

Se houver problemas com PostgreSQL, o sistema irá:

1. **Detectar automaticamente** problemas de conexão
2. **Fornecer diagnóstico detalhado** com códigos de erro PostgreSQL
3. **Fazer fallback para SQLite** automaticamente
4. **Registrar logs informativos** para troubleshooting

Exemplo de log de erro:

```
================================================================================
ERRO DE CONEXÃO POSTGRESQL
================================================================================
Detalhes do erro: Erro de autenticação PostgreSQL (código 28P01): password authentication failed for user "usuario"
Informações da conexão:
  Host: localhost
  Porta: 5432
  Database: mmssnake
  Usuário: usuario
  Senha configurada: Sim
Soluções possíveis:
1. Verificar se o PostgreSQL está rodando
2. Verificar se as credenciais estão corretas
3. Verificar se o database existe
4. Verificar se o usuário tem permissões adequadas
5. Verificar se a porta está acessível
6. Verificar se o driver psycopg2 está instalado
================================================================================
FALLBACK: Usando SQLite como banco de dados alternativo
```

## Sistema de Restrição de Brindes

### SKU Restrito: 9R628ZD4Y
O sistema implementa restrições rigorosas para produtos brinde:

#### **5 Níveis de Verificação:**
1. **Histórico Global (Username)**: Verifica se o usuário já utilizou o brinde em qualquer pedido
2. **Histórico por IP**: Verifica se o mesmo IP já utilizou o brinde anteriormente
3. **Quantidade no Pedido**: Verifica se já processou 1 unidade neste pedido
4. **Duplicação no Pedido**: Verifica se já existe registro para este SKU+username no pedido
5. **Quantidade do Item**: Limita a quantidade a 1 unidade por item

#### **Comportamento Inteligente:**
- **Se SÓ brindes inválidos**: Cancela o pedido inteiro
- **Se produtos pagos + brindes inválidos**: Remove apenas os brindes, mantém produtos pagos
- **Se produtos pagos + brindes válidos**: Processa normalmente

#### **Logs Detalhados:**
- Contadores de itens válidos, inválidos e processados
- Logs específicos para cada tipo de violação
- Auditoria completa de todas as decisões

## Fluxo de Processamento de Pedidos

### **1. Recebimento do Webhook**
- Validação da assinatura HMAC-SHA256
- Extração de dados do cliente (nome, email, telefone, IP)
- Verificação de customização (username do Instagram)

### **2. Verificação de Perfil**
- Sanitização do username (remove @, URLs, etc.)
- Verificação de privacidade via API do Instagram
- Se privado/erro: status `shipment_exception`
- Se público: continua processamento

### **3. Sistema de Restrição (para brindes)**
- Verificação de histórico global por username
- Verificação de histórico por IP
- Verificação de quantidade no pedido
- Verificação de duplicação
- Limitação de quantidade

### **4. Salvamento e Processamento**
- Criação de registro no banco de dados
- Adição à fila de processamento
- Envio de webhook externo (se configurado)

### **5. Execução de Serviços**
- Agendador verifica pedidos pendentes a cada 2 minutos
- Execução via API de SMM correspondente
- Para likes: distribuição entre posts (máximo 4)
- Para views: distribuição entre reels (máximo 4)
- Para stories: processamento direto do perfil de stories
- Para seguidores: processamento direto do perfil
- Marcação como `finished=1` após sucesso

### **6. Atualização de Status**
- Atualização para `delivered` no Yampi
- Atualização de `status_alias` no banco local
- Preservação do histórico (não apaga registros)

## Configuração do Ambiente

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# Banco de Dados (opcional - padrão: SQLite local)
DATABASE_URL="sqlite:///mmssnake.db"

# Yampi API
YAMPI_API_KEY="sua_api_key"
YAMPI_SECRET_KEY="sua_secret_key"
YAMPI_BASE_URL="https://api.yampi.com.br"
YAMPI_WEBHOOK_SECRET="sua_chave_secreta_webhook"

# APIs SMM
MACHINESMM_API_KEY="sua_api_key_machinesmm"
WORLDSMM_API_KEY="sua_api_key_worldsmm"
SMMCLOUDUK_API_KEY="sua_api_key_smmclouduk"

# APIs Instagram
LOOTER_API="sua_api_key_looter"
INSTAGRAM230_API="sua_api_key_instagram230"

# IDs de Sessão do Instagram (opcional)
INSTAGRAM_SESSION_ID_1="sua_session_id_1"
INSTAGRAM_SESSION_ID_2="sua_session_id_2"
# ... adicione quantas contas precisar
```

### 2. Configuração do Banco de Dados

O sistema suporta diferentes tipos de banco de dados através da variável `DATABASE_URL`:

- **SQLite (padrão)**: `sqlite:///mmssnake.db`
- **PostgreSQL**: `postgresql://usuario:senha@host:porta/database`
- **MySQL**: `mysql://usuario:senha@host:porta/database`

Se `DATABASE_URL` não estiver configurado, o sistema usará SQLite local automaticamente.

### 3. Instalação Local

1. Clone o repositório:
   ```bash
   git clone <url-do-repositorio>
   cd mmssnake
   ```

2. Configure o arquivo `.env`:
   ```bash
   cp env.example .env
   # Edite o arquivo .env com suas configurações
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute a aplicação:
   ```bash
   python app.py
   ```

### 4. Instalação com Docker

1. Clone o repositório e configure o `.env`

2. Execute com Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Ou execute apenas o container:
   ```bash
   docker build -t mmssnake .
   docker run -p 5000:5000 --env-file .env mmssnake
   ```

### 5. Deployment no Easypanel

1. Conecte seu repositório GitHub ao Easypanel
2. Configure as variáveis de ambiente conforme `easypanel.json`
3. Use o `Dockerfile.simple` para maior compatibilidade

## Endpoints da API

### Webhooks
- `POST /webhook`: Recebe webhooks da Yampi
- `POST /update-order-status`: Atualiza status de um pedido na Yampi

### Pagamentos
- `GET /payments`: Lista todos os pagamentos
- `PUT /payments/<id>`: Atualiza um pagamento
- `DELETE /payments/<id>`: Deleta um pagamento

### Produtos
- `GET /products`: Lista todos os produtos
- `POST /products`: Adiciona um novo produto
- `DELETE /products/<sku>`: Deleta um produto

## Manutenção e Troubleshooting

### Logs
A aplicação utiliza o módulo `logging` do Python para registrar eventos importantes. Os logs incluem:
- Erros de processamento de webhook
- Status de verificação de perfis
- Resultados de chamadas de API para serviços SMM
- Execução de tarefas agendadas
- Violações do sistema de restrição de brindes
- Notificações enviadas via Telegram

### Problemas Comuns

#### Perfil do Instagram não é verificado
- Verifique se as chaves de API para os serviços de Instagram estão válidas
- Verifique se o username foi extraído corretamente da personalização
- Verifique se o perfil não está privado

#### Pedidos não são processados
- Verifique se o agendador está em execução
- Verifique se os produtos têm configurações corretas no banco de dados
- Verifique se as APIs de SMM estão respondendo corretamente
- Verifique se o perfil está público

#### Webhook não é recebido
- Verifique se o webhook está configurado corretamente na Yampi
- Verifique se a assinatura do webhook está correta
- Verifique se o endpoint está acessível

#### Brindes sendo rejeitados
- Verifique se o usuário já utilizou o brinde anteriormente
- Verifique se o IP já foi usado para brinde
- Verifique se há duplicação no pedido
- Consulte os logs para detalhes específicos

### Backup do Banco de Dados
Recomenda-se fazer backup regular do banco de dados, especialmente antes de atualizações significativas.

### Monitoramento
- Configure alertas para erros críticos via Telegram
- Monitore logs de processamento de webhooks
- Acompanhe métricas de pedidos processados vs. rejeitados

## Considerações de Segurança

- Nunca compartilhe suas chaves de API ou credenciais de banco de dados
- Mantenha o arquivo `.env` fora do controle de versão
- A validação de assinatura HMAC para webhooks deve ser sempre mantida
- Implemente medidas de rate limiting para evitar sobrecarga de API
- O sistema de restrição por IP ajuda a prevenir abusos
- Logs detalhados facilitam auditoria e investigação de problemas

## Contribuindo

1. Faça um fork do repositório
2. Crie um branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Commit suas alterações (`git commit -m 'Adiciona nova feature'`)
4. Push para o branch (`git push origin feature/nome-da-feature`)
5. Abra um Pull Request

## Licença

Este projeto é licenciado sob [sua licença] - veja o arquivo LICENSE para detalhes.

## Frontend React (Painel de Controle)

O projeto inclui um painel web para gerenciar pagamentos e produtos via interface gráfica.

- Localização: `frontend/`
- Stack: React + Material-UI + Axios
- Comandos principais:
  ```bash
  cd frontend
  npm install
  npm run dev # ou npm start
  ```
- O painel consome os endpoints REST já existentes da API Flask.

---
