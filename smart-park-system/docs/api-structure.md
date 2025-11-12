# SmartPark API - Estrutura de URLs e Documentação Hierárquica

## Padrão de URLs Proposto

### Estrutura Geral

```json
api/{app_name}/{categoria}/{endpoint}/
```

### Exemplos por App

#### 🔐 **ACCOUNTS APP**

```json
api/accounts/auth/login/                    # Login
api/accounts/auth/refresh/                  # Refresh token
api/accounts/auth/logout/                   # Logout

api/accounts/user/register/                 # Registro de usuário
api/accounts/user/profile/                  # Perfil do usuário
api/accounts/user/profile/update/           # Atualizar perfil
api/accounts/user/profile/change-password/  # Trocar senha
api/accounts/user/profile/deactivate/       # Desativar conta
api/accounts/user/search/                   # Buscar usuários
api/accounts/user/utils/check-username/     # Verificar username
api/accounts/user/utils/check-email/        # Verificar email
```

#### 🌐 **CATALOG APP**

```json
api/catalog/public/establishments/          # Lista pública de estabelecimentos
api/catalog/public/establishments/{id}/slots/ # Vagas de um estabelecimento

api/catalog/store-types/list/               # Tipos de estabelecimento
api/catalog/vehicle-types/list/             # Tipos de veículos
api/catalog/slot-types/list/                # Tipos de vagas
```

#### 🏢 **TENANTS APP**

```json
api/tenants/client/list/                    # Lista de clientes
api/tenants/client/create/                  # Criar cliente
api/tenants/client/{id}/detail/             # Detalhes do cliente
api/tenants/client/{id}/update/             # Atualizar cliente
api/tenants/client/{id}/delete/             # Deletar cliente

api/tenants/member/list/                    # Membros do cliente
api/tenants/member/create/                  # Adicionar membro
api/tenants/member/{id}/update/             # Atualizar membro
api/tenants/member/{id}/remove/             # Remover membro

api/tenants/establishment/list/             # Estabelecimentos
api/tenants/establishment/create/           # Criar estabelecimento
api/tenants/establishment/{id}/detail/      # Detalhes
api/tenants/establishment/{id}/update/      # Atualizar
api/tenants/establishment/{id}/delete/      # Deletar

api/tenants/lot/list/                       # Lotes/Estacionamentos
api/tenants/lot/create/                     # Criar lote
api/tenants/lot/{id}/detail/                # Detalhes do lote
api/tenants/lot/{id}/update/                # Atualizar lote
api/tenants/lot/{id}/delete/                # Deletar lote

api/tenants/slot/list/                      # Vagas
api/tenants/slot/create/                    # Criar vaga
api/tenants/slot/{id}/detail/               # Detalhes da vaga
api/tenants/slot/{id}/update/               # Atualizar vaga
api/tenants/slot/{id}/delete/               # Deletar vaga
api/tenants/slot/{id}/status/               # Status atual da vaga
api/tenants/slot/{id}/history/              # Histórico da vaga
```

#### 📹 **HARDWARE APP**

```json
api/hardware/camera/list/                   # Lista de câmeras
api/hardware/camera/create/                 # Registrar câmera
api/hardware/camera/{id}/detail/            # Detalhes da câmera
api/hardware/camera/{id}/update/            # Atualizar câmera
api/hardware/camera/{id}/delete/            # Deletar câmera

api/hardware/monitoring/heartbeat/          # Heartbeat das câmeras
api/hardware/monitoring/status/             # Status dos dispositivos

api/hardware/api-key/list/                  # Chaves de API
api/hardware/api-key/create/                # Gerar chave
api/hardware/api-key/{id}/revoke/           # Revogar chave

api/hardware/integration/slot-update/       # Atualização de vaga via hardware
api/hardware/integration/batch-update/      # Atualização em lote
```

#### ⚡ **EVENTS APP**

```json
api/events/system/list/                     # Eventos do sistema
api/events/system/create/                   # Criar evento
api/events/system/{id}/detail/              # Detalhes do evento

api/events/analytics/dashboard/             # Dashboard de analytics
api/events/analytics/reports/               # Relatórios
api/events/analytics/metrics/               # Métricas do sistema
```

## Estrutura Hierárquica do Swagger

### Organização das Tags

```txt
📱 Accounts
  ├── 🔐 Accounts - Authentication
  └── 👤 Accounts - Users

🌐 Catalog  
  ├── 🌍 Catalog - Public
  ├── 🏪 Catalog - Store Types
  ├── 🚗 Catalog - Vehicle Types
  └── 🅿️ Catalog - Slot Types

🏢 Tenants
  ├── 🏢 Tenants - Clients
  ├── 👥 Tenants - Client Members  
  ├── 🏬 Tenants - Establishments
  ├── 🏞️ Tenants - Lots
  ├── 🚙 Tenants - Slots
  ├── 📊 Tenants - Slot Status
  └── 📈 Tenants - Slot Status History

📹 Hardware
  ├── 📹 Hardware - Cameras
  ├── 📡 Hardware - Camera Monitoring
  ├── 🔑 Hardware - API Keys
  └── 🔗 Hardware - Integration

⚡ Events
  ├── ⚡ Events - System Events
  └── 📊 Events - Analytics
```

## Benefícios da Nova Estrutura

### 1. **Organização Intuitiva**

- URLs seguem padrão consistente
- Fácil navegação no Swagger
- Agrupamento lógico por funcionalidade

### 2. **Escalabilidade**

- Fácil adicionar novos endpoints
- Estrutura flexível para novos apps
- Manutenção simplificada

### 3. **Developer Experience**

- URLs autodocumentadas
- Swagger bem organizado
- Fácil localização de endpoints

### 4. **Separação de Responsabilidades**

- Catalog: dados públicos e tipos/categorias
- Tenants: dados específicos do cliente
- Accounts: autenticação e usuários
- Hardware: integração com dispositivos
- Events: eventos e analytics

## Implementação

### 1. **Configuração do drf-spectacular**

```python
SPECTACULAR_SETTINGS = {
    "TAGS": [
        {
            "name": "Accounts - Authentication",
            "description": "🔐 Endpoints para autenticação..."
        },
        # ... outras tags
    ]
}
```

### 2. **Views com Tags Hierárquicas**

```python
@extend_schema(
    tags=["Accounts - Authentication"],
    summary="User Login",
    description="Authenticate user and obtain JWT tokens"
)
class LoginView(APIView):
    pass
```

### 3. **URLs Organizadas**

```python
urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth_login"),
    path("user/profile/", ProfileView.as_view(), name="user_profile"),
]
```

## Status de Implementação

- ✅ **Accounts App**: Estrutura implementada
- 🔄 **Configuração Swagger**: Tags hierárquicas configuradas  
- ⏳ **Outros Apps**: Aplicar padrão nos demais apps
- ⏳ **Documentação**: Adicionar exemplos e descrições detalhadas
