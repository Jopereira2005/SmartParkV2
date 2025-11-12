from rest_framework import serializers
from django.contrib.auth.models import User, Group
from typing import Dict, Any
from .models import Clients, ClientMembers
from apps.core.serializers import BaseModelSerializer, SoftDeleteSerializerMixin


class ClientSerializer(BaseModelSerializer, SoftDeleteSerializerMixin):
    class Meta(BaseModelSerializer.Meta):
        model = Clients
        fields = BaseModelSerializer.Meta.fields + ["name", "onboarding_status"]


class ClientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clients
        fields = ["name", "onboarding_status"]

    def create(self, validated_data):
        # Apenas admin pode criar clientes
        return super().create(validated_data)


class ClientMemberSerializer(BaseModelSerializer, SoftDeleteSerializerMixin):
    user = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = ClientMembers
        fields = BaseModelSerializer.Meta.fields + [
            "client",
            "user",
            "role",
            "joined_at",
        ]

    def get_user(self, obj: ClientMembers) -> Dict[str, Any]:
        return {
            "id": obj.user.id,
            "name": obj.user.get_full_name() or obj.user.username,
            "email": obj.user.email,
        }

    def get_role(self, obj: ClientMembers) -> Dict[str, Any]:
        return {"id": obj.role.id, "name": obj.role.name}

    def get_client(self, obj: ClientMembers) -> Dict[str, Any]:
        return {"id": obj.client.id, "name": obj.client.name}


class ClientMemberCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuário não encontrado")

    def validate_group_id(self, value):
        try:
            group = Group.objects.get(id=value)
            return value
        except Group.DoesNotExist:
            raise serializers.ValidationError("Group não encontrado")

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        group_id = attrs.get("group_id")
        client_id = self.context.get("client_id")

        # Verificar se o usuário já é membro deste cliente
        if ClientMembers.objects.filter(client_id=client_id, user_id=user_id).exists():
            raise serializers.ValidationError("Este usuário já é membro deste cliente")

        return attrs

    def create(self, validated_data):
        client_id = self.context.get("client_id")
        return ClientMembers.objects.create(
            client_id=client_id,
            user_id=validated_data["user_id"],
            role_id=validated_data["group_id"],
        )
