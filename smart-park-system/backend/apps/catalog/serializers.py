from rest_framework import serializers
from typing import Dict, Any, Optional
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field
from .models import (
    StoreTypes,
    Establishments,
    Lots,
    Slots,
    SlotTypes,
    VehicleTypes,
    SlotStatus,
    SlotStatusHistory,
    UserFavorites,
)
from apps.core.serializers import (
    BaseModelSerializer,
    TenantModelSerializer,
    SoftDeleteSerializerMixin,
    AddressSerializer,
)
from apps.core.models import Address


class StoreTypeSerializer(BaseModelSerializer, SoftDeleteSerializerMixin):
    class Meta(BaseModelSerializer.Meta):
        model = StoreTypes
        fields = BaseModelSerializer.Meta.fields + ["name"]


class EstablishmentSerializer(TenantModelSerializer, SoftDeleteSerializerMixin):
    store_type = StoreTypeSerializer(read_only=True)
    store_type_id = serializers.IntegerField(write_only=True, required=False)
    address_detail = serializers.SerializerMethodField()

    class Meta(TenantModelSerializer.Meta):
        model = Establishments
        fields = TenantModelSerializer.Meta.fields + [
            "name",
            "store_type",
            "store_type_id",
            "address_detail",
        ]
    
    @extend_schema_field(AddressSerializer(allow_null=True))
    def get_address_detail(self, obj) -> dict | None:
        """Retorna o primeiro endereço do estabelecimento"""
        address = obj.addresses.first()
        if address:
            return AddressSerializer(address).data
        return None


class CreateEstablishmentWithAddressSerializer(TenantModelSerializer, SoftDeleteSerializerMixin):
    """
    Serializer para criar estabelecimento com endereço incluído
    """
    
    store_type = StoreTypeSerializer(read_only=True)
    store_type_id = serializers.IntegerField(write_only=True, required=False)
    address = AddressSerializer(write_only=True, required=False)

    class Meta(TenantModelSerializer.Meta):
        model = Establishments
        fields = TenantModelSerializer.Meta.fields + [
            "name",
            "store_type",
            "store_type_id",
            "address",
        ]

    def create(self, validated_data):
        address_data = validated_data.pop("address", None)
        
        # Criar o estabelecimento
        establishment = super().create(validated_data)
        
        # Criar endereço se fornecido
        if address_data:
            content_type = ContentType.objects.get_for_model(Establishments)
            Address.objects.create(
                content_type=content_type,
                object_id=establishment.id,
                **address_data
            )
        
        return establishment


class LotSerializer(TenantModelSerializer, SoftDeleteSerializerMixin):
    establishment = EstablishmentSerializer(read_only=True)
    establishment_id = serializers.IntegerField(write_only=True)
    client = serializers.SerializerMethodField()

    class Meta(TenantModelSerializer.Meta):
        model = Lots
        fields = TenantModelSerializer.Meta.fields + [
            "establishment",
            "establishment_id",
            "lot_code",
            "name",
            "client",
        ]
    
    @extend_schema_field(serializers.CharField())
    def get_client(self, obj) -> str:
        """Retorna o nome do cliente através do establishment"""
        return obj.client.name if obj.client else None


class SlotTypeSerializer(BaseModelSerializer, SoftDeleteSerializerMixin):
    class Meta(BaseModelSerializer.Meta):
        model = SlotTypes
        fields = BaseModelSerializer.Meta.fields + ["name"]


class VehicleTypeSerializer(BaseModelSerializer, SoftDeleteSerializerMixin):
    class Meta(BaseModelSerializer.Meta):
        model = VehicleTypes
        fields = BaseModelSerializer.Meta.fields + ["name"]


