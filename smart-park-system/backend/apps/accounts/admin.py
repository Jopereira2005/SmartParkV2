from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

# Importar o admin_site customizado
from smartpark.admin import admin_site


# Customizar o UserAdmin existente
class CustomUserAdmin(BaseUserAdmin):
    """
    Admin customizado para User com informações extras
    """

    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "user_groups",
        "client_info",
        "is_active",
        "last_login",
        "date_joined",
    ]
    list_filter = [
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
        "date_joined",
        "last_login",
    ]
    search_fields = ["username", "first_name", "last_name", "email"]
    readonly_fields = ["date_joined", "last_login", "client_memberships_info"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Informações Adicionais",
            {"fields": ("client_memberships_info",), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Otimizar queryset com prefetch"""
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "groups", "client_members__client", "client_members__role"
            )
        )

    def user_groups(self, obj):
        """Mostrar grupos do usuário"""
        groups = obj.groups.all()
        if groups:
            group_links = []
            for group in groups:
                url = reverse("admin:auth_group_change", args=[group.id])
                group_links.append(f'<a href="{url}">{group.name}</a>')
            return format_html(" | ".join(group_links))
        return "-"

    user_groups.short_description = "Grupos"

    def client_info(self, obj):
        """Mostrar informações de clientes"""
        memberships = obj.client_members.select_related("client", "role")
        if memberships:
            client_info = []
            for membership in memberships:
                client_url = reverse(
                    "admin:tenants_clients_change", args=[membership.client.id]
                )
                client_info.append(
                    f'<a href="{client_url}">{membership.client.name}</a> '
                    f"({membership.role.name})"
                )
            return format_html("<br>".join(client_info))
        return "-"

    client_info.short_description = "Clientes"

    def client_memberships_info(self, obj):
        """Informações detalhadas sobre memberships"""
        memberships = obj.client_members.select_related("client", "role")
        if memberships:
            info_list = []
            for membership in memberships:
                info_list.append(
                    f"Cliente: {membership.client.name}<br>"
                    f"Role: {membership.role.name}<br>"
                    f"Desde: {membership.joined_at}<br><br>"
                )
            return format_html("".join(info_list))
        return "Nenhuma associação com clientes"

    client_memberships_info.short_description = "Memberships Detalhadas"


class GroupAdmin(admin.ModelAdmin):
    """
    Admin customizado para Groups com estatísticas
    """

    list_display = ["name", "users_count", "client_members_count"]
    search_fields = ["name"]

    def get_queryset(self, request):
        """Otimizar queryset com annotate"""
        return (
            super()
            .get_queryset(request)
            .annotate(
                users_count=Count("user", distinct=True),
                client_members_count=Count("client_members", distinct=True),
            )
        )

    def users_count(self, obj):
        """Contar usuários no grupo"""
        count = obj.users_count
        if count > 0:
            url = reverse("admin:auth_user_changelist") + f"?groups__id__exact={obj.id}"
            return format_html('<a href="{}">{} usuários</a>', url, count)
        return "0 usuários"

    users_count.short_description = "Usuários"

    def client_members_count(self, obj):
        """Contar membros de clientes neste grupo"""
        count = obj.client_members_count
        if count > 0:
            return f"{count} memberships"
        return "0 memberships"

    client_members_count.short_description = "Client Members"


# Inline para mostrar grupos do usuário
class UserGroupsInline(admin.TabularInline):
    """
    Inline para grupos do usuário
    """

    model = User.groups.through
    extra = 0
    verbose_name = "Grupo"
    verbose_name_plural = "Grupos"


# Action personalizada para ativar/desativar usuários
@admin.action(description="Ativar usuários selecionados")
def activate_users(modeladmin, request, queryset):
    """Ativar usuários em lote"""
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} usuários foram ativados.")


@admin.action(description="Desativar usuários selecionados")
def deactivate_users(modeladmin, request, queryset):
    """Desativar usuários em lote"""
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} usuários foram desativados.")


@admin.action(description="Adicionar ao grupo app_user")
def add_to_app_user_group(modeladmin, request, queryset):
    """Adicionar usuários ao grupo app_user"""
    app_user_group, created = Group.objects.get_or_create(name="app_user")
    count = 0
    for user in queryset:
        if not user.groups.filter(name="app_user").exists():
            user.groups.add(app_user_group)
            count += 1
    modeladmin.message_user(
        request, f"{count} usuários foram adicionados ao grupo app_user."
    )


# Registrar os admins customizados no admin_site customizado
admin_site.register(User, CustomUserAdmin)
admin_site.register(Group, GroupAdmin)

# Adicionar actions customizadas
CustomUserAdmin.actions = [activate_users, deactivate_users, add_to_app_user_group]
