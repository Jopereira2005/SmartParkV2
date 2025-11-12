# SmartPark - Sistema Inteligente de Gerenciamento de Estacionamentos

**Uma solução abrangente de estacionamento inteligente utilizando visão computacional e IoT para monitoramento de vagas em tempo real.**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-suportado-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 Visão Geral

O SmartPark é um sistema inteligente de gerenciamento de estacionamentos projetado para resolver desafios de mobilidade urbana fornecendo informações de disponibilidade de vagas em tempo real. O sistema integra tecnologia de visão computacional com dispositivos IoT para monitorar vagas de estacionamento e entregar dados através de uma plataforma API abrangente.

### Principais Funcionalidades

- **Monitoramento em Tempo Real**: Câmeras com visão computacional detectam presença e ausência de veículos
- **Arquitetura Multi-tenant**: Suporte para múltiplos clientes (empresas) com dados isolados
- **API Pública**: Endpoints abertos para aplicativos móveis e integrações de terceiros
- **Painel Administrativo**: Interface Django Admin para gerenciamento do sistema
- **Autenticação JWT**: Acesso seguro à API com rotação de tokens de refresh
- **Atualizações por Eventos**: Mudanças de status de vagas em tempo real via integração com hardware
- **Permissões Abrangentes**: Controle de acesso baseado em funções (Admin, Admin Cliente, Usuário App)

### Problema Identificado

Áreas urbanas enfrentam desafios significativos no gerenciamento de vagas de estacionamento:

- Motoristas perdem tempo procurando vagas disponíveis
- Aumento do congestionamento de trânsito e emissões
- Empresas não têm visibilidade sobre a utilização de suas vagas
- Falta de forma padronizada para compartilhar dados de disponibilidade de vagas

### Solução

O SmartPark aborda esses desafios através de:

- Fornecimento de disponibilidade de vagas em tempo real
- Redução do tempo gasto procurando estacionamento
- Capacitação de empresas para otimizar suas operações de estacionamento
- Suporte a decisões de planejamento urbano baseadas em dados

## 🏗️ Arquitetura

O sistema segue uma arquitetura moderna inspirada em microsserviços:

### Componentes

1. **API Backend** (Django + DRF)

    - API RESTful com documentação abrangente
    - Isolamento de dados multi-tenant
    - Autenticação e autorização baseada em JWT
    - Processamento de eventos em tempo real

2. **Banco de Dados** (PostgreSQL)

    - Schema normalizado com indexação adequada
    - Suporte para dados espaciais (PostGIS pronto)
    - Trilhas de auditoria e exclusão suave

3. **Integração de Hardware**

    - Agentes de visão computacional para detecção de vagas
    - Autenticação baseada em chave API para dispositivos de hardware
    - Atualizações de status orientadas por eventos

4. **Interface Administrativa**
    - Django Admin para gerenciamento do sistema
    - Fluxos de aprovação e gerenciamento de clientes
    - Configuração e monitoramento de hardware

### Estrutura das Apps Django

O backend está organizado em aplicações Django específicas por domínio:

#### `apps.core`

- **Propósito**: Utilitários compartilhados e modelos base
- **Componentes Principais**:
  - `BaseModel`: Campos comuns (id, public_id, timestamps, exclusão suave)
  - `TenantModel`: Modelo base multi-tenant com isolamento de cliente
  - Managers customizados para exclusão suave e filtragem por tenant
  - Classes de permissão e mixins de view

#### `apps.tenants`

- **Propósito**: Gerenciamento de clientes (empresas) e membros
- **Models**: `Clients`, `ClientMembers`
- **Funcionalidades**: Fluxo de onboarding de clientes, gerenciamento de funções de membros
- **Endpoints API**: CRUD de clientes, gerenciamento de membros

#### `apps.catalog`

- **Propósito**: Gerenciamento da infraestrutura central de estacionamento
- **Models**:
  - `StoreTypes`: Categorias de tipos de negócio
  - `Establishments`: Localizações físicas de empresas
  - `Lots`: Áreas de estacionamento dentro de estabelecimentos
  - `Slots`: Vagas de estacionamento individuais
  - `SlotStatus`: Status atual das vagas
  - `SlotStatusHistory`: Trilha de auditoria de mudanças de status
- **Funcionalidades**: Hierarquia multi-nível (Cliente → Estabelecimento → Lote → Vaga)