class SlotSerializer(TenantModelSerializer, SoftDeleteSerializerMixin):
    lot = LotSerializer(read_only=True)
    lot_id = serializers.IntegerField(write_only=True)
    slot_type = SlotTypeSerializer(read_only=True)
    slot_type_id = serializers.IntegerField(write_only=True)
    current_status = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()

    class Meta(TenantModelSerializer.Meta):
        model = Slots
        fields = TenantModelSerializer.Meta.fields + [
            "lot",
            "lot_id",
            "slot_code",
            "slot_type",
            "slot_type_id",
            "polygon_json",
            "active",
            "current_status",
            "client",
        ]
    
    @extend_schema_field(serializers.CharField())
    def get_client(self, obj) -> str:
        """Retorna o nome do cliente através do lot.establishment"""
        return obj.client.name if obj.client else None

    def get_current_status(self, obj: Slots) -> Optional[Dict[str, Any]]:
        try:
            status = obj.current_status.first()
            if status:
                return {
                    "status": status.status,
                    "vehicle_type": (
                        status.vehicle_type.name if status.vehicle_type else None
                    ),
                    "confidence": status.confidence,
                    "changed_at": status.changed_at,
                }
        except:
            pass
        return None


class SlotStatusSerializer(BaseModelSerializer, SoftDeleteSerializerMixin):
    slot = SlotSerializer(read_only=True)
    slot_id = serializers.IntegerField(write_only=True)
    vehicle_type = VehicleTypeSerializer(read_only=True)
    vehicle_type_id = serializers.IntegerField(write_only=True, required=False)

    class Meta(BaseModelSerializer.Meta):
        model = SlotStatus
        fields = BaseModelSerializer.Meta.fields + [
            "slot",
            "slot_id",
            "status",
            "vehicle_type",
            "vehicle_type_id",
            "confidence",
            "changed_at",
        ]


class SlotStatusHistorySerializer(BaseModelSerializer, SoftDeleteSerializerMixin):
    slot = SlotSerializer(read_only=True)
    vehicle_type = VehicleTypeSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SlotStatusHistory
        fields = BaseModelSerializer.Meta.fields + [
            "slot",
            "status",
            "vehicle_type",
            "confidence",
            "event_id",
            "recorded_at",
        ]


class SlotStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SlotStatus.STATUS_CHOICES)
    vehicle_type_id = serializers.IntegerField(required=False, allow_null=True)
    confidence = serializers.DecimalField(
        max_digits=4, decimal_places=3, required=False, allow_null=True
    )

    def validate_status(self, value):
        if value not in [choice[0] for choice in SlotStatus.STATUS_CHOICES]:
            raise serializers.ValidationError("Status inválido")
        return value

    def validate_vehicle_type_id(self, value):
        if value is not None:
            try:
                VehicleTypes.objects.get(id=value)
            except VehicleTypes.DoesNotExist:
                raise serializers.ValidationError("Tipo de veículo não encontrado")
        return value


class UpdateEstablishmentAddressSerializer(serializers.Serializer):
    """
    Serializer para atualizar apenas o endereço do estabelecimento
    """
    street = serializers.CharField(max_length=255)
    number = serializers.CharField(max_length=20)
    complement = serializers.CharField(max_length=100, required=False, allow_blank=True)
    neighborhood = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=2)
    postal_code = serializers.CharField(max_length=10)
    country = serializers.CharField(max_length=50, default="Brasil")


class UpdateEstablishmentWithAddressSerializer(TenantModelSerializer):
    """
    Serializer para atualizar dados do estabelecimento e endereço
    """
    address = UpdateEstablishmentAddressSerializer(required=False)
    store_type_id = serializers.IntegerField(required=False)

    class Meta(TenantModelSerializer.Meta):
        model = Establishments
        fields = TenantModelSerializer.Meta.fields + [
            "name",
            "store_type_id",
            "address",
        ]
        read_only_fields = ['client', 'client_name']
    
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        
        # Atualizar dados do estabelecimento
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualizar ou criar endereço
        if address_data:
            content_type = ContentType.objects.get_for_model(Establishments)
            address, created = Address.objects.get_or_create(
                content_type=content_type,
                object_id=instance.id,
                defaults=address_data
            )
            if not created:
                for attr, value in address_data.items():
                    setattr(address, attr, value)
                address.save()
        
        return instance


# ==================== PUBLIC SERIALIZERS ====================

class PublicSlotInfoSerializer(serializers.Serializer):
    """Serializer para informações de uma vaga específica"""
    slot_type = serializers.CharField(help_text="Tipo da vaga (ex: Carro, Moto)")
    status = serializers.CharField(help_text="Status da vaga (FREE, OCCUPIED, RESERVED, MAINTENANCE, DISABLED)")


