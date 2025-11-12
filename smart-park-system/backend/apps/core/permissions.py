from rest_framework import permissions
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from apps.tenants.models import ClientMembers


class BasePermission(permissions.BasePermission):
    """
    Classe base para permissões customizadas
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True


class IsAdminUser(BasePermission):
    """
    Permite acesso apenas para usuários admin
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="admin").exists()
        )


class IsClientAdmin(BasePermission):
    """
    Permite acesso para client admins (acesso total a todos os estabelecimentos)
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin do cliente (sem estabelecimento específico = acesso total)
        return ClientMembers.objects.filter(
            user=request.user, role__name="client_admin", establishment__isnull=True
        ).exists()


class IsAppUser(BasePermission):
    """
    Permite acesso para usuários do app
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="app_user").exists()
        )


class IsClientAdminOrAdmin(BasePermission):
    """
    Permite acesso para client admins ou admins
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin do sistema
        if request.user.groups.filter(name="admin").exists():
            return True

        # Admin do cliente (acesso total)
        return ClientMembers.objects.filter(
            user=request.user, role__name="client_admin", establishment__isnull=True
        ).exists()


class IsClientEstablishmentAdmin(BasePermission):
    """
    Permite acesso para admins de estabelecimento específico
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin do sistema
        if request.user.groups.filter(name="admin").exists():
            return True

        # Admin do cliente (acesso total)
        if ClientMembers.objects.filter(
            user=request.user, role__name="client_admin", establishment__isnull=True
        ).exists():
            return True

        # Admin de estabelecimento específico
        return ClientMembers.objects.filter(
            user=request.user,
            role__name="client_establishment_admin",
            establishment__isnull=False,
        ).exists()


class IsClientEstablishmentAdminOrAdmin(BasePermission):
    """
    Permite acesso para admins de estabelecimento ou admins do cliente ou admins do sistema
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin do sistema
        if request.user.groups.filter(name="admin").exists():
            return True

        # Admin do cliente (acesso total)
        if ClientMembers.objects.filter(
            user=request.user, role__name="client_admin", establishment__isnull=True
        ).exists():
            return True

        # Admin de estabelecimento específico
        return ClientMembers.objects.filter(
            user=request.user,
            role__name="client_establishment_admin",
            establishment__isnull=False,
        ).exists()


class IsOwnerOrAdmin(BasePermission):
    """
    Permite acesso para o dono do objeto ou admin
    """

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin tem acesso a tudo
        if request.user.groups.filter(name="admin").exists():
            return True

        # Verifica se é o dono do objeto
        if hasattr(obj, "user") and obj.user == request.user:
            return True

        if hasattr(obj, "created_by") and obj.created_by == request.user:
            return True

        return False


class IsClientMember(BasePermission):
    """
    Permite acesso para membros de clientes (qualquer role)
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin tem acesso a tudo
        if request.user.groups.filter(name="admin").exists():
            return True

        # Verifica se é membro de algum cliente (qualquer role)
        return request.user.client_members.exists()


class IsClientAdminForClient(BasePermission):
    """
    Permite acesso para client admins do cliente específico (acesso total)
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin tem acesso a tudo
        if request.user.groups.filter(name="admin").exists():
            return True

        # Admin do cliente (acesso total - sem estabelecimento específico)
        return ClientMembers.objects.filter(
            user=request.user, role__name="client_admin", establishment__isnull=True
        ).exists()


class IsOwnerOrClientAdmin(BasePermission):
    """
    Permite acesso para o dono ou client admin do cliente
    """

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin tem acesso a tudo
        if request.user.groups.filter(name="admin").exists():
            return True

        # Verifica se é o dono do objeto
        if hasattr(obj, "user") and obj.user == request.user:
            return True

        # Verifica se é client admin do cliente do objeto
        if hasattr(obj, "client"):
            return request.user.client_members.filter(
                client=obj.client, role__name="client_admin"
            ).exists()

        return False


class ReadOnlyOrAdmin(BasePermission):
    """
    Permite leitura para usuários autenticados, escrita apenas para admins
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.groups.filter(name="admin").exists()


class IsActiveUser(BasePermission):
    """
    Permite acesso apenas para usuários ativos
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active