#### `apps.hardware`

- **Propósito**: Gerenciamento de dispositivos IoT e câmeras
- **Models**: `ApiKeys`, `Cameras`, `CameraHeartbeats`
- **Funcionalidades**: Gerenciamento de chaves API, monitoramento de câmeras, integração com hardware

#### `apps.events`

- **Propósito**: Processamento de eventos e rastreamento de mudanças de status
- **Models**: `SlotStatusEvents`
- **Funcionalidades**: Ingestão de eventos em tempo real de dispositivos de hardware

## 🚀 Primeiros Passos

### Pré-requisitos

- Python 3.13+
- PostgreSQL 12+
- pip e pip-tools
- Git

### Instalação

1. **Clone o repositório**

    ```bash
    git clone https://github.com/jvaguiar05/smart-park-system.git
    cd smart-park-system
    ```

2. **Configure o ambiente virtual Python**

    ```bash
    python -m venv .venv
    # No Windows
    .venv\Scripts\activate
    # No macOS/Linux
    source .venv/bin/activate
    ```

3. **Instale as dependências**

    ```bash
    cd backend
    pip install -r requirements/dev.txt
    ```

4. **Configure as variáveis de ambiente**
   Crie um arquivo `.env` na raiz do projeto:

    ```env
    DJANGO_DEBUG=True
    DJANGO_SECRET_KEY=sua-chave-secreta-aqui
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
    DATABASE_URL=postgresql://postgres:password@localhost:5432/smartpark_db
    CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    ```

5. **Configure o banco de dados**

    ```bash
    # Crie o banco PostgreSQL
    createdb smartpark_db

    # Execute as migrações
    python manage.py migrate

    # Crie um superusuário
    python manage.py createsuperuser
    ```

6. **Inicie o servidor de desenvolvimento**

    ```bash
    python manage.py runserver
    ```

A API estará disponível em `http://localhost:8000` e a interface administrativa em `http://localhost:8000/admin/`.

### Documentação da API

A documentação interativa da API está disponível em:

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **Schema OpenAPI**: `http://localhost:8000/api/schema/`

## 🏢 Arquitetura Multi-Tenant

O SmartPark implementa uma arquitetura multi-tenant onde:

- **Clientes**: Representam empresas/organizações que possuem instalações de estacionamento
- **Isolamento**: Os dados de cada cliente são completamente isolados
- **Permissões**: Acesso baseado em funções garante que usuários vejam apenas dados autorizados
- **Escalabilidade**: Suporte para múltiplos clientes sem vazamento de dados

### Funções de Usuário

1. **Admin (`admin`)**

    - Acesso a todo o sistema
    - Aprovação e gerenciamento de clientes
    - Provisionamento de hardware
    - Relatórios globais

2. **Admin Cliente (`client_admin`)**

    - Gerenciar dados do próprio cliente
    - Gerenciamento de estabelecimentos e lotes
    - Configuração de hardware para instalações próprias
    - Gerenciamento de membros

3. **Usuário App (`app_user`)**
    - Acesso somente leitura a endpoints públicos
    - Consultar disponibilidade de vagas
    - Gerenciamento básico de perfil

## 📡 Visão Geral da API

### Autenticação

A API usa JWT (JSON Web Tokens) para autenticação:

```bash
# Login para obter token de acesso
POST /api/auth/token/
{
  "username": "seu_usuario",
  "password": "sua_senha"
}

# Renovar token de acesso
POST /api/auth/token/refresh/
{
  "refresh": "seu_refresh_token"
}
```

### Principais Endpoints

#### Endpoints Públicos

```bash
# Listar estabelecimentos públicos
GET /api/catalog/public/establishments/

# Obter status de estacionamento de um estabelecimento
GET /api/catalog/public/establishments/{id}/slots/
```

#### Gerenciamento de Clientes (Apenas Admin)

```bash
# Listar/Criar clientes
GET|POST /api/tenants/clients/

# Detalhes do cliente
GET|PUT|PATCH|DELETE /api/tenants/clients/{id}/
```

#### Gerenciamento de Estabelecimentos

```bash
# Listar/Criar estabelecimentos
GET|POST /api/catalog/establishments/

# Detalhes do estabelecimento
GET|PUT|PATCH|DELETE /api/catalog/establishments/{id}/
```

#### Gerenciamento de Estacionamentos

