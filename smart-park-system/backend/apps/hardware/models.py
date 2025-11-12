from django.db import models
from apps.core.models import BaseModel, TenantModel, SoftDeleteManager, TenantManager


class ApiKeys(TenantModel):
    name = models.CharField(max_length=100)
    key_id = models.CharField(max_length=64, unique=True)
    hmac_secret_hash = models.TextField()
    enabled = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        db_table = "api_keys"
        verbose_name = "Chave de API"
        verbose_name_plural = "Chaves de API"

    def __str__(self):
        return f"{self.name} ({self.key_id})"


class Cameras(TenantModel):
    STATE_CHOICES = [
        ("UNASSIGNED", "Não atribuída"),
        ("ASSIGNED", "Atribuída"),
        ("ACTIVE", "Ativa"),
        ("INACTIVE", "Inativa"),
        ("MAINTENANCE", "Manutenção"),
        ("ERROR", "Erro"),
    ]

    establishment = models.ForeignKey(
        "catalog.Establishments",
        on_delete=models.PROTECT,
        db_column="establishment_id",
        null=True,
        blank=True,
        related_name="cameras",
    )
    lot = models.ForeignKey(
        "catalog.Lots",
        on_delete=models.PROTECT,
        db_column="lot_id",
        null=True,
        blank=True,
        related_name="cameras",
    )
    camera_code = models.CharField(max_length=50)
    api_key = models.ForeignKey(
        "ApiKeys",
        on_delete=models.PROTECT,
        db_column="api_key_id",
        related_name="cameras",
    )
    state = models.CharField(max_length=16, choices=STATE_CHOICES, default="UNASSIGNED")
    last_seen_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        db_table = "cameras"
        verbose_name = "Câmera"
        verbose_name_plural = "Câmeras"
        constraints = [
            models.UniqueConstraint(
                fields=["client", "camera_code"], name="uq_cameras_client_code"
            ),
        ]

    def __str__(self):
        return f"{self.camera_code} - {self.client.name} ({self.get_state_display()})"


class CameraHeartbeats(BaseModel):
    camera = models.ForeignKey(
        "Cameras",
        on_delete=models.PROTECT,
        db_column="camera_id",
        related_name="heartbeats",
    )
    received_at = models.DateTimeField(auto_now_add=True)
    payload_json = models.JSONField(null=True, blank=True)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "camera_heartbeats"
        verbose_name = "Heartbeat da Câmera"
        verbose_name_plural = "Heartbeats das Câmeras"
        indexes = [
            models.Index(
                fields=["camera", "received_at"], name="ix_cam_heartbeats_cam_rec_at"
            ),
        ]

    def __str__(self):
        return f"Heartbeat {self.camera.camera_code} - {self.received_at}"
