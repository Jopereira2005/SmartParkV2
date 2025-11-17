from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Clients, ClientMembers
from .serializers import (
    ClientSerializer,
    ClientCreateSerializer,
    ClientMemberSerializer,
    ClientMemberCreateSerializer,
)
from apps.core.permissions import IsAdminUser, IsClientAdminForClient
from apps.core.views import (
    BaseViewSetMixin,
    SoftDeleteViewSetMixin,
    SearchMixin,
    PaginationMixin,
)


@extend_schema_view(
    get=extend_schema(
        summary="List all clients",
        description="Retrieve a paginated list of all clients in the system",
        tags=["Tenants - Clients"],
    ),
    post=extend_schema(
        summary="Create new client",
        description="Create a new client in the system",
        tags=["Tenants - Clients"],
    ),
)
class ClientListCreateView(
    SoftDeleteViewSetMixin, SearchMixin, PaginationMixin, generics.ListCreateAPIView
):
    queryset = Clients.objects.all()
    permission_classes = [IsAdminUser]
    search_fields = ["name", "onboarding_status"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClientCreateSerializer
        return ClientSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Get client details",
        description="Retrieve details of a specific client",
        tags=["Tenants - Clients"],
    ),
    put=extend_schema(
        summary="Update client",
        description="Update client information",
        tags=["Tenants - Clients"],
    ),
    patch=extend_schema(
        summary="Partially update client",
        description="Partially update client information",
        tags=["Tenants - Clients"],
    ),
    delete=extend_schema(
        summary="Delete client",
        description="Soft delete a client",
        tags=["Tenants - Clients"],
    ),
)
class ClientDetailView(SoftDeleteViewSetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Clients.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminUser]


@extend_schema_view(
    get=extend_schema(
        summary="List client members",
        description="List all members of a specific client",
        tags=["Tenants - Client Members"],
    ),
    post=extend_schema(
        summary="Add client member",
        description="Add a new member to a client",
        tags=["Tenants - Client Members"],
    ),
)
class ClientMemberListView(
    BaseViewSetMixin, SearchMixin, PaginationMixin, generics.ListCreateAPIView
):
    serializer_class = ClientMemberSerializer
    permission_classes = [IsClientAdminForClient]
    search_fields = ["user__person__name", "user__person__email", "role__name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ClientMembers.objects.none()
        client_id = self.kwargs["client_id"]
        return ClientMembers.objects.filter(client_id=client_id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClientMemberCreateSerializer
        return ClientMemberSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["client_id"] = self.kwargs["client_id"]
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_member = serializer.save()

        # Retornar o objeto criado com serializer de leitura
        read_serializer = ClientMemberSerializer(client_member)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Get client member details",
        description="Retrieve details of a specific client member",
        tags=["Tenants - Client Members"],
    ),
    delete=extend_schema(
        summary="Remove client member",
        description="Remove a member from a client",
        tags=["Tenants - Client Members"],
    ),
)
class ClientMemberDetailView(BaseViewSetMixin, generics.RetrieveDestroyAPIView):
    serializer_class = ClientMemberSerializer
    permission_classes = [IsClientAdminForClient]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ClientMembers.objects.none()
        client_id = self.kwargs["client_id"]
        return ClientMembers.objects.filter(client_id=client_id)


@extend_schema(
    summary="Get my clients",
    description="Retrieve list of clients for the authenticated user",
    tags=["Tenants - Client Members"],
    responses={200: ClientMemberSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_clients_view(request):
    """Listar clientes do usuário logado"""
    user_clients = ClientMembers.objects.filter(user=request.user).select_related(
        "client", "role"
    )

    clients_data = []
    for membership in user_clients:
        clients_data.append(
            {
                "id": membership.client.id,
                "name": membership.client.name,
                "onboarding_status": membership.client.onboarding_status,
                "role": membership.role.name,
                "joined_at": membership.joined_at,
            }
        )

    return Response(clients_data)