```bash
# Listar/Criar lotes
GET|POST /api/catalog/lots/

# Listar/Criar vagas em um lote
GET|POST /api/catalog/lots/{lot_id}/slots/

# Detalhes e status da vaga
GET|PUT|PATCH|DELETE /api/catalog/slots/{id}/
```

#### Integração de Hardware

```bash
# Listar/Criar chaves API
GET|POST /api/hardware/api-keys/

# Listar/Criar câmeras
GET|POST /api/hardware/cameras/

# Enviar eventos de status de vaga (Apenas Hardware)
POST /api/hardware/events/slot-status/
```

Dispositivos de hardware (câmeras) se autenticam usando chaves API e enviam eventos de status:

```bash
# Endpoint de hardware para atualizações de status
POST /api/hardware/events/slot-status/
Headers:
  X-API-Key: sua-chave-api-hardware
  Content-Type: application/json

Body:
{
  "hardwareCode": "CAM-ENTRADA-01",
  "lotId": "uuid-do-lote",
  "items": [
    {
      "slotCode": "A1",
      "status": "OCCUPIED",
      "vehicle": "car",
      "occurredAt": "2025-09-14T15:30:00Z"
    }
  ]
}
```

## 🧪 Testes

O projeto inclui suítes de teste abrangentes para cada app:

```bash
# Executar todos os testes
python manage.py test

# Executar testes para app específica
python manage.py test apps.catalog

# Executar com cobertura
coverage run manage.py test
coverage report
```

Os arquivos de teste estão organizados no diretório `tests/` de cada app:

- `test_models.py`: Validação de modelos e lógica de negócio
- `test_views.py`: Teste de endpoints da API
- `test_serializers.py`: Teste de serialização de dados
- `test_urls.py`: Teste de roteamento de URLs

## 🛠️ Desenvolvimento

### Estrutura do Código

```txt
backend/
├── manage.py                 # Script de gerenciamento Django
├── smartpark/               # Configurações principais do projeto
│   ├── settings/           # Configurações específicas por ambiente
│   ├── urls.py            # Configuração de URLs raiz
│   └── wsgi.py            # Aplicação WSGI
└── apps/                   # Aplicações específicas por domínio
    ├── core/              # Utilitários compartilhados e modelos base
    ├── tenants/           # Gerenciamento de clientes e membros
    ├── catalog/           # Infraestrutura de estacionamento
    ├── hardware/          # Gerenciamento de dispositivos IoT
    └── events/            # Processamento de eventos
```

### Principais Tecnologias

- **Django 5.2**: Framework web
- **Django REST Framework**: Desenvolvimento de API
- **PostgreSQL**: Banco de dados principal
- **JWT**: Tokens de autenticação
- **drf-spectacular**: Documentação da API
- **django-environ**: Configuração de ambiente
- **django-cors-headers**: Manipulação de CORS

### Configuração de Ambiente

O projeto usa configurações específicas por ambiente:

- `settings/base.py`: Configurações comuns
- `settings/dev.py`: Ambiente de desenvolvimento
- `settings/prod.py`: Ambiente de produção

### Schema do Banco de Dados

O banco de dados segue um design normalizado com relacionamentos adequados:

- **Isolamento multi-tenant**: Todos os modelos específicos por tenant incluem `client_id`
- **Exclusão suave**: A maioria dos modelos suporta exclusão suave via `deleted_at`
- **Trilhas de auditoria**: Timestamps e rastreamento de mudanças
- **Suporte espacial**: Pronto para dados geométricos PostGIS

## 📋 Status do Projeto

### Implementação Atual

✅ **Funcionalidades Concluídas:**

- Arquitetura Django multi-tenant
- Autenticação JWT com refresh tokens
- Endpoints de API abrangentes
- Interface Django Admin
- Permissões baseadas em funções
- Gerenciamento de chaves API de hardware
- Sistema de processamento de eventos
- Documentação da API com Swagger

### Roadmap

🚧 **Em Progresso:**

- Aplicações frontend (web e mobile)
- Integração de visão computacional
- Notificações em tempo real
- Análises avançadas

📋 **Funcionalidades Planejadas:**

- Histórico e análises de ocupação de vagas
- Monitoramento de heartbeat de câmeras
- Funcionalidades espaciais avançadas com PostGIS
- Otimizações de performance
- Monitoramento e logging abrangentes

