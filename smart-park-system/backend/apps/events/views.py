from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from .serializers import SlotStatusEventSerializer, SlotStatusEventCreateSerializer
from apps.core.permissions import IsClientMember
from apps.core.views import TenantViewSetMixin, SearchMixin, PaginationMixin


@extend_schema_view(
    get=extend_schema(
        summary="List slot status events",
        description="Retrieve paginated list of slot status change events",
        tags=["Events - System Events"],
    ),
    post=extend_schema(
        summary="Create slot status event",
        description="Record a new slot status change event",
        tags=["Events - System Events"],
    ),
)
class SlotStatusEventListCreateView(
    TenantViewSetMixin, SearchMixin, PaginationMixin, generics.ListCreateAPIView
):
    serializer_class = SlotStatusEventSerializer
    permission_classes = [IsClientMember]
    search_fields = ["event_type", "slot__slot_code", "lot__lot_code"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SlotStatusEventCreateSerializer
        return SlotStatusEventSerializer


@extend_schema(
    summary="Get slot status event details",
    description="Retrieve details of a specific slot status event",
    tags=["Events - System Events"],
)
class SlotStatusEventDetailView(TenantViewSetMixin, generics.RetrieveAPIView):
    serializer_class = SlotStatusEventSerializer
    permission_classes = [IsClientMember]
