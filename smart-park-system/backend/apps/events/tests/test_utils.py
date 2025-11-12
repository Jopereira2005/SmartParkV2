from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta
from model_bakery import baker

from apps.tenants.models import Clients, ClientMembers
from apps.events.models import SlotStatusEvents


class TestDataMixin:
    """Mixin para criação de dados de teste"""

    def create_user(
        self, username="testuser", email="test@example.com", password="testpass"
    ):
        """Cria um usuário para testes"""
        return User.objects.create_user(
            username=username, email=email, password=password
        )

    def create_admin_user(self):
        """Cria um usuário admin para testes"""
        return User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )

    def create_group(self, name=None):
        """Cria um grupo para testes"""
        if name:
            group, created = Group.objects.get_or_create(name=name)
            return group
        return baker.make(Group, name=f"test_group_{baker.random_gen.gen_integer()}")

    def create_client(self, name="Test Client", onboarding_status="ACTIVE"):
        """Cria um cliente para testes"""
        return Clients.objects.create(name=name, onboarding_status=onboarding_status)

    def create_client_member(self, user, client, role=None):
        """Cria um membro de cliente para testes"""
        if not role:
            role = self.create_group()
        return ClientMembers.objects.create(user=user, client=client, role=role)

    def create_vehicle_type(self, name=None):
        """Cria um tipo de veículo para testes"""
        if name:
            # Tentar get_or_create para nomes específicos
            from apps.catalog.models import VehicleTypes

            vehicle_type, created = VehicleTypes.objects.get_or_create(name=name)
            return vehicle_type
        return baker.make("catalog.VehicleTypes")

    def create_establishment(self, name=None, client=None):
        """Cria um estabelecimento para testes"""
        if not client:
            client = self.create_client()

        # Use baker's random generation when name is None
        return baker.make(
            "catalog.Establishments", client=client, **({"name": name} if name else {})
        )

    def create_lot(self, lot_code="LOT001", establishment=None, client=None):
        """Cria um lote para testes"""
        if not establishment:
            establishment = self.create_establishment(client=client)
        return baker.make(
            "catalog.Lots",
            lot_code=lot_code,
            establishment=establishment,
            client=establishment.client,
        )

    def create_slot(self, slot_code="SLOT001", lot=None, client=None):
        """Cria uma vaga para testes"""
        if not lot:
            lot = self.create_lot(client=client)
        return baker.make(
            "catalog.Slots", slot_code=slot_code, lot=lot, client=lot.client
        )

    def create_camera(self, camera_code="CAM001", client=None):
        """Cria uma câmera para testes"""
        if not client:
            client = self.create_client()

        # Criar API key primeiro
        api_key = baker.make(
            "hardware.ApiKeys", client=client, name="Test API Key", enabled=True
        )

        return baker.make(
            "hardware.Cameras",
            camera_code=camera_code,
            client=client,
            api_key=api_key,
            state="ACTIVE",
        )

    def create_slot_status_event(
        self,
        event_type="STATUS_CHANGE",
        slot=None,
        client=None,
        curr_status="OCCUPIED",
        prev_status="FREE",
        occurred_at=None,
        **kwargs,
    ):
        """Cria um evento de status de slot para testes"""
        if not slot:
            slot = self.create_slot(client=client)

        if not occurred_at:
            occurred_at = timezone.now()

        lot = kwargs.pop("lot", slot.lot)

        return SlotStatusEvents.objects.create(
            event_type=event_type,
            slot=slot,
            lot=lot,
            client=slot.client,
            curr_status=curr_status,
            prev_status=prev_status,
            occurred_at=occurred_at,
            **kwargs,
        )
