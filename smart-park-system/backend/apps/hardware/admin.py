from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import ApiKeys, Cameras, CameraHeartbeats

# Importar o admin_site customizado
from smartpark.admin import admin_site


class CameraHeartbeatsInline(admin.TabularInline):
    model = CameraHeartbeats
    extra = 0
    fields = ["received_at", "payload_summary"]
    readonly_fields = ["received_at", "payload_summary"]
    ordering = ["-received_at"]

    def payload_summary(self, obj):
        if obj.payload_json:
            return (
                str(obj.payload_json)[:50] + "..."
                if len(str(obj.payload_json)) > 50
                else str(obj.payload_json)
            )
        return "-"

    payload_summary.short_description = "Payload"

    def get_queryset(self, request):
        return super().get_queryset(request)[:5]  # Mostrar apenas os 5 mais recentes


class ApiKeysAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "key_id_masked",
        "client",
        "enabled_status",
        "cameras_count",
        "created_at",
    ]
    list_filter = ["enabled", "created_at", "client"]
    search_fields = ["name", "key_id", "client__name"]

    fieldsets = (
        ("Informações Básicas", {"fields": ("name", "client", "enabled")}),
        (
            "Chave de API",
            {
                "fields": ("key_id", "hmac_secret_hash"),
                "description": "Mantenha essas informações seguras!",
            },
        ),
        (
            "Dados de Auditoria",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(cameras_count=Count("cameras"))

    def key_id_masked(self, obj):
        if obj.key_id:
            return f"{obj.key_id[:8]}***{obj.key_id[-4:]}"
        return "-"

    key_id_masked.short_description = "Key ID"

    def enabled_status(self, obj):
        if obj.enabled:
            return format_html('<span style="color: green;">✓ Ativa</span>')
        return format_html('<span style="color: red;">✗ Inativa</span>')

    enabled_status.short_description = "Status"

    def cameras_count(self, obj):
        count = (
            obj.cameras_count if hasattr(obj, "cameras_count") else obj.cameras.count()
        )
        if count > 0:
            url = (
                reverse("admin:hardware_cameras_changelist")
                + f"?api_key__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{} câmeras</a>', url, count)
        return "0 câmeras"

    cameras_count.short_description = "Câmeras"

    actions = ["enable_keys", "disable_keys"]

    def enable_keys(self, request, queryset):
        updated = queryset.update(enabled=True)
        self.message_user(request, f"{updated} chaves ativadas.")

    enable_keys.short_description = "Ativar chaves selecionadas"

    def disable_keys(self, request, queryset):
        updated = queryset.update(enabled=False)
        self.message_user(request, f"{updated} chaves desativadas.")

    disable_keys.short_description = "Desativar chaves selecionadas"


class CamerasAdmin(admin.ModelAdmin):
    list_display = [
        "camera_code",
        "client",
        "location_info",
        "state_display",
        "last_heartbeat",
        "heartbeats_count",
        "created_at",
    ]
    list_filter = ["state", "created_at", "last_seen_at", "client"]
    search_fields = [
        "camera_code",
        "client__name",
        "establishment__name",
        "lot__lot_code",
    ]
    inlines = [CameraHeartbeatsInline]

    fieldsets = (
        ("Informações Básicas", {"fields": ("camera_code", "client", "api_key")}),
        ("Localização", {"fields": ("establishment", "lot")}),
        ("Status e Configuração", {"fields": ("state",)}),
        (
            "Dados de Auditoria",
            {
                "fields": ("created_at", "updated_at", "last_seen_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ["created_at", "updated_at", "last_seen_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("client", "establishment", "lot")
            .annotate(heartbeats_count=Count("heartbeats"))
        )

    def location_info(self, obj):
        parts = []
        if obj.establishment:
            parts.append(obj.establishment.name)
        if obj.lot:
            parts.append(f"Lote: {obj.lot.lot_code}")
        return " | ".join(parts) if parts else "Não definido"

    location_info.short_description = "Localização"

    def state_display(self, obj):
        colors = {
            "ACTIVE": "green",
            "INACTIVE": "red",
            "MAINTENANCE": "orange",
            "ERROR": "red",
        }
        color = colors.get(obj.state, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_state_display(),
        )

    state_display.short_description = "Estado"

    def last_heartbeat(self, obj):
        if obj.last_seen_at:
            delta = timezone.now() - obj.last_seen_at
            if delta.total_seconds() < 300:  # 5 minutos
                color = "green"
                text = "Online"
            elif delta.total_seconds() < 3600:  # 1 hora
                color = "orange"
                text = f"{int(delta.total_seconds() // 60)} min atrás"
            else:
                color = "red"
                text = f"{int(delta.total_seconds() // 3600)}h atrás"
            return format_html('<span style="color: {};">{}</span>', color, text)
        return "Nunca conectada"

    last_heartbeat.short_description = "Último Heartbeat"

    def heartbeats_count(self, obj):
        count = (
            obj.heartbeats_count
            if hasattr(obj, "heartbeats_count")
            else obj.heartbeats.count()
        )
        if count > 0:
            url = (
                reverse("admin:hardware_cameraheartbeats_changelist")
                + f"?camera__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"

    heartbeats_count.short_description = "Heartbeats"

    actions = ["activate_cameras", "deactivate_cameras", "set_maintenance"]

    def activate_cameras(self, request, queryset):
        updated = queryset.update(state="ACTIVE")
        self.message_user(request, f"{updated} câmeras ativadas.")

    activate_cameras.short_description = "Ativar câmeras selecionadas"

    def deactivate_cameras(self, request, queryset):
        updated = queryset.update(state="INACTIVE")
        self.message_user(request, f"{updated} câmeras desativadas.")

    deactivate_cameras.short_description = "Desativar câmeras selecionadas"

    def set_maintenance(self, request, queryset):
        updated = queryset.update(state="MAINTENANCE")
        self.message_user(request, f"{updated} câmeras em manutenção.")

    set_maintenance.short_description = "Definir como manutenção"


class CameraHeartbeatsAdmin(admin.ModelAdmin):
    list_display = ["camera_info", "received_at", "payload_preview", "time_since"]
    list_filter = ["received_at", "camera__client"]
    search_fields = ["camera__camera_code", "camera__client__name"]
    readonly_fields = ["received_at", "payload_json"]
    date_hierarchy = "received_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("camera__client")

    def camera_info(self, obj):
        return f"{obj.camera.camera_code} ({obj.camera.client.name})"

    camera_info.short_description = "Câmera"

    def payload_preview(self, obj):
        if obj.payload_json:
            preview = str(obj.payload_json)[:100]
            return preview + "..." if len(str(obj.payload_json)) > 100 else preview
        return "-"

    payload_preview.short_description = "Payload"

    def time_since(self, obj):
        delta = timezone.now() - obj.received_at
        if delta.total_seconds() < 60:
            return "Agora"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() // 60)} min atrás"
        elif delta.days < 1:
            return f"{int(delta.total_seconds() // 3600)}h atrás"
        else:
            return f"{delta.days} dias atrás"

    time_since.short_description = "Há quanto tempo"


# Registrar no admin_site customizado
admin_site.register(ApiKeys, ApiKeysAdmin)
admin_site.register(Cameras, CamerasAdmin)
admin_site.register(CameraHeartbeats, CameraHeartbeatsAdmin)
