from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from model_bakery import baker

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


class StoreTypesModelTest(TestCase, TestDataMixin):
    """Testes para o modelo StoreTypes"""

    def test_store_type_creation(self):
        """Testa criação básica de tipo de loja"""
        store_type = self.create_store_type(name="Shopping Mall")

        self.assertEqual(store_type.name, "Shopping Mall")
        self.assertIsNotNone(store_type.created_at)
        self.assertIsNotNone(store_type.updated_at)
        self.assertFalse(store_type.is_deleted)

    def test_store_type_str_method(self):
        """Testa método __str__ do StoreTypes"""
        store_type = self.create_store_type(name="Hospital")
        self.assertEqual(str(store_type), "Hospital")

    def test_store_type_unique_name(self):
        """Testa constraint de nome único"""
        self.create_store_type(name="Unique Store")

        with self.assertRaises(IntegrityError):
            self.create_store_type(name="Unique Store")

    def test_store_type_soft_delete(self):
        """Testa soft delete functionality"""
        store_type = self.create_store_type()
        store_type_id = store_type.id

        # Soft delete
        store_type.soft_delete()

        # Verificar se foi marcado como deletado
        store_type.refresh_from_db()
        self.assertTrue(store_type.is_deleted)

        # Verificar se não aparece no queryset padrão
        self.assertFalse(StoreTypes.objects.filter(id=store_type_id).exists())


class EstablishmentsModelTest(TestCase, TestDataMixin):
    """Testes para o modelo Establishments"""

    def test_establishment_creation(self):
        """Testa criação básica de estabelecimento"""
        client = self.create_client()
        store_type = self.create_store_type()
        establishment = self.create_establishment(
            client=client,
            store_type=store_type,
            name="Test Mall",
            address="123 Main St",
            city="Test City",
            state="TS",
            lat=-23.5505,
            lng=-46.6333,
        )

        self.assertEqual(establishment.name, "Test Mall")
        self.assertEqual(establishment.client, client)
        self.assertEqual(establishment.store_type, store_type)
        self.assertEqual(establishment.address, "123 Main St")
        self.assertEqual(establishment.city, "Test City")
        self.assertEqual(establishment.state, "TS")
        self.assertEqual(establishment.lat, -23.5505)
        self.assertEqual(establishment.lng, -46.6333)

    def test_establishment_str_method(self):
        """Testa método __str__ do Establishments"""
        client = self.create_client(name="Test Client")
        establishment = self.create_establishment(
            client=client, name="Test Establishment"
        )
        expected = "Test Establishment (Test Client)"
        self.assertEqual(str(establishment), expected)

    def test_establishment_unique_constraint(self):
        """Testa constraint único por cliente e nome"""
        client = self.create_client()
        self.create_establishment(client=client, name="Unique Name")

        with self.assertRaises(IntegrityError):
            self.create_establishment(client=client, name="Unique Name")

    def test_establishment_different_clients_same_name(self):
        """Testa que clientes diferentes podem ter estabelecimentos com mesmo nome"""
        client1 = self.create_client()
        client2 = self.create_client()

        est1 = self.create_establishment(client=client1, name="Same Name")
        est2 = self.create_establishment(client=client2, name="Same Name")

        self.assertNotEqual(est1.id, est2.id)
        self.assertEqual(est1.name, est2.name)

    def test_establishment_optional_fields(self):
        """Testa campos opcionais"""
        client = self.create_client()
        establishment = baker.make(
            Establishments,
            client=client,
            name="Test Est",
            store_type=None,
            address=None,
            city=None,
            state=None,
            lat=None,
            lng=None,
        )

        self.assertIsNone(establishment.store_type)
        self.assertIsNone(establishment.address)
        self.assertIsNone(establishment.city)
        self.assertIsNone(establishment.state)
        self.assertIsNone(establishment.lat)
        self.assertIsNone(establishment.lng)


