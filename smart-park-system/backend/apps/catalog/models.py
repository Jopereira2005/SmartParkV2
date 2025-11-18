from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from apps.core.models import BaseModel, TenantModel, SoftDeleteManager, TenantManager


class LotManager(SoftDeleteManager):
    """Manager customizado para Lots que filtra por establishment.client"""
    def for_user(self, user):
        """Filtra lots pelos clientes do usuário via establishment"""
        user_clients = user.client_members.values_list('client_id', flat=True)
        return self.filter(establishment__client_id__in=user_clients)


class SlotManager(SoftDeleteManager):
    """Manager customizado para Slots que filtra por lot.establishment.client"""
    def for_user(self, user):
        """Filtra slots pelos clientes do usuário via lot.establishment"""
        user_clients = user.client_members.values_list('client_id', flat=True)
        return self.filter(lot__establishment__client_id__in=user_clients)


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
    
    # Generic relation to Address
    addresses = GenericRelation('core.Address', related_query_name='establishment')

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


class Lots(BaseModel):
    establishment = models.ForeignKey(
        "Establishments",
        on_delete=models.PROTECT,
        db_column="establishment_id",
        related_name="lots",
    )
    lot_code = models.CharField(max_length=50)
    name = models.CharField(max_length=120, null=True, blank=True)

    objects = LotManager()

    class Meta:
        db_table = "lots"
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        constraints = [
            models.UniqueConstraint(
                fields=["establishment", "lot_code"], name="uq_lots_establishment_code"
            ),
        ]

    def __str__(self):
        return f"{self.lot_code} - {self.establishment.name}"
    
    @property
    def client(self):
        """Property para acessar o client via establishment"""
        return self.establishment.client


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


class Slots(BaseModel):
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

    objects = SlotManager()

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
    
    @property
    def client(self):
        """Property para acessar o client via lot.establishment"""
        return self.lot.establishment.client

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


class UserFavorites(BaseModel):
    """
    Modelo para gerenciar estabelecimentos favoritos dos usuários
    """
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="favorites",
    )
    establishment = models.ForeignKey(
        "Establishments",
        on_delete=models.CASCADE,
        db_column="establishment_id",
        related_name="favorited_by",
    )
    
    objects = SoftDeleteManager()

    class Meta:
        db_table = "user_favorites"
        verbose_name = "Favorito do Usuário"
        verbose_name_plural = "Favoritos dos Usuários"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "establishment"], 
                name="uq_user_favorites_user_establishment"
            ),
        ]
        indexes = [
            models.Index(fields=["user"], name="ix_uf_user"),
            models.Index(fields=["establishment"], name="ix_uf_establishment"),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.establishment.name}"
