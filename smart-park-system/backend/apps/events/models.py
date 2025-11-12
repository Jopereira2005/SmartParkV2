from django.db import models
import uuid
from apps.core.models import TenantModel, TenantManager


class SlotStatusEvents(TenantModel):
    EVENT_TYPE_CHOICES = [
        ("STATUS_CHANGE", "Mudança de Status"),
        ("VEHICLE_DETECTED", "Veículo Detectado"),
        ("VEHICLE_LEFT", "Veículo Saiu"),
        ("MAINTENANCE_START", "Início de Manutenção"),
        ("MAINTENANCE_END", "Fim de Manutenção"),
        ("RESERVATION_START", "Início de Reserva"),
        ("RESERVATION_END", "Fim de Reserva"),
    ]

    event_id = models.UUIDField(unique=True, default=uuid.uuid4)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    occurred_at = models.DateTimeField()
    lot = models.ForeignKey(
        "catalog.Lots",
        on_delete=models.PROTECT,
        db_column="lot_id",
        related_name="slot_status_events",
    )
    camera = models.ForeignKey(
        "hardware.Cameras",
        on_delete=models.PROTECT,
        db_column="camera_id",
        null=True,
        blank=True,
        related_name="slot_status_events",
    )
    sequence = models.BigIntegerField(null=True, blank=True)
    slot = models.ForeignKey(
        "catalog.Slots",
        on_delete=models.PROTECT,
        db_column="slot_id",
        related_name="slot_status_events",
    )
    prev_status = models.CharField(max_length=16, null=True, blank=True)
    prev_vehicle = models.ForeignKey(
        "catalog.VehicleTypes",
        on_delete=models.PROTECT,
        db_column="prev_vehicle_id",
        null=True,
        blank=True,
        related_name="prev_slot_status_events",
    )
    curr_status = models.CharField(max_length=16)
    curr_vehicle = models.ForeignKey(
        "catalog.VehicleTypes",
        on_delete=models.PROTECT,
        db_column="curr_vehicle_id",
        null=True,
        blank=True,
        related_name="curr_slot_status_events",
    )
    confidence = models.DecimalField(
        max_digits=4, decimal_places=3, null=True, blank=True
    )
    source_model = models.CharField(max_length=60, null=True, blank=True)
    source_version = models.CharField(max_length=30, null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        db_table = "slot_status_events"
        verbose_name = "Evento de Status"
        verbose_name_plural = "Eventos de Status"
        indexes = [
            models.Index(
                fields=["slot", "occurred_at"], name="ix_slot_sts_events_occ_at"
            ),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.slot.slot_code} ({self.occurred_at})"