class LotsModelTest(TestCase, TestDataMixin):
    """Testes para o modelo Lots"""

    def test_lot_creation(self):
        """Testa criação básica de lote"""
        establishment = self.create_establishment()
        lot = self.create_lot(
            establishment=establishment, lot_code="LOT001", name="Main Lot"
        )

        self.assertEqual(lot.establishment, establishment)
        self.assertEqual(lot.client, establishment.client)
        self.assertEqual(lot.lot_code, "LOT001")
        self.assertEqual(lot.name, "Main Lot")

    def test_lot_str_method(self):
        """Testa método __str__ do Lots"""
        establishment = self.create_establishment(name="Test Est")
        lot = self.create_lot(establishment=establishment, lot_code="LOT123")
        expected = "LOT123 - Test Est"
        self.assertEqual(str(lot), expected)

    def test_lot_unique_constraint(self):
        """Testa constraint único por cliente e código"""
        client = self.create_client()
        self.create_lot(client=client, lot_code="UNIQUE001")

        with self.assertRaises(IntegrityError):
            self.create_lot(client=client, lot_code="UNIQUE001")

    def test_lot_different_clients_same_code(self):
        """Testa que clientes diferentes podem ter lotes com mesmo código"""
        client1 = self.create_client()
        client2 = self.create_client()

        lot1 = self.create_lot(client=client1, lot_code="SAME001")
        lot2 = self.create_lot(client=client2, lot_code="SAME001")

        self.assertNotEqual(lot1.id, lot2.id)
        self.assertEqual(lot1.lot_code, lot2.lot_code)


class SlotTypesModelTest(TestCase, TestDataMixin):
    """Testes para o modelo SlotTypes"""

    def test_slot_type_creation(self):
        """Testa criação básica de tipo de vaga"""
        slot_type = self.create_slot_type(name="Standard")

        self.assertEqual(slot_type.name, "Standard")
        self.assertIsNotNone(slot_type.created_at)
        self.assertFalse(slot_type.is_deleted)

    def test_slot_type_str_method(self):
        """Testa método __str__ do SlotTypes"""
        slot_type = self.create_slot_type(name="Premium")
        self.assertEqual(str(slot_type), "Premium")

    def test_slot_type_unique_name(self):
        """Testa constraint de nome único"""
        self.create_slot_type(name="VIP")

        with self.assertRaises(IntegrityError):
            self.create_slot_type(name="VIP")


class VehicleTypesModelTest(TestCase, TestDataMixin):
    """Testes para o modelo VehicleTypes"""

    def test_vehicle_type_creation(self):
        """Testa criação básica de tipo de veículo"""
        vehicle_type = self.create_vehicle_type(name="Car")

        self.assertEqual(vehicle_type.name, "Car")
        self.assertIsNotNone(vehicle_type.created_at)
        self.assertFalse(vehicle_type.is_deleted)

    def test_vehicle_type_str_method(self):
        """Testa método __str__ do VehicleTypes"""
        vehicle_type = self.create_vehicle_type(name="Motorcycle")
        self.assertEqual(str(vehicle_type), "Motorcycle")

    def test_vehicle_type_unique_name(self):
        """Testa constraint de nome único"""
        self.create_vehicle_type(name="Truck")

        with self.assertRaises(IntegrityError):
            self.create_vehicle_type(name="Truck")


class SlotsModelTest(TestCase, TestDataMixin):
    """Testes para o modelo Slots"""

    def test_slot_creation(self):
        """Testa criação básica de vaga"""
        lot = self.create_lot()
        slot_type = self.create_slot_type()
        polygon = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        }

        slot = self.create_slot(
            lot=lot,
            slot_type=slot_type,
            slot_code="A01",
            polygon_json=polygon,
            active=True,
        )

        self.assertEqual(slot.lot, lot)
        self.assertEqual(slot.client, lot.client)
        self.assertEqual(slot.slot_type, slot_type)
        self.assertEqual(slot.slot_code, "A01")
        self.assertEqual(slot.polygon_json, polygon)
        self.assertTrue(slot.active)

    def test_slot_str_method(self):
        """Testa método __str__ do Slots"""
        lot = self.create_lot(lot_code="LOT001")
        slot = self.create_slot(lot=lot, slot_code="A01")
        expected = "A01 - LOT001"
        self.assertEqual(str(slot), expected)

    def test_slot_unique_constraint(self):
        """Testa constraint único por lote e código"""
        lot = self.create_lot()
        self.create_slot(lot=lot, slot_code="A01")

        with self.assertRaises(IntegrityError):
            self.create_slot(lot=lot, slot_code="A01")

    def test_slot_different_lots_same_code(self):
        """Testa que lotes diferentes podem ter vagas com mesmo código"""
        lot1 = self.create_lot()
        lot2 = self.create_lot()

        slot1 = self.create_slot(lot=lot1, slot_code="A01")
        slot2 = self.create_slot(lot=lot2, slot_code="A01")

        self.assertNotEqual(slot1.id, slot2.id)
        self.assertEqual(slot1.slot_code, slot2.slot_code)

    def test_slot_default_active(self):
        """Testa valor padrão do campo active"""
        slot = baker.make(
            Slots,
            lot=self.create_lot(),
            slot_type=self.create_slot_type(),
            slot_code="TEST",
            polygon_json={},
        )
        self.assertTrue(slot.active)


