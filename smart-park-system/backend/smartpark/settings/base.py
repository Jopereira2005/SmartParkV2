from pathlib import Path
import environ
from datetime import timedelta

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend/smartpark
ROOT_DIR = BASE_DIR.parent.parent  # .../ (raiz do repo)

# Envs (lê .env na raiz do repo)
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, "CHANGE_ME"),
    DJANGO_ALLOWED_HOSTS=(list, ["*"]),
    DATABASE_URL=(str, "postgresql://postgres:postgres@localhost:5432/smart-park-db"),
    CORS_ALLOWED_ORIGINS=(list, []),
)
environ.Env.read_env(ROOT_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "jazzmin",  # Deve vir antes do django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # apps do projeto
    "apps.core",
    "apps.accounts",
    "apps.tenants",
    "apps.catalog",
    "apps.hardware",
    "apps.events",
    "apps.public",
    "apps.client_backoffice",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS deve vir cedo
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "smartpark.urls"
WSGI_APPLICATION = "smartpark.wsgi.application"
ASGI_APPLICATION = "smartpark.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR.parent / "templates"],  # Aponta para backend/templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR.parent / "staticfiles"  # Para deploy
STATICFILES_DIRS = [
    BASE_DIR.parent / "templates/admin",  # Caminho correto: backend/templates/admin
]

# Media files (uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Cache configuration for better admin performance
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "smartpark-cache",
        "TIMEOUT": 300,  # 5 minutes
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        }
    }
}

# Session configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# DB via DATABASE_URL
DATABASES = {"default": env.db("DATABASE_URL")}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Swagger/Schema
SPECTACULAR_SETTINGS = {
    "TITLE": "SmartPark API",
    "DESCRIPTION": "Sistema de gerenciamento de estacionamentos inteligentes",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Development server"},
    ],
    "TAGS": [
        # ============ ACCOUNTS APP ============
        {
            "name": "Accounts - Authentication",
            "description": "🔐 Endpoints para autenticação de usuários (login, logout, refresh token)",
        },
        {
            "name": "Accounts - Users",
            "description": "👤 Endpoints para gerenciamento de usuários (perfil, busca, validação)",
        },
        # ============ CATALOG APP ============
        {
            "name": "Catalog - Public",
            "description": "🌐 Endpoints públicos do catálogo (estabelecimentos, vagas)",
        },
        {
            "name": "Catalog - Types",
            "description": "📓 Tipos de entidades (estabelecimentos, veículos, vagas)",
        },
        # ============ TENANTS APP ============
        {
            "name": "Tenants - Clients",
            "description": "🏢 Gerenciamento de clientes do sistema",
        },
        {
            "name": "Tenants - Client Members",
            "description": "👥 Gerenciamento de membros de clientes",
        },
        {
            "name": "Tenants - Establishments",
            "description": "🏬 Gerenciamento de estabelecimentos",
        },
        {
            "name": "Tenants - Lots",
            "description": "🏞️ Gerenciamento de estacionamentos/lotes",
        },
        {
            "name": "Tenants - Slots",
            "description": "🚙 Gerenciamento de vagas de estacionamento",
        },
        {"name": "Tenants - Slot Status", "description": "📊 Status atual das vagas"},
        {
            "name": "Tenants - Slot Status History",
            "description": "📈 Histórico de mudanças de status das vagas",
        },
        # ============ HARDWARE APP ============
        {
            "name": "Hardware - Cameras",
            "description": "📹 Gerenciamento de câmeras de monitoramento",
        },
        {
            "name": "Hardware - Camera Monitoring",
            "description": "📡 Monitoramento e heartbeats das câmeras",
        },
        {
            "name": "Hardware - API Keys",
            "description": "🔑 Gerenciamento de chaves de API para hardware",
        },
        {
            "name": "Hardware - Integration",
            "description": "🔗 Endpoints para integração com hardware",
        },
        # ============ EVENTS APP ============
        {
            "name": "Events - System Events",
            "description": "⚡ Sistema de eventos de status das vagas",
        },
        {
            "name": "Events - Analytics",
            "description": "📊 Eventos e análises do sistema",
        },
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "SORT_OPERATIONS": False,
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

# CORS Configuration
# Para desenvolvimento, permitir todos os origins
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS", default=[])
    CORS_ALLOW_CREDENTIALS = True

# Headers permitidos
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-api-key",
    "x-signature",
    "x-timestamp",
]

# Métodos permitidos
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# Permite cookies/credenciais em requests CORS
CORS_EXPOSE_HEADERS = [
    "content-type",
    "x-csrftoken",
]

# CSRF Configuration para APIs
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
])

# Configurações de CSRF do .env
CSRF_COOKIE_HTTPONLY = env.bool("CSRF_COOKIE_HTTPONLY", default=False)
CSRF_COOKIE_SAMESITE = env.str("CSRF_COOKIE_SAMESITE", default="Lax")


# ============================================================================
# JAZZMIN SETTINGS - Interface moderna para Django Admin
# ============================================================================

