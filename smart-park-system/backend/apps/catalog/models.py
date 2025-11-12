from django.db import models
from apps.core.models import BaseModel, TenantModel, SoftDeleteManager, TenantManager


class StoreTypes(BaseModel):
    name = models.CharField(max_length=50, unique=True)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "store_types"
        verbose_name = "Tipo de Loja"
        verbose_name_plural = "Tipos de Lojas"

    def __str__(self):
        return self.name


class Establishments(TenantModel):
    name = models.CharField(max_length=120)
    store_type = models.ForeignKey(
        "StoreTypes",
        on_delete=models.PROTECT,
        db_column="store_type_id",
        null=True,
        blank=True,
        related_name="establishments",
    )
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        db_table = "establishments"
        verbose_name = "Estabelecimento"
        verbose_name_plural = "Estabelecimentos"
        constraints = [
            models.UniqueConstraint(
                fields=["client", "name"], name="uq_establishments_client_name"
            ),
        ]
        indexes = [
            models.Index(fields=["store_type"], name="ix_establishments_store_type"),
        ]

    def __str__(self):
        return f"{self.name} ({self.client.name})"


class Lots(TenantModel):
    establishment = models.ForeignKey(
        "Establishments",
        on_delete=models.PROTECT,
        db_column="establishment_id",
        related_name="lots",
    )
    lot_code = models.CharField(max_length=50)
    name = models.CharField(max_length=120, null=True, blank=True)

    objects = TenantManager()

    class Meta:
        db_table = "lots"
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        constraints = [
            models.UniqueConstraint(
                fields=["client", "lot_code"], name="uq_lots_client_code"
            ),
        ]

    def __str__(self):
        return f"{self.lot_code} - {self.establishment.name}"


class SlotTypes(BaseModel):
    name = models.CharField(max_length=30, unique=True)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "slot_types"
        verbose_name = "Tipo de Vaga"
        verbose_name_plural = "Tipos de Vagas"

    def __str__(self):
        return self.name


class VehicleTypes(BaseModel):
    name = models.CharField(max_length=30, unique=True)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "vehicle_types"
        verbose_name = "Tipo de Veículo"
        verbose_name_plural = "Tipos de Veículos"

    def __str__(self):
        return self.name


class Slots(TenantModel):
    lot = models.ForeignKey(
        "Lots", on_delete=models.PROTECT, db_column="lot_id", related_name="slots"
    )
    slot_code = models.CharField(max_length=10)
    slot_type = models.ForeignKey(
        "SlotTypes",
        on_delete=models.PROTECT,
        db_column="slot_type_id",
        related_name="slots",
    )
    polygon_json = models.JSONField()
    active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        db_table = "slots"
        verbose_name = "Vaga"
        verbose_name_plural = "Vagas"
        constraints = [
            models.UniqueConstraint(
                fields=["lot", "slot_code"], name="uq_slots_lot_code"
            ),
        ]

    def __str__(self):
        return f"{self.slot_code} - {self.lot.lot_code}"


class SlotStatus(models.Model):
    STATUS_CHOICES = [
        ("FREE", "Livre"),
        ("OCCUPIED", "Ocupada"),
        ("RESERVED", "Reservada"),
        ("MAINTENANCE", "Manutenção"),
        ("DISABLED", "Desabilitada"),
    ]

    id = models.BigAutoField(primary_key=True)
    slot = models.ForeignKey(
        "Slots",
        on_delete=models.PROTECT,
        db_column="slot_id",
        related_name="current_status",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    vehicle_type = models.ForeignKey(
        "VehicleTypes",
        on_delete=models.PROTECT,
        db_column="vehicle_type_id",
        null=True,
        blank=True,
        related_name="slot_statuses",
    )
    confidence = models.DecimalField(
        max_digits=4, decimal_places=3, null=True, blank=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "slot_status"
        verbose_name = "Status da Vaga"
        verbose_name_plural = "Status das Vagas"
        constraints = [
            models.UniqueConstraint(fields=["slot"], name="uq_slot_status_slot"),
        ]

    def __str__(self):
        return f"{self.slot.slot_code} - {self.get_status_display()}"


class SlotStatusHistory(BaseModel):
    slot = models.ForeignKey(
        "Slots",
        on_delete=models.PROTECT,
        db_column="slot_id",
        related_name="status_history",
    )
    status = models.CharField(max_length=16)
    vehicle_type = models.ForeignKey(
        "VehicleTypes",
        on_delete=models.PROTECT,
        db_column="vehicle_type_id",
        null=True,
        blank=True,
        related_name="slot_status_history",
    )
    confidence = models.DecimalField(
        max_digits=4, decimal_places=3, null=True, blank=True
    )
    event_id = models.UUIDField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "slot_status_history"
        verbose_name = "Histórico de Status"
        verbose_name_plural = "Históricos de Status"
        indexes = [
            models.Index(
                fields=["slot", "recorded_at"], name="ix_slot_hist_slot_rec_at"
            ),
        ]

    def __str__(self):
        return f"{self.slot.slot_code} - {self.status} ({self.recorded_at})"