class SlotStatusModelTest(TestCase, TestDataMixin):
    """Testes para o modelo SlotStatus"""

    def test_slot_status_creation(self):
        """Testa criação básica de status de vaga"""
        slot = self.create_slot()
        vehicle_type = self.create_vehicle_type()

        status = self.create_slot_status(
            slot=slot, status="OCCUPIED", vehicle_type=vehicle_type, confidence=0.950
        )

        self.assertEqual(status.slot, slot)
        self.assertEqual(status.status, "OCCUPIED")
        self.assertEqual(status.vehicle_type, vehicle_type)
        self.assertEqual(float(status.confidence), 0.950)
        self.assertIsNotNone(status.changed_at)

    def test_slot_status_str_method(self):
        """Testa método __str__ do SlotStatus"""
        slot = self.create_slot(slot_code="A01")
        status = self.create_slot_status(slot=slot, status="FREE")
        expected = "A01 - Livre"
        self.assertEqual(str(status), expected)

    def test_slot_status_choices(self):
        """Testa choices válidos para status"""
        valid_statuses = ["FREE", "OCCUPIED", "RESERVED", "MAINTENANCE", "DISABLED"]

        for status_choice in valid_statuses:
            slot = self.create_slot()  # Create different slot for each test
            status = self.create_slot_status(
                slot=slot, status=status_choice, confidence=None
            )
            status.full_clean()  # Valida o modelo
            self.assertEqual(status.status, status_choice)

    def test_slot_status_unique_constraint(self):
        """Testa constraint único por slot"""
        slot = self.create_slot()
        self.create_slot_status(slot=slot, status="FREE")

        with self.assertRaises(IntegrityError):
            self.create_slot_status(slot=slot, status="OCCUPIED")

    def test_slot_status_optional_fields(self):
        """Testa campos opcionais"""
        slot = self.create_slot()
        status = self.create_slot_status(
            slot=slot, status="FREE", vehicle_type=None, confidence=None
        )

        self.assertIsNone(status.vehicle_type)
        self.assertIsNone(status.confidence)


class SlotStatusHistoryModelTest(TestCase, TestDataMixin):
    """Testes para o modelo SlotStatusHistory"""

    def test_slot_status_history_creation(self):
        """Testa criação básica de histórico de status"""
        slot = self.create_slot()
        vehicle_type = self.create_vehicle_type()

        history = self.create_slot_status_history(
            slot=slot,
            status="OCCUPIED",
            vehicle_type=vehicle_type,
            confidence=0.880,
            event_id="123e4567-e89b-12d3-a456-426614174000",
        )

        self.assertEqual(history.slot, slot)
        self.assertEqual(history.status, "OCCUPIED")
        self.assertEqual(history.vehicle_type, vehicle_type)
        self.assertEqual(float(history.confidence), 0.880)
        self.assertIsNotNone(history.recorded_at)

    def test_slot_status_history_str_method(self):
        """Testa método __str__ do SlotStatusHistory"""
        slot = self.create_slot(slot_code="B02")
        history = self.create_slot_status_history(slot=slot, status="RESERVED")

        expected_start = "B02 - RESERVED ("
        self.assertTrue(str(history).startswith(expected_start))

    def test_slot_status_history_soft_delete(self):
        """Testa soft delete functionality"""
        history = self.create_slot_status_history()
        history_id = history.id

        # Soft delete
        history.soft_delete()

        # Verificar se foi marcado como deletado
        history.refresh_from_db()
        self.assertTrue(history.is_deleted)

        # Verificar se não aparece no queryset padrão
        self.assertFalse(SlotStatusHistory.objects.filter(id=history_id).exists())

    def test_slot_status_history_optional_fields(self):
        """Testa campos opcionais"""
        slot = self.create_slot()
        history = self.create_slot_status_history(
            slot=slot, status="FREE", vehicle_type=None, confidence=None, event_id=None
        )

        self.assertIsNone(history.vehicle_type)
        self.assertIsNone(history.confidence)
        self.assertIsNone(history.event_id)