class PublicLotInfoSerializer(serializers.Serializer):
    """Serializer para informações de um lote específico"""
    lot_name = serializers.CharField(help_text="Nome do lote")
    slots = serializers.DictField(
        child=PublicSlotInfoSerializer(),
        help_text="Dicionário com código da vaga como chave e informações como valor"
    )


class PublicEstablishmentLotsResponseSerializer(serializers.Serializer):
    """Serializer para resposta hierárquica de lotes e vagas de um estabelecimento"""
    establishment_id = serializers.IntegerField(help_text="ID do estabelecimento")
    establishment_name = serializers.CharField(help_text="Nome do estabelecimento")
    lots = serializers.DictField(
        child=PublicLotInfoSerializer(),
        help_text="Dicionário com código do lote como chave e informações como valor"
    )
    
    class Meta:
        examples = {
            "example_response": {
                "establishment_id": 1,
                "establishment_name": "Shopping Center Plaza",
                "lots": {
                    "A1": {
                        "lot_name": "Lote A1",
                        "slots": {
                            "A1-001": {
                                "slot_type": "Carro",
                                "status": "FREE"
                            },
                            "A1-002": {
                                "slot_type": "Moto",
                                "status": "OCCUPIED"
                            }
                        }
                    },
                    "B1": {
                        "lot_name": "Lote B1", 
                        "slots": {
                            "B1-001": {
                                "slot_type": "Carro",
                                "status": "RESERVED"
                            }
                        }
                    }
                }
            }
        }


class PublicAllEstablishmentsLotsResponseSerializer(serializers.Serializer):
    """Serializer para resposta paginada de todos os estabelecimentos com lotes e vagas"""
    count = serializers.IntegerField(help_text="Total de estabelecimentos")
    next = serializers.URLField(allow_null=True, help_text="URL da próxima página")
    previous = serializers.URLField(allow_null=True, help_text="URL da página anterior")
    results = serializers.ListField(
        child=PublicEstablishmentLotsResponseSerializer(),
        help_text="Lista de estabelecimentos com suas vagas organizadas hierarquicamente"
    )
    
    class Meta:
        examples = {
            "paginated_response": {
                "count": 25,
                "next": "http://api.example.com/catalog/public/establishments/lots/?page=2",
                "previous": None,
                "results": [
                    {
                        "establishment_id": 1,
                        "establishment_name": "Shopping Center Plaza",
                        "lots": {
                            "A1": {
                                "lot_name": "Lote A1",
                                "slots": {
                                    "A1-001": {
                                        "slot_type": "Carro",
                                        "status": "FREE"
                                    },
                                    "A1-002": {
                                        "slot_type": "Moto",
                                        "status": "OCCUPIED"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "establishment_id": 2,
                        "establishment_name": "Estacionamento Centro",
                        "lots": {
                            "B1": {
                                "lot_name": "Lote Principal",
                                "slots": {
                                    "B1-001": {
                                        "slot_type": "Carro",
                                        "status": "RESERVED"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }


# ==================== USER FAVORITES SERIALIZERS ====================

class UserFavoriteSerializer(BaseModelSerializer):
    """
    Serializer para gerenciar favoritos do usuário
    """
    establishment = EstablishmentSerializer(read_only=True)
    establishment_id = serializers.IntegerField(write_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta(BaseModelSerializer.Meta):
        model = UserFavorites
        fields = BaseModelSerializer.Meta.fields + [
            "user",
            "establishment",
            "establishment_id",
        ]

    def validate(self, data):
        """
        Validar se o favorito já existe
        """
        user = data['user']
        establishment_id = data['establishment_id']
        
        # Verificar se já existe
        if UserFavorites.objects.filter(user=user, establishment_id=establishment_id).exists():
            raise serializers.ValidationError({
                "establishment_id": "Este estabelecimento já está nos seus favoritos."
            })
        
        return data


class FavoriteEstablishmentSerializer(BaseModelSerializer):
    """
    Serializer simplificado para listar estabelecimentos favoritos
    """
    establishment = EstablishmentSerializer(read_only=True)
    
    class Meta(BaseModelSerializer.Meta):
        model = UserFavorites
        fields = ["id", "establishment", "created_at"]
