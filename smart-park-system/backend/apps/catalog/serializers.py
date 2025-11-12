from rest_framework import serializers
from typing import Dict, Any, Optional
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
from apps.core.serializers import (
    BaseModelSerializer,
    TenantModelSerializer,
    SoftDeleteSerializerMixin,
)


class StoreTypeSerializer(BaseModelSerializer, SoftDeleteSerializerMixin):
    class Meta(BaseModelSerializer.Meta):
        model = StoreTypes
        fields = BaseModelSerializer.Meta.fields + ["name"]


class EstablishmentSerializer(TenantModelSerializer, SoftDeleteSerializerMixin):
    store_type = StoreTypeSerializer(read_only=True)
    store_type_id = serializers.IntegerField(write_only=True, required=False)

    class Meta(TenantModelSerializer.Meta):
        model = Establishments
        fields = TenantModelSerializer.Meta.fields + [
            "name",
            "store_type",
            "store_type_id",
            "address",
            "city",
            "state",
            "lat",
            "lng",
        ]


class LotSerializer(TenantModelSerializer, SoftDeleteSerializerMixin):
    establishment = EstablishmentSerializer(read_only=True)
    establishment_id = serializers.IntegerField(write_only=True)

    class Meta(TenantModelSerializer.Meta):
        model = Lots
        fields = TenantModelSerializer.Meta.fields + [
            "establishment",
            "establishment_id",
            "lot_code",
            "name",
        ]


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
        ]

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