JAZZMIN_SETTINGS = {
    # Título da aplicação
    "site_title": "SmartPark Admin",
    "site_header": "🏗️ SmartPark - Sistema Inteligente",
    "site_brand": "SmartPark",
    "site_logo": None,  # Pode adicionar logo depois
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": "fas fa-parking",
    
    # Texto de boas-vindas na página de login
    "welcome_sign": "Bem-vindo ao SmartPark Admin Backoffice",
    
    # Texto de copyright
    "copyright": "SmartPark - Sistema Inteligente de Estacionamentos © 2025",
    
    # Busca de models no admin
    "search_model": ["auth.User", "tenants.Clients", "catalog.Establishments"],
    
    # ID do usuário para mostrar avatar (campo)
    "user_avatar": None,
    
    ############
    # Top Menu #
    ############
    
    # Links no topo do admin
    "topmenu_links": [
        # Dashboard principal
        {"name": "🏠 Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        
        # Páginas úteis
        {"name": "🌐 Site Público", "url": "/", "new_window": True},
        {"name": "📚 API Docs", "url": "/api/docs/", "new_window": True},
    ],
    
    #############
    # Side Menu #
    #############
    
    # Se deve mostrar a sidebar
    "show_sidebar": True,
    
    # Se deve mostrar navegação na sidebar
    "navigation_expanded": True,
    
    # Esconder apps/models específicos
    "hide_apps": [],
    "hide_models": [],
    
    # Ordenar apps (caso contrário é alfabético)
    "order_with_respect_to": [
        "tenants",      # Clientes primeiro
        "catalog",      # Catálogo de estabelecimentos
        "hardware",     # Hardware/câmeras
        "events",       # Eventos do sistema
        "accounts",     # Contas de usuários
        "auth",         # Autenticação Django
    ],
    
    # Ícones customizados para apps
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
        
        "tenants": "fas fa-building",
        "tenants.Clients": "fas fa-handshake",
        "tenants.ClientMembers": "fas fa-user-tie",
        
        "catalog": "fas fa-store",
        "catalog.Establishments": "fas fa-building-flag",
        "catalog.Lots": "fas fa-square-parking",
        "catalog.Slots": "fas fa-parking",
        "catalog.StoreTypes": "fas fa-tags",
        "catalog.VehicleTypes": "fas fa-car",
        "catalog.SlotTypes": "fas fa-list-alt",
        "catalog.SlotStatus": "fas fa-traffic-light",
        "catalog.SlotStatusHistory": "fas fa-history",
        
        "hardware": "fas fa-video",
        "hardware.Cameras": "fas fa-camera",
        "hardware.ApiKeys": "fas fa-key",
        "hardware.CameraHeartbeats": "fas fa-heartbeat",
        
        "events": "fas fa-bell",
        "events.SlotStatusEvents": "fas fa-car-side",
        
        "accounts": "fas fa-user-shield",
    },
    
    # Links customizados na sidebar que são sempre exibidos
    "custom_links": {
        "tenants": [{
            "name": "📊 Dashboard de Clientes",
            "url": "admin:tenants_clients_changelist",
            "icon": "fas fa-chart-pie",
            "permissions": ["tenants.view_clients"]
        }, {
            "name": "👥 Gestão de Membros", 
            "url": "admin:tenants_clientmembers_changelist",
            "icon": "fas fa-users-cog",
            "permissions": ["tenants.view_clientmembers"]
        }],
        "catalog": [{
            "name": "🗺️ Mapa de Vagas",
            "url": "admin:catalog_slots_changelist", 
            "icon": "fas fa-map-marked-alt",
            "permissions": ["catalog.view_slots"]
        }, {
            "name": "📍 Status em Tempo Real",
            "url": "admin:catalog_slotstatus_changelist",
            "icon": "fas fa-broadcast-tower", 
            "permissions": ["catalog.view_slotstatus"]
        }],
        "hardware": [{
            "name": "� Monitor de Câmeras",
            "url": "admin:hardware_cameras_changelist",
            "icon": "fas fa-video",
            "permissions": ["hardware.view_cameras"]
        }, {
            "name": "💓 Heartbeats",
            "url": "admin:hardware_cameraheartbeats_changelist",
            "icon": "fas fa-heartbeat",
        }]
    },
    
    # Links customizados na sidebar - removidos temporariamente devido a problemas de URL
    "custom_links": {},
    
    # Configurações de relatórios e analytics
    "show_ui_builder": False,
    
    # Configurações relacionadas ao modelo do SmartPark
    "related_modal_active": True,  # Permite edição em modal
    "custom_navigation": True,
    
    # CSS e JS customizados
    "custom_css": "css/jazzmin_custom.css",
    "custom_js": "js/jazzmin_custom.js",
    
    # Se deve mostrar o link para o site público
    "show_ui_builder": False,
    
    ###############
    # Change view #
    ###############
    
    "changeform_format": "horizontal_tabs",
    # "changeform_format": "collapsible",
    # "changeform_format": "carousel",
    
    "changeform_format_overrides": {
        "auth.user": "collapsible", 
        "auth.group": "vertical_tabs",
        "tenants.clients": "horizontal_tabs",
        "catalog.establishments": "horizontal_tabs",
        "hardware.cameras": "collapsible",
    },
    
    # Add a language dropdown into the admin
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,  # Navbar fixo para melhor UX
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,  # Sidebar fixo para navegação fácil
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,  # Melhor hierarquia visual
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,  # Estilo mais moderno
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary", 
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": True  # Ações fixas para listas longas
}
