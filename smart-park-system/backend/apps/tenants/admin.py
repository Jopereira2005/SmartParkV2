from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Clients, ClientMembers

# Importar o admin_site customizado
from smartpark.admin import admin_site


class ClientMembersInline(admin.TabularInline):
    model = ClientMembers
    extra = 0
    fields = ["user", "role", "joined_at"]
    readonly_fields = ["joined_at"]


class ClientsAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "onboarding_status",
        "members_count",
        "establishments_count",
        "created_at",
    ]
    list_filter = ["onboarding_status", "created_at"]
    search_fields = ["name"]
    inlines = [ClientMembersInline]

    fieldsets = (
        ("Informações Básicas", {"fields": ("name", "onboarding_status")}),
        (
            "Dados de Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            members_count=Count("client_members"),
            establishments_count=Count("establishments_set"),
        )

    def members_count(self, obj):
        count = (
            obj.members_count
            if hasattr(obj, "members_count")
            else obj.client_members.count()
        )
        url = (
            reverse("admin:tenants_clientmembers_changelist")
            + f"?client__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{} membros</a>', url, count)

    members_count.short_description = "Membros"

    def establishments_count(self, obj):
        count = (
            obj.establishments_count
            if hasattr(obj, "establishments_count")
            else obj.establishments_set.count()
        )
        if count > 0:
            url = (
                reverse("admin:catalog_establishments_changelist")
                + f"?client__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{} estabelecimentos</a>', url, count)
        return "0 estabelecimentos"

    establishments_count.short_description = "Estabelecimentos"

    actions = ["activate_clients", "deactivate_clients"]

    def activate_clients(self, request, queryset):
        updated = queryset.update(onboarding_status="ACTIVE")
        self.message_user(request, f"{updated} clientes ativados.")

    activate_clients.short_description = "Ativar clientes selecionados"

    def deactivate_clients(self, request, queryset):
        updated = queryset.update(onboarding_status="INACTIVE")
        self.message_user(request, f"{updated} clientes desativados.")

    deactivate_clients.short_description = "Desativar clientes selecionados"


class ClientMembersAdmin(admin.ModelAdmin):
    list_display = ["client", "user_info", "role", "joined_at"]
    list_filter = ["role", "joined_at", "client"]
    search_fields = ["client__name", "user__username", "user__email"]

    def user_info(self, obj):
        return f"{obj.user.username} ({obj.user.email})"

    user_info.short_description = "Usuário"


# Registrar no admin_site customizado
admin_site.register(Clients, ClientsAdmin)
admin_site.register(ClientMembers, ClientMembersAdmin)
