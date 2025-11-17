from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import SlotStatusEvents

# Importar o admin_site customizado
from smartpark.admin import admin_site


class SlotStatusEventsAdmin(admin.ModelAdmin):
    list_display = [
        "event_id_short",
        "event_type_display",
        "slot_info",
        "client",
        "timing_info",
        "processed_time",
    ]
    list_filter = [
        "event_type",
        "occurred_at",
        "received_at",
        "client",
        "slot__lot__establishment",
    ]
    search_fields = [
        "event_id",
        "slot__slot_code",
        "client__name",
        "slot__lot__lot_code",
        "slot__lot__establishment__name",
    ]
    readonly_fields = [
        "event_id",
        "received_at",
    ]
    date_hierarchy = "occurred_at"

    fieldsets = (
        (
            "Informações do Evento",
            {"fields": ("event_id", "event_type", "occurred_at", "received_at")},
        ),
        ("Localização", {"fields": ("client", "slot", "lot", "camera")}),
        (
            "Status",
            {"fields": ("prev_status", "curr_status", "prev_vehicle", "curr_vehicle")},
        ),
        (
            "Dados Técnicos",
            {
                "fields": ("confidence", "source_model", "source_version", "sequence"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "client",
                "slot__lot__establishment",
                "lot__establishment",
                "camera",
            )
        )

    def event_id_short(self, obj):
        return f"{str(obj.event_id)[:8]}..."

    event_id_short.short_description = "Event ID"

    def event_type_display(self, obj):
        colors = {
            "SLOT_OCCUPIED": "red",
            "SLOT_FREED": "green",
            "SLOT_RESERVED": "orange",
            "SLOT_MAINTENANCE": "gray",
        }
        color = colors.get(obj.event_type, "blue")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_event_type_display(),
        )

    event_type_display.short_description = "Tipo de Evento"

    def slot_info(self, obj):
        if obj.slot:
            establishment = obj.slot.lot.establishment.name
            return f"{obj.slot.slot_code} ({establishment})"
        elif obj.lot:
            return f"Lote: {obj.lot.lot_code}"
        elif obj.establishment:
            return f"Estabelecimento: {obj.establishment.name}"
        return "N/A"

    slot_info.short_description = "Localização"

    def timing_info(self, obj):
        if not obj.occurred_at or not obj.received_at:
            return "N/A - Dados incompletos"

        occurred = obj.occurred_at.strftime("%d/%m %H:%M:%S")
        received = obj.received_at.strftime("%d/%m %H:%M:%S")

        # Calcular delay
        delay = obj.received_at - obj.occurred_at
        delay_seconds = delay.total_seconds()

        color = (
            "green" if delay_seconds < 5 else "orange" if delay_seconds < 30 else "red"
        )

        return format_html(
            'Ocorreu: {}<br>Recebido: {}<br><span style="color: {};">Delay: {}s</span>',
            occurred,
            received,
            color,
            f"{delay_seconds:.1f}",
        )

    timing_info.short_description = "Timing"

    def processed_time(self, obj):
        if not obj.occurred_at or not obj.received_at:
            return "N/A"

        delay = obj.received_at - obj.occurred_at
        delay_seconds = delay.total_seconds()

        if delay_seconds < 1:
            color = "green"
            text = "Instantâneo"
        elif delay_seconds < 5:
            color = "green"
            text = f"{delay_seconds:.1f}s"
        elif delay_seconds < 30:
            color = "orange"
            text = f"{delay_seconds:.1f}s"
        else:
            color = "red"
            text = f"{delay_seconds:.1f}s"

        return format_html('<span style="color: {};">{}</span>', color, text)

    processed_time.short_description = "Tempo de Processamento"

    def processed_time_detail(self, obj):
        if not obj.received_at or not obj.occurred_at:
            return "N/A - Dados incompletos"

        delay = obj.received_at - obj.occurred_at
        delay_seconds = delay.total_seconds()

        info = f"Ocorrido em: {obj.occurred_at}<br>"
        info += f"Recebido em: {obj.received_at}<br>"
        info += f"Delay: {delay_seconds:.2f} segundos<br>"

        if delay_seconds > 30:
            info += '<span style="color: red;">⚠️ Delay alto - verificar conectividade</span>'
        elif delay_seconds > 5:
            info += '<span style="color: orange;">⚠️ Delay moderado</span>'
        else:
            info += '<span style="color: green;">✓ Processamento rápido</span>'

        return format_html(info)

    processed_time_detail.short_description = "Detalhes de Timing"

    def event_payload_formatted(self, obj):
        # Since SlotStatusEvents doesn't have event_payload,
        # we can show other relevant data
        data = {
            "event_type": obj.event_type,
            "curr_status": obj.curr_status,
            "prev_status": obj.prev_status,
            "confidence": float(obj.confidence) if obj.confidence else None,
            "source_model": obj.source_model,
            "source_version": obj.source_version,
        }

        import json

        try:
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            return format_html("<pre>{}</pre>", formatted)
        except:
            return str(data)

    event_payload_formatted.short_description = "Payload do Evento"


# Registrar no admin_site customizado
admin_site.register(SlotStatusEvents, SlotStatusEventsAdmin)
