from rest_framework import serializers
from django.utils import timezone
from .models import Address


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Serializer base com campos comuns
    """
    public_id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ['id', 'public_id', 'created_at', 'updated_at', 'is_deleted']


class TenantModelSerializer(BaseModelSerializer):
    """
    Serializer base para models com tenant
    """
    client_name = serializers.CharField(source='client.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        fields = BaseModelSerializer.Meta.fields + ['client', 'client_name']


class SoftDeleteSerializerMixin:
    """
    Mixin para serializers que lidam com soft delete
    """
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['is_deleted'] = instance.is_deleted
        return data


class TimestampedSerializerMixin:
    """
    Mixin para serializers que lidam com timestamps
    """
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'created_at'):
            data['created_at'] = instance.created_at
        if hasattr(instance, 'updated_at'):
            data['updated_at'] = instance.updated_at
        return data


class ValidationMixin:
    """
    Mixin com validações comuns
    """
    def validate_deleted_at(self, value):
        """Validação para deleted_at"""
        if value and value > timezone.now():
            raise serializers.ValidationError("deleted_at não pode ser no futuro")
        return value

    def validate_public_id(self, value):
        """Validação para public_id"""
        if value and self.Meta.model.objects.filter(public_id=value).exists():
            raise serializers.ValidationError("public_id já existe")
        return value


class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Address
    """
    
    class Meta:
        model = Address
        fields = [
            'id',
            'street',
            'number',
            'complement',
            'neighborhood',
            'city',
            'state',
            'postal_code',
            'country',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']