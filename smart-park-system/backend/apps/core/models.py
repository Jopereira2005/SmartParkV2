from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Modelo base com campos comuns a todos os models principais
    """
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        """Marca o objeto como deletado (soft delete)"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        """Restaura um objeto soft deleted"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        """Verifica se o objeto foi soft deleted"""
        return self.deleted_at is not None


class TenantModel(BaseModel):
    """
    Modelo base para entidades que pertencem a um cliente (tenant)
    """
    client = models.ForeignKey(
        "tenants.Clients",
        on_delete=models.PROTECT,
        db_column="client_id",
        related_name="%(class)s_set"
    )

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """
    Manager que filtra automaticamente objetos soft deleted
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """Retorna queryset incluindo objetos soft deleted"""
        return super().get_queryset()

    def only_deleted(self):
        """Retorna apenas objetos soft deleted"""
        return super().get_queryset().filter(deleted_at__isnull=False)


class TenantManager(SoftDeleteManager):
    """
    Manager para models com tenant que filtra por cliente do usuário
    """
    def for_user(self, user):
        """Filtra objetos pelos clientes do usuário"""
        user_clients = user.client_members.values_list('client_id', flat=True)
        return self.filter(client_id__in=user_clients)