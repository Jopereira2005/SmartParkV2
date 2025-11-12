from rest_framework import serializers
from .models import SlotStatusEvents
from apps.core.serializers import TenantModelSerializer, SoftDeleteSerializerMixin


class SlotStatusEventSerializer(TenantModelSerializer, SoftDeleteSerializerMixin):
    class Meta(TenantModelSerializer.Meta):
        model = SlotStatusEvents
        fields = TenantModelSerializer.Meta.fields + [
            'event_id', 'event_type', 'occurred_at', 'lot', 'camera', 
            'sequence', 'slot', 'prev_status', 'prev_vehicle', 'curr_status', 
            'curr_vehicle', 'confidence', 'source_model', 'source_version', 'received_at'
        ]


class SlotStatusEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotStatusEvents
        fields = [
            'event_type', 'occurred_at', 'lot', 'camera', 'sequence',
            'slot', 'prev_status', 'prev_vehicle', 'curr_status', 
            'curr_vehicle', 'confidence', 'source_model', 'source_version'
        ]

    def create(self, validated_data):
        # Definir o client baseado no slot
        slot = validated_data['slot']
        validated_data['client'] = slot.client
        return super().create(validated_data)
