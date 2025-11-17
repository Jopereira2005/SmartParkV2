from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.catalog.models import Slots, SlotStatus, SlotStatusHistory
from .serializers import (
    ApiKeySerializer,
    ApiKeyCreateSerializer,
    CameraSerializer,
    CameraCreateSerializer,
    CameraHeartbeatSerializer,
    CameraHeartbeatCreateSerializer,
    SlotStatusEventSerializer,
)
from apps.core.permissions import IsClientAdminForClient, IsClientMember
from apps.core.views import (
    TenantViewSetMixin,
    SearchMixin,
    PaginationMixin,
    FilterByClientMixin,
)


@extend_schema_view(
    get=extend_schema(
        summary="List API keys",
        description="Retrieve paginated list of API keys for client",
        tags=["Hardware - API Keys"],
    ),
    post=extend_schema(
        summary="Create API key",
        description="Create a new API key for client",
        tags=["Hardware - API Keys"],
    ),
)
class ApiKeyListCreateView(
    TenantViewSetMixin, SearchMixin, PaginationMixin, generics.ListCreateAPIView
):
    serializer_class = ApiKeySerializer
    permission_classes = [IsClientMember]
    search_fields = ["name", "key_id"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ApiKeyCreateSerializer
        return ApiKeySerializer


@extend_schema_view(
    get=extend_schema(
        summary="Get API key details",
        description="Retrieve details of a specific API key",
        tags=["Hardware - API Keys"],
    ),
    put=extend_schema(
        summary="Update API key",
        description="Update API key information",
        tags=["Hardware - API Keys"],
    ),
    patch=extend_schema(
        summary="Partially update API key",
        description="Partially update API key information",
        tags=["Hardware - API Keys"],
    ),
    delete=extend_schema(
        summary="Delete API key",
        description="Delete an API key",
        tags=["Hardware - API Keys"],
    ),
)
class ApiKeyDetailView(TenantViewSetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ApiKeySerializer
    permission_classes = [IsClientAdminForClient]


@extend_schema_view(
    get=extend_schema(
        summary="List cameras",
        description="Retrieve paginated list of cameras for client",
        tags=["Hardware - Cameras"],
    ),
    post=extend_schema(
        summary="Create camera",
        description="Create a new camera for client",
        tags=["Hardware - Cameras"],
    ),
)
class CameraListCreateView(
    TenantViewSetMixin, SearchMixin, PaginationMixin, generics.ListCreateAPIView
):
    serializer_class = CameraSerializer
    permission_classes = [IsClientMember]
    search_fields = ["camera_code", "state"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CameraCreateSerializer
        return CameraSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Get camera details",
        description="Retrieve details of a specific camera",
        tags=["Hardware - Cameras"],
    ),
    put=extend_schema(
        summary="Update camera",
        description="Update camera information",
        tags=["Hardware - Cameras"],
    ),
    patch=extend_schema(
        summary="Partially update camera",
        description="Partially update camera information",
        tags=["Hardware - Cameras"],
    ),
    delete=extend_schema(
        summary="Delete camera",
        description="Delete a camera",
        tags=["Hardware - Cameras"],
    ),
)
class CameraDetailView(TenantViewSetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CameraSerializer
    permission_classes = [IsClientAdminForClient]


@extend_schema(
    summary="Create camera heartbeat",
    description="Record a heartbeat from camera hardware",
    tags=["Hardware - Camera Monitoring"],
)
class CameraHeartbeatCreateView(generics.CreateAPIView):
    serializer_class = CameraHeartbeatCreateSerializer
    permission_classes = [permissions.AllowAny]  # Hardware pode enviar heartbeats

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        heartbeat = serializer.save()

        # Retornar com serializer de leitura
        read_serializer = CameraHeartbeatSerializer(heartbeat)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="List camera heartbeats",
    description="Retrieve paginated list of heartbeats for a specific camera",
    tags=["Hardware - Camera Monitoring"],
)
class CameraHeartbeatListView(
    FilterByClientMixin, SearchMixin, PaginationMixin, generics.ListAPIView
):
    serializer_class = CameraHeartbeatSerializer
    permission_classes = [IsClientMember]
    search_fields = ["payload_json"]

    def get_queryset(self):
        from .models import CameraHeartbeats

        if getattr(self, "swagger_fake_view", False):
            return CameraHeartbeats.objects.none()
        camera_id = self.kwargs["camera_id"]
        return CameraHeartbeats.objects.filter(camera_id=camera_id).order_by(
            "-received_at"
        )


@extend_schema(
    summary="Receive slot status event from hardware",
    description="Endpoint for hardware to report slot status changes",
    tags=["Hardware - Integration"],
    request=SlotStatusEventSerializer,
    responses={
        200: {"description": "Event processed successfully"},
        400: {"description": "Bad request - missing required fields"},
    },
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def slot_status_event_view(request):
    """Endpoint para receber eventos de status de vagas do hardware"""
    # TODO: Implementar validação de API Key e HMAC
    # Por enquanto, aceitar qualquer requisição

    serializer = SlotStatusEventSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        validated_data = serializer.validated_data
        slot_id = validated_data["slot_id"]
        slot_status_value = validated_data["status"]
        vehicle_type_id = validated_data.get("vehicle_type_id")
        confidence = validated_data.get("confidence")

        # Buscar a vaga
        slot = get_object_or_404(Slots, id=slot_id)

        # Atualizar ou criar status
        slot_status, created = SlotStatus.objects.get_or_create(
            slot=slot,
            defaults={
                "status": slot_status_value,
                "vehicle_type_id": vehicle_type_id,
                "confidence": confidence,
            },
        )

        if not created:
            # Atualizar status existente
            slot_status.status = slot_status_value
            slot_status.vehicle_type_id = vehicle_type_id
            slot_status.confidence = confidence
            slot_status.changed_at = timezone.now()
            slot_status.save()

        # Criar entrada no histórico
        SlotStatusHistory.objects.create(
            slot=slot,
            status=slot_status_value,
            vehicle_type_id=vehicle_type_id,
            confidence=confidence,
        )

        return Response(
            {
                "message": "Status atualizado com sucesso",
                "slot_id": slot_id,
                "status": slot_status_value,
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
