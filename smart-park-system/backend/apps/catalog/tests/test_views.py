from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone

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
from .test_utils import TestDataMixin

User = get_user_model()


class StoreTypeListViewTest(APITestCase, TestDataMixin):
    """Testes para StoreTypeListView"""

    def setUp(self):
        self.user = self.create_user()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("catalog:store-type-list")

    def test_list_store_types(self):
        """Testa listagem de tipos de loja"""
        store_type1 = self.create_store_type(name="Shopping Mall")
        store_type2 = self.create_store_type(name="Hospital")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIn("Shopping Mall", str(response.data))
        self.assertIn("Hospital", str(response.data))

    def test_search_store_types(self):
        """Testa busca por tipos de loja"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        self.create_store_type(name=f"STORE{unique_id}")
        self.create_store_type(name="Hospital Center ABC")

        response = self.client.get(self.url, {"search": f"STORE{unique_id}"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], f"STORE{unique_id}")

    def test_search_store_types_multiple_fields(self):
        """Testa busca por tipos de loja com múltiplos campos para cobrir linha 87"""
        # Create store types with different name patterns
        self.create_store_type(name="Shopping Mall Center")
        self.create_store_type(name="Hospital ABC")

        # Directly test the view with modified search_fields to trigger line 87
        from apps.catalog.views import StoreTypeListView
        from unittest.mock import patch

        # Patch the class-level search_fields to have multiple fields
        with patch.object(StoreTypeListView, "search_fields", ["name", "name"]):
            response = self.client.get(self.url, {"search": "mall"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 1)
            self.assertIn("Shopping Mall Center", str(response.data))

    def test_unauthenticated_access(self):
        """Testa acesso não autenticado"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EstablishmentViewsTest(APITestCase, TestDataMixin):
    """Testes para views de Establishments"""

    def setUp(self):
        self.client_obj = self.create_client()
        self.user = self.create_app_user()
        self.admin_user = self.create_client_admin_user()
        self.client.force_authenticate(user=self.user)

        # Mock client assignment
        role, _ = Group.objects.get_or_create(name="client_member")
        self.user.client_members.create(client=self.client_obj, role=role)
        self.admin_user.client_members.create(client=self.client_obj, role=role)

    def test_list_establishments(self):
        """Testa listagem de estabelecimentos"""
        establishment = self.create_establishment(
            client=self.client_obj, name="Test Mall"
        )
        url = reverse("catalog:establishment-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test Mall")

    def test_create_establishment(self):
        """Testa criação de estabelecimento"""
        store_type = self.create_store_type()
        url = reverse("catalog:establishment-list")

        data = {
            "client": self.client_obj.id,
            "name": "New Mall",
            "store_type_id": store_type.id,
            "address": "123 Street",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Mall")

    def test_search_establishments(self):
        """Testa busca por estabelecimentos"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        self.create_establishment(
            client=self.client_obj, name=f"EST{unique_id}", city="City Alpha"
        )
        self.create_establishment(
            client=self.client_obj, name="Mall Beta", city="City Beta"
        )
        url = reverse("catalog:establishment-list")

        response = self.client.get(url, {"search": f"EST{unique_id}"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_establishments_multiple_fields(self):
        """Testa busca em estabelecimentos com múltiplos campos para cobrir linha 82"""
        # EstablishmentListCreateView has multiple search_fields: ["name", "address", "city", "state"]
        # This should trigger the OR logic (line 82) when searching across multiple fields
        self.create_establishment(
            client=self.client_obj,
            name="Mall ABC",
            address="Street XYZ",
            city="City One",
            state="ST",
        )
        self.create_establishment(
            client=self.client_obj,
            name="Store DEF",
            address="Avenue GHI",
            city="City Two",
            state="OT",
        )
        url = reverse("catalog:establishment-list")

        # Search for "XYZ" which should match the address field of the first establishment
        # This tests the multiple field search logic (line 82: search_filters |= field_filter)
        response = self.client.get(url, {"search": "XYZ"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Mall ABC")

    def test_establishment_detail(self):
        """Testa detalhes de estabelecimento"""
        # Use admin user for detail view
        admin_role, _ = Group.objects.get_or_create(name="client_admin")
        admin_user = self.create_client_admin_user()
        admin_user.client_members.create(client=self.client_obj, role=admin_role)
        self.client.force_authenticate(user=admin_user)

        establishment = self.create_establishment(
            client=self.client_obj, name="Test Mall"
        )
        url = reverse("catalog:establishment-detail", kwargs={"pk": establishment.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Mall")

    def test_update_establishment_requires_admin(self):
        """Testa que atualização requer admin"""
        establishment = self.create_establishment(
            client=self.client_obj, name="Test Mall"
        )
        url = reverse("catalog:establishment-detail", kwargs={"pk": establishment.pk})

        data = {"name": "Updated Mall"}
        response = self.client.patch(url, data)

        # Should fail with regular user
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED],
        )

    def test_delete_establishment_requires_admin(self):
        """Testa que exclusão requer admin"""
        establishment = self.create_establishment(
            client=self.client_obj, name="Test Mall"
        )
        url = reverse("catalog:establishment-detail", kwargs={"pk": establishment.pk})

        response = self.client.delete(url)

        # Should fail with regular user
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED],
        )


class LotViewsTest(APITestCase, TestDataMixin):
    """Testes para views de Lots"""

    def setUp(self):
        self.client_obj = self.create_client()
        self.user = self.create_app_user()
        self.client.force_authenticate(user=self.user)

        # Mock client assignment
        role, _ = Group.objects.get_or_create(name="client_member")
        self.user.client_members.create(client=self.client_obj, role=role)

    def test_list_lots(self):
        """Testa listagem de lotes"""
        lot = self.create_lot(client=self.client_obj, lot_code="LOT001")
        url = reverse("catalog:lot-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["lot_code"], "LOT001")

    def test_create_lot(self):
        """Testa criação de lote"""
        establishment = self.create_establishment(client=self.client_obj)
        url = reverse("catalog:lot-list")

        data = {
            "client": self.client_obj.id,
            "establishment_id": establishment.id,
            "lot_code": "LOT002",
            "name": "Test Lot",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["lot_code"], "LOT002")

    def test_search_lots(self):
        """Testa busca por lotes"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        self.create_lot(
            client=self.client_obj, lot_code="LOT001", name=f"LOT{unique_id}"
        )
        self.create_lot(client=self.client_obj, lot_code="LOT002", name="Secondary Lot")
        url = reverse("catalog:lot-list")

        response = self.client.get(url, {"search": f"LOT{unique_id}"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_lot_detail(self):
        """Testa detalhes de lote"""
        # Use admin user for detail view
        admin_role, _ = Group.objects.get_or_create(name="client_admin")
        admin_user = self.create_client_admin_user()
        admin_user.client_members.create(client=self.client_obj, role=admin_role)
        self.client.force_authenticate(user=admin_user)

        lot = self.create_lot(client=self.client_obj, lot_code="LOT001")
        url = reverse("catalog:lot-detail", kwargs={"pk": lot.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lot_code"], "LOT001")


class SlotViewsTest(APITestCase, TestDataMixin):
    """Testes para views de Slots"""

    def setUp(self):
        self.client_obj = self.create_client()
        self.user = self.create_app_user()
        self.client.force_authenticate(user=self.user)
        self.lot = self.create_lot(client=self.client_obj)

        # Mock client assignment
        role, _ = Group.objects.get_or_create(name="client_member")
        self.user.client_members.create(client=self.client_obj, role=role)

    def test_list_slots_by_lot(self):
        """Testa listagem de vagas por lote"""
        slot = self.create_slot(lot=self.lot, slot_code="A01")
        url = reverse("catalog:slot-list", kwargs={"lot_id": self.lot.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["slot_code"], "A01")

    def test_create_slot_in_lot(self):
        """Testa criação de vaga em lote"""
        slot_type = self.create_slot_type()
        url = reverse("catalog:slot-list", kwargs={"lot_id": self.lot.id})

        data = {
            "client": self.client_obj.id,
            "lot_id": self.lot.id,
            "slot_code": "B02",
            "slot_type_id": slot_type.id,
            "polygon_json": {"coordinates": [[0, 0], [1, 1]]},
            "active": True,
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["slot_code"], "B02")

    def test_search_slots(self):
        """Testa busca por vagas"""
        import uuid

        unique_id = str(uuid.uuid4())[:6]  # Shorter for slot_code max length
        self.create_slot(lot=self.lot, slot_code=unique_id)
        self.create_slot(lot=self.lot, slot_code="OTH123")
        url = reverse("catalog:slot-list", kwargs={"lot_id": self.lot.id})

        response = self.client.get(url, {"search": unique_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_slots_no_results(self):
        """Test searching slots with no matching results to trigger empty search_filters condition"""
        url = reverse("catalog:slot-list", kwargs={"lot_id": self.lot.id})
        response = self.client.get(url, {"search": "NONEXISTENT999"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    def test_slot_detail(self):
        """Testa detalhes de vaga"""
        # Use admin user for detail view
        admin_role, _ = Group.objects.get_or_create(name="client_admin")
        admin_user = self.create_client_admin_user()
        admin_user.client_members.create(client=self.client_obj, role=admin_role)
        self.client.force_authenticate(user=admin_user)

        slot = self.create_slot(lot=self.lot, slot_code="A01")
        url = reverse("catalog:slot-detail", kwargs={"pk": slot.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["slot_code"], "A01")


class SlotTypeListViewTest(APITestCase, TestDataMixin):
    """Testes para SlotTypeListView"""

    def setUp(self):
        self.user = self.create_user()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("catalog:slot-type-list")

    def test_list_slot_types(self):
        """Testa listagem de tipos de vaga"""
        slot_type1 = self.create_slot_type(name="Standard")
        slot_type2 = self.create_slot_type(name="Premium")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_search_slot_types(self):
        """Testa busca por tipos de vaga"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        self.create_slot_type(name=f"SLOT{unique_id}")
        self.create_slot_type(name="Premium VIP")

        response = self.client.get(self.url, {"search": f"SLOT{unique_id}"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class VehicleTypeListViewTest(APITestCase, TestDataMixin):
    """Testes para VehicleTypeListView"""

    def setUp(self):
        self.user = self.create_user()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("catalog:vehicle-type-list")

    def test_list_vehicle_types(self):
        """Testa listagem de tipos de veículo"""
        vehicle_type1 = self.create_vehicle_type(name="Car")
        vehicle_type2 = self.create_vehicle_type(name="Motorcycle")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_search_vehicle_types(self):
        """Testa busca por tipos de veículo"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        self.create_vehicle_type(name=f"VEH{unique_id}")
        self.create_vehicle_type(name="Motorcycle")

        response = self.client.get(self.url, {"search": f"VEH{unique_id}"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class SlotStatusViewsTest(APITestCase, TestDataMixin):
    """Testes para views de SlotStatus"""

    def setUp(self):
        self.client_obj = self.create_client()
        self.user = self.create_app_user()
        self.client.force_authenticate(user=self.user)
        self.slot = self.create_slot(client=self.client_obj)
        self.slot_status = self.create_slot_status(slot=self.slot, status="FREE")

        # Mock client assignment
        role, _ = Group.objects.get_or_create(name="client_member")
        self.user.client_members.create(client=self.client_obj, role=role)

    def test_get_slot_status(self):
        """Testa obtenção de status da vaga"""
        url = reverse("catalog:slot-status-detail", kwargs={"pk": self.slot_status.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "FREE")

    def test_update_slot_status(self):
        """Testa atualização de status da vaga"""
        vehicle_type = self.create_vehicle_type()
        url = reverse("catalog:slot-status-detail", kwargs={"pk": self.slot_status.pk})

        data = {
            "status": "OCCUPIED",
            "vehicle_type_id": vehicle_type.id,
            "confidence": "0.950",
        }

        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "OCCUPIED")

        # Verificar se histórico foi criado
        history_count = SlotStatusHistory.objects.filter(slot=self.slot).count()
        self.assertGreater(history_count, 0)

    def test_update_slot_status_invalid_vehicle_type(self):
        """Testa atualização com tipo de veículo inválido"""
        url = reverse("catalog:slot-status-detail", kwargs={"pk": self.slot_status.pk})

        data = {"status": "OCCUPIED", "vehicle_type_id": 99999}  # ID inexistente

        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_slot_status_invalid_status(self):
        """Testa atualização com status inválido"""
        url = reverse("catalog:slot-status-detail", kwargs={"pk": self.slot_status.pk})

        data = {"status": "INVALID_STATUS"}

        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_slot_status_with_null_vehicle_type(self):
        """Testa atualização de status com vehicle_type_id como None para cobrir linha 326"""
        url = reverse("catalog:slot-status-detail", kwargs={"pk": self.slot_status.pk})

        data = {
            "status": "FREE",
            "vehicle_type_id": None,  # This should trigger line 326: slot_status.vehicle_type = None
            "confidence": "0.800",
        }

        response = self.client.put(
            url, data, format="json"
        )  # Use JSON format to allow None

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "FREE")

        # Refresh from database to check vehicle_type is None
        self.slot_status.refresh_from_db()
        self.assertIsNone(self.slot_status.vehicle_type)

    def test_update_slot_status_with_confidence(self):
        """Test updating slot status with confidence field to cover line 326"""
        # Create vehicle type for the test
        vehicle_type = self.create_vehicle_type()

        url = reverse("catalog:slot-status-detail", kwargs={"pk": self.slot_status.pk})

        data = {
            "status": "OCCUPIED",
            "vehicle_type_id": vehicle_type.id,
            "confidence": 0.95,
        }

        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify confidence was saved
        self.slot_status.refresh_from_db()
        self.assertEqual(float(self.slot_status.confidence), 0.95)


class SlotStatusHistoryViewTest(APITestCase, TestDataMixin):
    """Testes para SlotStatusHistoryListView"""

    def setUp(self):
        self.client_obj = self.create_client()
        self.user = self.create_app_user()
        self.client.force_authenticate(user=self.user)
        self.slot = self.create_slot(client=self.client_obj)

        # Mock client assignment
        role, _ = Group.objects.get_or_create(name="client_member")
        self.user.client_members.create(client=self.client_obj, role=role)

    def test_list_slot_status_history(self):
        """Testa listagem de histórico de status"""
        history1 = self.create_slot_status_history(slot=self.slot, status="FREE")
        history2 = self.create_slot_status_history(slot=self.slot, status="OCCUPIED")
        url = reverse("catalog:slot-status-history", kwargs={"slot_id": self.slot.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_search_slot_status_history(self):
        """Testa busca no histórico de status"""
        self.create_slot_status_history(slot=self.slot, status="FREE")
        self.create_slot_status_history(slot=self.slot, status="OCCUPIED")

        url = reverse("catalog:slot-status-history", kwargs={"slot_id": self.slot.id})

        response = self.client.get(url, {"search": "OCCUPIED"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class PublicAPIViewsTest(APITestCase, TestDataMixin):
    """Testes para endpoints públicos"""

    def setUp(self):
        # Public endpoints don't require authentication
        pass

    def test_public_establishments_list(self):
        """Testa listagem pública de estabelecimentos"""
        client_obj = self.create_client(onboarding_status="ACTIVE")
        establishment = self.create_establishment(
            client=client_obj,
            name="Public Mall",
            address="123 Public St",
            city="Public City",
        )

        url = reverse("catalog:public-establishments")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Public Mall")

    def test_public_establishments_only_active_clients(self):
        """Testa que apenas clientes ativos aparecem na listagem pública"""
        active_client = self.create_client(onboarding_status="ACTIVE")
        inactive_client = self.create_client(onboarding_status="PENDING")

        self.create_establishment(client=active_client, name="Active Mall")
        self.create_establishment(client=inactive_client, name="Inactive Mall")

        url = reverse("catalog:public-establishments")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Active Mall")

    def test_public_slot_status(self):
        """Testa endpoint público de status das vagas"""
        client_obj = self.create_client()
        establishment = self.create_establishment(client=client_obj)
        lot = self.create_lot(establishment=establishment, lot_code="LOT001")
        slot = self.create_slot(lot=lot, slot_code="A01", active=True)

        url = reverse(
            "catalog:public-slot-status", kwargs={"establishment_id": establishment.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slot_code"], "A01")
        self.assertEqual(response.data[0]["lot_code"], "LOT001")

    def test_public_slot_status_only_active_slots(self):
        """Testa que apenas vagas ativas aparecem no endpoint público"""
        client_obj = self.create_client()
        establishment = self.create_establishment(client=client_obj)
        lot = self.create_lot(establishment=establishment)

        active_slot = self.create_slot(lot=lot, slot_code="A01", active=True)
        inactive_slot = self.create_slot(lot=lot, slot_code="A02", active=False)

        url = reverse(
            "catalog:public-slot-status", kwargs={"establishment_id": establishment.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slot_code"], "A01")

    def test_public_slot_status_nonexistent_establishment(self):
        """Testa endpoint público com estabelecimento inexistente"""
        url = reverse("catalog:public-slot-status", kwargs={"establishment_id": 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_slot_status_no_current_status(self):
        """Test slot with no current status to cover line 467 in views.py"""
        client_obj = self.create_client(onboarding_status="ACTIVE")
        establishment = self.create_establishment(client=client_obj)
        lot = self.create_lot(establishment=establishment)

        # Create a slot but don't create any status for it
        slot = self.create_slot(lot=lot, slot_code="NO_STATUS")

        url = reverse(
            "catalog:public-slot-status", kwargs={"establishment_id": establishment.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find our slot in the response (response.data is a list, not a dict)
        slot_data = None
        for slot_info in response.data:
            if slot_info["slot_code"] == "NO_STATUS":
                slot_data = slot_info
                break

        self.assertIsNotNone(slot_data)
        self.assertIsNone(slot_data["status"])  # Should be None when no status exists

    def test_public_slot_status_with_vehicle_type(self):
        """Test slot status with vehicle_type to cover line 467 (status_obj.vehicle_type.name)"""
        client_obj = self.create_client(onboarding_status="ACTIVE")
        establishment = self.create_establishment(client=client_obj)
        lot = self.create_lot(establishment=establishment)
        slot = self.create_slot(
            lot=lot, slot_code="WITHVEH"
        )  # Shortened to fit varchar(10)

        # Create a vehicle type and slot status with it
        vehicle_type = self.create_vehicle_type(name="Car")
        self.create_slot_status(
            slot=slot, status="OCCUPIED", vehicle_type=vehicle_type, confidence=0.95
        )

        url = reverse(
            "catalog:public-slot-status", kwargs={"establishment_id": establishment.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find our slot in the response
        slot_data = None
        for slot_info in response.data:
            if slot_info["slot_code"] == "WITHVEH":
                slot_data = slot_info
                break

        self.assertIsNotNone(slot_data)
        self.assertIsNotNone(slot_data["status"])
        self.assertEqual(
            slot_data["status"]["vehicle_type"], "Car"
        )  # This tests line 467
        self.assertEqual(slot_data["status"]["status"], "OCCUPIED")
