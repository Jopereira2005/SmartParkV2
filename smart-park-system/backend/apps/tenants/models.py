from django.db import models
from django.contrib.auth.models import User, Group
from apps.core.models import BaseModel, SoftDeleteManager


class Clients(BaseModel):
    ONBOARDING_STATUS_CHOICES = [
        ("PENDING", "Pendente"),
        ("ACTIVE", "Ativo"),
        ("SUSPENDED", "Suspenso"),
        ("CANCELLED", "Cancelado"),
    ]

    name = models.CharField(max_length=120)
    onboarding_status = models.CharField(
        max_length=32, choices=ONBOARDING_STATUS_CHOICES, default="PENDING"
    )

    objects = SoftDeleteManager()

    class Meta:
        db_table = "clients"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        indexes = [
            models.Index(fields=["name"], name="ix_clients_name"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_onboarding_status_display()})"


class ClientMembers(BaseModel):
    client = models.ForeignKey(
        "Clients",
        on_delete=models.PROTECT,
        db_column="client_id",
        related_name="client_members",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="user_id",
        related_name="client_members",
    )
    role = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        db_column="role_id",
        related_name="client_members",
    )
    # Estabelecimento específico (opcional - null para client_admin)
    establishment = models.ForeignKey(
        "catalog.Establishments",
        on_delete=models.PROTECT,
        db_column="establishment_id",
        related_name="client_members",
        null=True,
        blank=True,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "client_members"
        verbose_name = "Membro do Cliente"
        verbose_name_plural = "Membros dos Clientes"
        constraints = [
            # Constraint único: usuário + cliente + estabelecimento + role
            models.UniqueConstraint(
                fields=["client", "user", "establishment", "role"],
                name="uq_client_members_unique",
            ),
        ]

    def __str__(self):
        establishment_str = (
            f" - {self.establishment.name}" if self.establishment else ""
        )
        return f"{self.user.username} - {self.client.name}{establishment_str} ({self.role.name})"
