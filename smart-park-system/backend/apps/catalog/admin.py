from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    StoreTypes,
    Establishments,
    Lots,
    Slots,
    SlotTypes,
    VehicleTypes,
    SlotStatus,
    SlotStatusHistory,
)

# Importar o admin_site customizado
from smartpark.admin import admin_site


class LotsInline(admin.TabularInline):
    model = Lots
    extra = 0
    fields = ["lot_code", "name", "slots_count"]
    readonly_fields = ["slots_count"]

    def slots_count(self, obj):
        if obj.pk:
            return obj.slots.count()
        return 0

    slots_count.short_description = "Vagas"


class SlotsInline(admin.TabularInline):
    model = Slots
    extra = 0
    fields = ["slot_code", "slot_type", "active", "current_status_display"]
    readonly_fields = ["current_status_display"]

    def current_status_display(self, obj):
        if obj.pk:
            try:
                status = obj.current_status.first()
                if status:
                    color = "green" if status.status == "FREE" else "red"
                    return format_html(
                        '<span style="color: {};">{}</span>',
                        color,
                        status.get_status_display(),
                    )
            except:
                pass
            return format_html('<span style="color: gray;">Sem status</span>')
        return "-"

    current_status_display.short_description = "Status Atual"


class StoreTypesAdmin(admin.ModelAdmin):
    list_display = ["name", "establishments_count"]
    search_fields = ["name"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(establishments_count=Count("establishments"))
        )

    def establishments_count(self, obj):
        count = obj.establishments_count
        if count > 0:
            url = (
                reverse("admin:catalog_establishments_changelist")
                + f"?store_type__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"

    establishments_count.short_description = "Estabelecimentos"


class EstablishmentsAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "client",
        "store_type",
        "location_info",
        "lots_count",
        "total_slots",
        "occupied_slots",
        "created_at",
    ]
    list_filter = ["store_type", "city", "state", "created_at", "client"]
    search_fields = ["name", "client__name", "address", "city"]
    inlines = [LotsInline]

    fieldsets = (
        ("Informações Básicas", {"fields": ("name", "client", "store_type")}),
        ("Localização", {"fields": ("address", "city", "state", "lat", "lng")}),
        (
            "Dados de Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                lots_count=Count("lots"),
                total_slots=Count("lots__slots"),
                occupied_slots_count=Count(
                    "lots__slots__current_status",
                    filter=Q(lots__slots__current_status__status="OCCUPIED"),
                ),
            )
        )

    def location_info(self, obj):
        return f"{obj.city}, {obj.state}"

    location_info.short_description = "Localização"

    def lots_count(self, obj):
        count = obj.lots_count if hasattr(obj, "lots_count") else obj.lots.count()
        if count > 0:
            url = (
                reverse("admin:catalog_lots_changelist")
                + f"?establishment__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"

    lots_count.short_description = "Lotes"

    def total_slots(self, obj):
        count = (
            obj.total_slots
            if hasattr(obj, "total_slots")
            else sum(lot.slots.count() for lot in obj.lots.all())
        )
        return count

    total_slots.short_description = "Total Vagas"

    def occupied_slots(self, obj):
        count = obj.occupied_slots_count if hasattr(obj, "occupied_slots_count") else 0
        total = self.total_slots(obj)
        if total > 0:
            percentage = (count / total) * 100
            color = (
                "red" if percentage > 80 else "orange" if percentage > 50 else "green"
            )
            # Manually format to avoid SafeString issues
            percentage_str = f"{percentage:.1f}"
            html = f'<span style="color: {color};">{count}/{total} ({percentage_str}%)</span>'
            return mark_safe(html)
        return "0/0"

    occupied_slots.short_description = "Ocupação"


class LotsAdmin(admin.ModelAdmin):
    list_display = [
        "lot_code",
        "name",
        "establishment",
        "client_info",
        "slots_count",
        "occupied_slots",
        "created_at",
    ]
    list_filter = ["created_at", "establishment__client", "establishment"]
    search_fields = ["lot_code", "name", "establishment__name"]
    inlines = [SlotsInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("establishment__client")
            .annotate(
                slots_count=Count("slots"),
                occupied_slots_count=Count(
                    "slots__current_status",
                    filter=Q(slots__current_status__status="OCCUPIED"),
                ),
            )
        )

    def client_info(self, obj):
        return obj.establishment.client.name

    client_info.short_description = "Cliente"

    def slots_count(self, obj):
        count = obj.slots_count if hasattr(obj, "slots_count") else obj.slots.count()
        if count > 0:
            url = (
                reverse("admin:catalog_slots_changelist") + f"?lot__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"

    slots_count.short_description = "Vagas"

    def occupied_slots(self, obj):
        count = obj.occupied_slots_count if hasattr(obj, "occupied_slots_count") else 0
        total = obj.slots_count if hasattr(obj, "slots_count") else obj.slots.count()
        if total > 0:
            percentage = (count / total) * 100
            color = (
                "red" if percentage > 80 else "orange" if percentage > 50 else "green"
            )
            # Manually format to avoid SafeString issues
            percentage_str = f"{percentage:.1f}"
            html = f'<span style="color: {color};">{count}/{total} ({percentage_str}%)</span>'
            return mark_safe(html)
        return "0/0"

    occupied_slots.short_description = "Ocupação"


class SlotsAdmin(admin.ModelAdmin):
    list_display = [
        "slot_code",
        "lot_info",
        "slot_type",
        "active",
        "current_status_display",
        "last_status_change",
        "created_at",
    ]
    list_filter = [
        "slot_type",
        "active",
        "created_at",
        "lot__establishment__client",
        "current_status__status",
    ]
    search_fields = ["slot_code", "lot__lot_code", "lot__establishment__name"]

    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("slot_code", "lot", "slot_type", "active")},
        ),
        (
            "Status Atual",
            {"fields": ("current_status_info",), "classes": ("collapse",)},
        ),
        (
            "Dados de Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ["created_at", "updated_at", "current_status_info"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("lot__establishment__client", "slot_type")
            .prefetch_related("current_status")
        )

    def lot_info(self, obj):
        return f"{obj.lot.lot_code} ({obj.lot.establishment.name})"

    lot_info.short_description = "Lote"

    def current_status_display(self, obj):
        try:
            # Get the single current status (unique constraint ensures only one)
            status = obj.current_status.get()
            colors = {
                "FREE": "green",
                "OCCUPIED": "red",
                "RESERVED": "orange",
                "MAINTENANCE": "gray",
            }
            color = colors.get(status.status, "black")
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                status.get_status_display(),
            )
        except:
            return format_html('<span style="color: gray;">Sem status</span>')

    current_status_display.short_description = "Status"

    def last_status_change(self, obj):
        try:
            status = obj.current_status.get()
            return status.changed_at.strftime("%d/%m %H:%M")
        except:
            return "-"

    last_status_change.short_description = "Última Mudança"

    def current_status_info(self, obj):
        try:
            status = obj.current_status.get()
            info = f"Status: {status.get_status_display()}<br>"
            info += f"Alterado em: {status.changed_at}<br>"
            if status.vehicle_type:
                info += f"Tipo de Veículo: {status.vehicle_type.name}<br>"
            if status.confidence:
                info += f"Confiança: {status.confidence}%"
            return format_html(info)
        except:
            return "Nenhum status registrado"

    current_status_info.short_description = "Informações do Status"

    actions = ["activate_slots", "deactivate_slots"]

    def activate_slots(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"{updated} vagas ativadas.")

    activate_slots.short_description = "Ativar vagas selecionadas"

    def deactivate_slots(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"{updated} vagas desativadas.")

    deactivate_slots.short_description = "Desativar vagas selecionadas"


