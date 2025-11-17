#!/bin/bash

# ===================================================
# SmartPark Django Application Entrypoint Script
# ===================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[SmartPark Entrypoint]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SmartPark Entrypoint]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[SmartPark Entrypoint]${NC} $1"
}

log_error() {
    echo -e "${RED}[SmartPark Entrypoint]${NC} $1"
}

# ===================
# Environment Setup
# ===================
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Change to app directory
cd /app

# ===================
# Database Functions
# ===================
wait_for_db() {
    log "Aguardando conexão com o banco de dados..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python manage.py check --database default >/dev/null 2>&1; then
            log_success "Banco de dados conectado!"
            return 0
        fi
        
        log "Tentativa $attempt/$max_attempts - Aguardando banco de dados..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Falha ao conectar com o banco de dados após $max_attempts tentativas"
    exit 1
}

wait_for_redis() {
    log "Aguardando conexão com Redis..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "import redis; r=redis.from_url('${REDIS_URL:-redis://redis:6379/0}'); r.ping()" >/dev/null 2>&1; then
            log_success "Redis conectado!"
            return 0
        fi
        
        log "Tentativa $attempt/$max_attempts - Aguardando Redis..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_warning "Redis não disponível, continuando sem cache"
}

# ===================
# Django Functions
# ===================
run_migrations() {
    log "Executando migrações do banco de dados..."
    python manage.py migrate --noinput
    log_success "Migrações executadas com sucesso!"
}

collect_static() {
    log "Coletando arquivos estáticos..."
    python manage.py collectstatic --noinput --clear
    log_success "Arquivos estáticos coletados!"
}

create_superuser() {
    if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log "Criando superusuário..."
        python manage.py createsuperuser \
            --noinput \
            --username "$DJANGO_SUPERUSER_USERNAME" \
            --email "$DJANGO_SUPERUSER_EMAIL" || log_warning "Superusuário já existe ou falha na criação"
    else
        # Create default superuser for development
        log "Criando superusuário padrão para desenvolvimento..."
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@smartpark.local',
        password='admin123'
    )
    print('Superusuário criado: admin/admin123')
else:
    print('Usuário admin já existe')
EOF
    fi
}

load_fixtures() {
    if [ "$LOAD_INITIAL_DATA" = "true" ]; then
        log "Carregando dados iniciais..."
        
        # Check if there are any fixture files
        if ls fixtures/*.json >/dev/null 2>&1; then
            for fixture in fixtures/*.json; do
                log "Carregando fixture: $fixture"
                python manage.py loaddata "$fixture" || log_warning "Falha ao carregar $fixture"
            done
        else
            log_warning "Nenhuma fixture encontrada em fixtures/"
        fi
    fi
}

# ===================
# Health Check
# ===================
health_check() {
    log "Executando verificação de saúde..."
    
    # Check Django
    python manage.py check --deploy 2>/dev/null || log_warning "Verificação de deploy Django falhou"
    
    # Check database
    python manage.py check --database default || {
        log_error "Verificação do banco de dados falhou"
        return 1
    }
    
    log_success "Verificação de saúde concluída!"
}

# ===================
# Development Setup
# ===================
setup_development() {
    log "Configurando ambiente de desenvolvimento..."
    
    # Install development dependencies if requirements file exists
    if [ -f "requirements/dev.txt" ]; then
        log "Instalando dependências de desenvolvimento..."
        pip install -r requirements/dev.txt
    fi
    
    # Setup pre-commit hooks in development
    if command -v pre-commit >/dev/null 2>&1; then
        log "Configurando pre-commit hooks..."
        pre-commit install || log_warning "Falha ao instalar pre-commit hooks"
    fi
}

# ===================
# Production Setup
# ===================
setup_production() {
    log "Configurando ambiente de produção..."
    
    # Ensure static files are collected
    collect_static
    
    # Run additional production checks
    python manage.py check --deploy || log_warning "Verificações de produção falharam"
}

# ===================
# Main Execution
# ===================
main() {
    log "Iniciando SmartPark Application"
    log "Ambiente: ${DJANGO_SETTINGS_MODULE:-smartpark.settings.dev}"
    
    # Wait for services
    wait_for_db
    wait_for_redis
    
    # Run migrations
    run_migrations
    
    # Environment-specific setup
    if [ "$DJANGO_DEBUG" = "True" ] || [ "$DJANGO_DEBUG" = "true" ]; then
        setup_development
        log "Modo de desenvolvimento ativado"
    else
        setup_production
        log "Modo de produção ativado"
    fi
    
    # Create superuser if credentials provided
    create_superuser
    
    # Load initial data if requested
    load_fixtures
    
    # Final health check
    health_check
    
    log_success "Inicialização concluída!"
}

# ===================
# Command Handling
# ===================

# If first argument is a management command, run it
if [ "$1" = "manage.py" ] || [ "$1" = "./manage.py" ]; then
    log "Executando comando Django: $*"
    main
    exec python "$@"
fi

# If first argument is a Django management command
if [ "$1" = "runserver" ] || [ "$1" = "migrate" ] || [ "$1" = "collectstatic" ] || [ "$1" = "shell" ] || [ "$1" = "test" ]; then
    log "Executando comando Django: python manage.py $*"
    main
    exec python manage.py "$@"
fi

# If first argument is a Celery command
if [ "$1" = "celery" ]; then
    log "Executando comando Celery: $*"
    wait_for_db
    wait_for_redis
    exec "$@"
fi

# If first argument is gunicorn
if [ "$1" = "gunicorn" ]; then
    log "Iniciando servidor Gunicorn"
    main
    exec "$@"
fi

# If first argument is a custom command
case "$1" in
    "production")
        log "Iniciando em modo produção"
        main
        exec gunicorn smartpark.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers 3 \
            --worker-class gevent \
            --worker-connections 1000 \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --timeout 30 \
            --keep-alive 2 \
            --access-logfile - \
            --error-logfile - \
            --log-level info
        ;;
    "development")
        log "Iniciando em modo desenvolvimento"
        main
        exec python manage.py runserver 0.0.0.0:8000
        ;;
    "worker")
        log "Iniciando Celery Worker"
        wait_for_db
        wait_for_redis
        exec celery -A smartpark worker -l info --concurrency=2
        ;;
    "beat")
        log "Iniciando Celery Beat Scheduler"
        wait_for_db
        wait_for_redis
        exec celery -A smartpark beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;
    "flower")
        log "Iniciando Celery Flower Monitor"
        wait_for_redis
        exec celery -A smartpark flower --port=5555
        ;;
    "test")
        log "Executando testes"
        wait_for_db
        exec python manage.py test "$@"
        ;;
    "bash")
        log "Iniciando shell bash"
        exec /bin/bash
        ;;
    *)
        # Default: run the command as-is
        log "Executando comando personalizado: $*"
        main
        exec "$@"
        ;;
esac