## 📚 Documentação

Documentação adicional está disponível na pasta `docs/`:

- **[Especificação MVP](docs/smart-park-mvp.md)**: Requisitos detalhados do projeto
- **[Schema do Banco de Dados](docs/db/smart-park-db.md)**: Design completo do banco de dados
- **[Roadmap de Desenvolvimento](docs/ROADMAP_GUIDE.md)**: Progresso do desenvolvimento e próximos passos
- **[Guia de Testes](docs/test_guide.md)**: Diretrizes de teste e melhores práticas

## 🔧 Contribuindo

### Fluxo de Desenvolvimento

1. **Faça fork e clone o repositório**
2. **Crie uma branch de funcionalidade**: `git checkout -b feature/nome-da-sua-funcionalidade`
3. **Faça suas alterações** seguindo os padrões de código
4. **Execute os testes**: `python manage.py test`
5. **Commit suas alterações**: `git commit -m "Adiciona sua funcionalidade"`
6. **Push para seu fork**: `git push origin feature/nome-da-sua-funcionalidade`
7. **Crie um pull request**

### Padrões de Código

- Siga PEP 8 para estilo de código Python
- Use nomes de variáveis e funções significativos
- Escreva docstrings para todos os métodos públicos
- Inclua testes para novas funcionalidades
- Mantenha commits focados e bem documentados

### Migrações do Banco de Dados

Ao fazer alterações nos modelos:

```bash
# Criar arquivos de migração
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Verificar status das migrações
python manage.py showmigrations
```

## 🚀 Deploy

### Configuração de Ambiente (prod)

1. **Variáveis de Ambiente de Produção**

    ```env
    DJANGO_DEBUG=False
    DJANGO_SECRET_KEY=sua-chave-secreta-de-producao
    DJANGO_ALLOWED_HOSTS=seudominio.com,api.seudominio.com
    DATABASE_URL=postgresql://usuario:senha@host:porta/banco
    CORS_ALLOWED_ORIGINS=https://seufrontend.com
    ```

2. **Arquivos Estáticos**

    ```bash
    python manage.py collectstatic
    ```

3. **Configuração do Banco de Dados**

    ```bash
    python manage.py migrate
    python manage.py createsuperuser
    ```

### Suporte Docker

Um Dockerfile e docker-compose.yml podem ser adicionados para deploy containerizado:

```yaml
# exemplo docker-compose.yml
version: "3.8"
services:
    db:
        image: postgres:13
        environment:
            POSTGRES_DB: smartpark_db
            POSTGRES_USER: postgres
            POSTGRES_PASSWORD: password

    web:
        build: .
        ports:
            - "8000:8000"
        depends_on:
            - db
        environment:
            DATABASE_URL: postgresql://postgres:password@db:5432/smartpark_db
```

## 📖 Contexto Acadêmico

Este projeto foi desenvolvido como parte da disciplina **UPX (Usina de Projetos Experimentais)** na **Facens**, com foco em **Smart Cities** e **soluções de mobilidade urbana** alinhadas ao **Objetivo de Desenvolvimento Sustentável 11** da ONU (Cidades e Comunidades Sustentáveis).

### Objetivos do Projeto

- **Acadêmico**: Demonstrar aplicação prática de princípios de engenharia de software
- **Técnico**: Construir um sistema de gerenciamento de estacionamento escalável habilitado para IoT
- **Social**: Contribuir para soluções de mobilidade urbana e redução do congestionamento de trânsito
- **Ambiental**: Apoiar a redução de emissões através da otimização da busca por estacionamento

### Resultados de Aprendizagem

- Design de arquitetura SaaS multi-tenant
- Desenvolvimento de API RESTful com Django REST Framework
- Integração de dispositivos IoT e arquiteturas orientadas por eventos
- Processamento de dados em tempo real e gerenciamento de status
- Autenticação e autorização em sistemas distribuídos
- Design e otimização de banco de dados
- Estratégias de teste para aplicações web

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Facens** - Por fornecer o framework acadêmico e orientação
- **Comunidade Django** - Pelo excelente framework web e ecossistema
- **Contribuidores Open Source** - Pelas bibliotecas e ferramentas que tornam este projeto possível

---

**SmartPark** - Tornando o estacionamento urbano inteligente, uma vaga por vez. 🚗🅿️
