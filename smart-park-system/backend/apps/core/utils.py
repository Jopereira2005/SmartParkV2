from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import hashlib
import secrets
from typing import Optional, List, Dict, Any
from apps.tenants.models import ClientMembers


def generate_public_id() -> str:
    """
    Gera um UUID4 para public_id
    """
    return str(uuid.uuid4())


def generate_api_key() -> str:
    """
    Gera uma chave de API segura
    """
    return secrets.token_urlsafe(32)


def generate_hmac_secret() -> str:
    """
    Gera um secret HMAC seguro
    """
    return secrets.token_urlsafe(64)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Gera hash de senha com salt
    """
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )

    return password_hash.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verifica se a senha está correta
    """
    expected_hash, _ = hash_password(password, salt)
    return expected_hash == password_hash


def get_user_clients(user) -> List[int]:
    """
    Retorna lista de IDs dos clientes do usuário
    """
    if not user or not user.is_authenticated:
        return []

    return list(user.client_members.values_list("client_id", flat=True))


def filter_by_user_clients(queryset, user, client_field: str = "client_id"):
    """
    Filtra queryset pelos clientes do usuário
    """
    user_clients = get_user_clients(user)
    if not user_clients:
        return queryset.none()

    return queryset.filter(**{f"{client_field}__in": user_clients})


def is_admin_user(user) -> bool:
    """
    Verifica se o usuário é admin
    """
    if not user or not user.is_authenticated:
        return False

    return user.groups.filter(name="admin").exists()


def is_client_admin(user) -> bool:
    """
    Verifica se o usuário é client admin
    """
    if not user or not user.is_authenticated:
        return False

    return user.groups.filter(name="client_admin").exists()


def is_app_user(user) -> bool:
    """
    Verifica se o usuário é app user
    """
    if not user or not user.is_authenticated:
        return False

    return user.groups.filter(name="app_user").exists()


def get_user_role(user) -> Optional[str]:
    """
    Retorna o role principal do usuário (admin > client_admin > app_user)
    """
    if not user or not user.is_authenticated:
        return None

    user_groups = user.groups.values_list("name", flat=True)

    if "admin" in user_groups:
        return "admin"
    elif "client_admin" in user_groups:
        return "client_admin"
    elif "app_user" in user_groups:
        return "app_user"

    return None


def validate_public_id(public_id: str) -> bool:
    """
    Valida se o public_id é um UUID válido
    """
    try:
        uuid.UUID(public_id)
        return True
    except (ValueError, TypeError):
        return False


def is_client_establishment_admin(user, establishment=None) -> bool:
    """
    Verifica se o usuário é admin de estabelecimento
    """
    if not user or not user.is_authenticated:
        return False

    # Admin do sistema
    if user.groups.filter(name="admin").exists():
        return True

    # Admin do cliente (acesso total)
    if ClientMembers.objects.filter(
        user=user, role__name="client_admin", establishment__isnull=True
    ).exists():
        return True

    # Admin de estabelecimento específico
    if establishment:
        return ClientMembers.objects.filter(
            user=user,
            role__name="client_establishment_admin",
            establishment=establishment,
        ).exists()

    # Admin de qualquer estabelecimento
    return ClientMembers.objects.filter(
        user=user, role__name="client_establishment_admin", establishment__isnull=False
    ).exists()


def get_user_establishments(user, client):
    """
    Retorna estabelecimentos que o usuário pode acessar
    """
    from apps.catalog.models import Establishments

    if not user or not user.is_authenticated:
        return Establishments.objects.none()

    # Admin do sistema vê tudo
    if user.groups.filter(name="admin").exists():
        return Establishments.objects.filter(client=client)

    # Admin do cliente vê todos os estabelecimentos do cliente
    if ClientMembers.objects.filter(
        user=user, client=client, role__name="client_admin", establishment__isnull=True
    ).exists():
        return Establishments.objects.filter(client=client)

    # Usuário vê apenas estabelecimentos específicos
    return Establishments.objects.filter(
        client=client,
        client_members__user=user,
        client_members__establishment__isnull=False,
    ).distinct()


def can_access_establishment(user, establishment):
    """
    Verifica se usuário pode acessar estabelecimento específico
    """
    if not user or not user.is_authenticated:
        return False

    # Admin do sistema
    if user.groups.filter(name="admin").exists():
        return True

    # Admin do cliente (acesso total)
    if ClientMembers.objects.filter(
        user=user,
        client=establishment.client,
        role__name="client_admin",
        establishment__isnull=True,
    ).exists():
        return True

    # Admin de estabelecimento específico
    return ClientMembers.objects.filter(
        user=user,
        client=establishment.client,
        establishment=establishment,
        role__name="client_establishment_admin",
    ).exists()


def get_user_role_in_establishment(user, establishment):
    """
    Retorna o role do usuário no estabelecimento
    """
    if not user or not user.is_authenticated:
        return None

    # Admin do sistema
    if user.groups.filter(name="admin").exists():
        return "admin"

    # Admin do cliente
    if ClientMembers.objects.filter(
        user=user,
        client=establishment.client,
        role__name="client_admin",
        establishment__isnull=True,
    ).exists():
        return "client_admin"

    # Admin de estabelecimento específico
    member = ClientMembers.objects.filter(
        user=user, client=establishment.client, establishment=establishment
    ).first()

    return member.role.name if member else None


def validate_email(email: str) -> bool:
    """
    Valida formato de email
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def format_datetime(dt) -> str:
    """
    Formata datetime para string ISO
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        return dt

    return dt.isoformat()


def get_timezone_aware_now():
    """
    Retorna timezone.now() para consistência
    """
    return timezone.now()


def create_audit_log(
    action: str, user, object_type: str, object_id: int, changes: Dict[str, Any] = None
) -> None:
    """
    Cria log de auditoria (implementação básica)
    """
    # Implementação básica - pode ser expandida para usar um sistema de logging
    log_data = {
        "action": action,
        "user_id": user.id if user else None,
        "object_type": object_type,
        "object_id": object_id,
        "changes": changes or {},
        "timestamp": get_timezone_aware_now(),
    }

    # Aqui você pode salvar no banco, enviar para um serviço de logging, etc.
    print(f"AUDIT LOG: {log_data}")


def sanitize_string(value: str, max_length: int = None) -> str:
    """
    Sanitiza string removendo caracteres perigosos
    """
    if not isinstance(value, str):
        return str(value)

    # Remove caracteres de controle e caracteres perigosos
    sanitized = "".join(char for char in value if ord(char) >= 32)

    if max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def generate_confirmation_code() -> str:
    """
    Gera código de confirmação (ex: para email)
    """
    return secrets.token_hex(6).upper()


def calculate_confidence_score(detections: List[Dict], threshold: float = 0.5) -> float:
    """
    Calcula score de confiança baseado em detecções
    """
    if not detections:
        return 0.0

    scores = [d.get("confidence", 0) for d in detections if "confidence" in d]
    if not scores:
        return 0.0

    avg_score = sum(scores) / len(scores)
    return min(avg_score, 1.0) if avg_score >= threshold else 0.0


def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Valida se as coordenadas são válidas
    """
    return (
        isinstance(lat, (int, float))
        and isinstance(lng, (int, float))
        and -90 <= lat <= 90
        and -180 <= lng <= 180
    )


def format_phone_number(phone: str) -> str:
    """
    Formata número de telefone para padrão brasileiro
    """
    if not phone:
        return ""

    # Remove todos os caracteres não numéricos
    digits = "".join(filter(str.isdigit, phone))

    # Formata para (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"

    return phone