class SlotTypesAdmin(admin.ModelAdmin):
    list_display = ["name", "slots_count"]
    search_fields = ["name"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(slots_count=Count("slots"))

    def slots_count(self, obj):
        count = obj.slots_count
        if count > 0:
            url = (
                reverse("admin:catalog_slots_changelist")
                + f"?slot_type__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"

    slots_count.short_description = "Vagas"


class VehicleTypesAdmin(admin.ModelAdmin):
    list_display = ["name", "active_slots_count"]
    search_fields = ["name"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                active_slots_count=Count(
                    "slot_statuses", filter=Q(slot_statuses__status="OCCUPIED")
                )
            )
        )

    def active_slots_count(self, obj):
        count = obj.active_slots_count
        return f"{count} vagas ocupadas"

    active_slots_count.short_description = "Ocupação Atual"


class SlotStatusAdmin(admin.ModelAdmin):
    list_display = [
        "slot_info",
        "status",
        "vehicle_type",
        "confidence_display",
        "changed_at",
    ]
    list_filter = ["status", "vehicle_type", "changed_at"]
    search_fields = ["slot__slot_code", "slot__lot__lot_code"]
    readonly_fields = ["changed_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("slot__lot__establishment", "vehicle_type")
        )

    def slot_info(self, obj):
        return f"{obj.slot.slot_code} ({obj.slot.lot.establishment.name})"

    slot_info.short_description = "Vaga"

    def confidence_display(self, obj):
        if obj.confidence:
            color = (
                "green"
                if obj.confidence >= 9
                else "orange" if obj.confidence >= 7 else "red"
            )
            # Manually format to avoid SafeString issues
            confidence_str = f"{obj.confidence:.1f}"
            html = f'<span style="color: {color};">{confidence_str}%</span>'
            return mark_safe(html)
        return "-"

    confidence_display.short_description = "Confiança"


class SlotStatusHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "slot_info",
        "status",
        "vehicle_type",
        "confidence_display",
        "recorded_at",
    ]
    list_filter = ["status", "vehicle_type", "recorded_at"]
    search_fields = ["slot__slot_code", "slot__lot__lot_code"]
    readonly_fields = ["recorded_at"]
    date_hierarchy = "recorded_at"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("slot__lot__establishment", "vehicle_type")
        )

    def slot_info(self, obj):
        return f"{obj.slot.slot_code} ({obj.slot.lot.establishment.name})"

    slot_info.short_description = "Vaga"

    def confidence_display(self, obj):
        if obj.confidence:
            color = (
                "green"
                if obj.confidence >= 9
                else "orange" if obj.confidence >= 7 else "red"
            )
            # Manually format to avoid SafeString issues
            confidence_str = f"{obj.confidence:.1f}"
            html = f'<span style="color: {color};">{confidence_str}%</span>'
            return mark_safe(html)
        return "-"

    confidence_display.short_description = "Confiança"


# Registrar no admin_site customizado
admin_site.register(StoreTypes, StoreTypesAdmin)
admin_site.register(Establishments, EstablishmentsAdmin)
admin_site.register(Lots, LotsAdmin)
admin_site.register(Slots, SlotsAdmin)
admin_site.register(SlotTypes, SlotTypesAdmin)
admin_site.register(VehicleTypes, VehicleTypesAdmin)
admin_site.register(SlotStatus, SlotStatusAdmin)
admin_site.register(SlotStatusHistory, SlotStatusHistoryAdmin)
