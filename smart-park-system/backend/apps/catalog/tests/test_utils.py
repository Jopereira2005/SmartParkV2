from model_bakery import baker
from django.contrib.auth.models import User, Group
from apps.tenants.models import Clients
from apps.catalog.models import (
    StoreTypes,
    Establishments,
    Lots,
    SlotTypes,
    VehicleTypes,
    Slots,
    SlotStatus,
    SlotStatusHistory,
)


class TestDataMixin:
    """Mixin com métodos auxiliares para criar dados de teste"""

    @classmethod
    def create_user(cls, username=None, email=None, **kwargs):
        """Cria um usuário de teste"""
        data = {
            "username": username or f"user{baker.random_gen.gen_integer()}",
            "email": email or f"{username or 'user'}@example.com",
            "is_active": True,
            **kwargs,
        }
        return baker.make(User, **data)

    @classmethod
    def create_client(cls, name=None, **kwargs):
        """Cria um cliente de teste"""
        data = {
            "name": name or f"Client {baker.random_gen.gen_integer()}",
            "onboarding_status": "ACTIVE",
            **kwargs,
        }
        return baker.make(Clients, **data)

    @classmethod
    def create_store_type(cls, name=None, **kwargs):
        """Cria um tipo de loja de teste"""
        data = {
            "name": name or f"Store Type {baker.random_gen.gen_integer()}",
            **kwargs,
        }
        return baker.make(StoreTypes, **data)

    @classmethod
    def create_establishment(cls, client=None, store_type=None, name=None, **kwargs):
        """Cria um estabelecimento de teste"""
        data = {
            "client": client or cls.create_client(),
            "store_type": store_type or cls.create_store_type(),
            "name": name or f"Establishment {baker.random_gen.gen_integer()}",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            **kwargs,
        }
        return baker.make(Establishments, **data)

    @classmethod
    def create_lot(cls, establishment=None, client=None, lot_code=None, **kwargs):
        """Cria um lote de teste"""
        if not establishment:
            establishment = cls.create_establishment(client=client)

        data = {
            "establishment": establishment,
            "client": client or establishment.client,
            "lot_code": lot_code or f"LOT{baker.random_gen.gen_integer(1, 9999)}",
            "name": f"Lot {baker.random_gen.gen_integer(1, 9999)}",
            **kwargs,
        }
        return baker.make(Lots, **data)

    @classmethod
    def create_slot_type(cls, name=None, **kwargs):
        """Cria um tipo de vaga de teste"""
        data = {
            "name": name or f"Slot Type {baker.random_gen.gen_integer()}",
            **kwargs,
        }
        return baker.make(SlotTypes, **data)

    @classmethod
    def create_vehicle_type(cls, name=None, **kwargs):
        """Cria um tipo de veículo de teste"""
        data = {
            "name": name or f"Vehicle Type {baker.random_gen.gen_integer()}",
            **kwargs,
        }
        return baker.make(VehicleTypes, **data)

    @classmethod
    def create_slot(
        cls, lot=None, client=None, slot_type=None, slot_code=None, **kwargs
    ):
        """Cria uma vaga de teste"""
        if not lot:
            lot = cls.create_lot(client=client)

        data = {
            "lot": lot,
            "client": client or lot.client,
            "slot_type": slot_type or cls.create_slot_type(),
            "slot_code": slot_code or f"S{baker.random_gen.gen_integer(1, 999)}",
            "polygon_json": {"coordinates": [[0, 0], [1, 0], [1, 1], [0, 1]]},
            "active": True,
            **kwargs,
        }
        return baker.make(Slots, **data)

    @classmethod
    def create_slot_status(cls, slot=None, status="FREE", vehicle_type=None, **kwargs):
        """Cria um status de vaga de teste"""
        data = {
            "slot": slot or cls.create_slot(),
            "status": status,
            "vehicle_type": vehicle_type,
        }
        # Only set confidence if explicitly provided
        if "confidence" in kwargs:
            data["confidence"] = kwargs.pop("confidence")
        else:
            data["confidence"] = 0.950  # Default value

        data.update(kwargs)
        return baker.make(SlotStatus, **data)

    @classmethod
    def create_slot_status_history(
        cls, slot=None, status="FREE", vehicle_type=None, **kwargs
    ):
        """Cria um histórico de status de vaga de teste"""
        data = {
            "slot": slot or cls.create_slot(),
            "status": status,
            "vehicle_type": vehicle_type,
            "confidence": 0.950,  # DecimalField(max_digits=4, decimal_places=3)
            **kwargs,
        }
        return baker.make(SlotStatusHistory, **data)

    @classmethod
    def create_admin_user(cls):
        """Cria um usuário admin"""
        admin_group, _ = Group.objects.get_or_create(name="admin")
        user = cls.create_user()
        user.groups.add(admin_group)
        return user

    @classmethod
    def create_client_admin_user(cls):
        """Cria um usuário client_admin"""
        client_admin_group, _ = Group.objects.get_or_create(name="client_admin")
        user = cls.create_user()
        user.groups.add(client_admin_group)
        return user

    @classmethod
    def create_app_user(cls):
        """Cria um usuário app_user"""
        app_user_group, _ = Group.objects.get_or_create(name="app_user")
        user = cls.create_user()
        user.groups.add(app_user_group)
        return user


def create_test_groups():
    """Cria os grupos básicos necessários para os testes"""
    groups = ["admin", "client_admin", "app_user"]
    created_groups = []

    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        created_groups.append(group)

    return created_groups
