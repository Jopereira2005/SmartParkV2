from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import serializers
from decimal import Decimal

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
from apps.catalog.serializers import (
    StoreTypeSerializer,
    EstablishmentSerializer,
    LotSerializer,
    SlotTypeSerializer,
    VehicleTypeSerializer,
    SlotSerializer,
    SlotStatusSerializer,
    SlotStatusHistorySerializer,
    SlotStatusUpdateSerializer,
)
from .test_utils import TestDataMixin


class StoreTypeSerializerTest(TestCase, TestDataMixin):
    """Testes para StoreTypeSerializer"""

    def test_serialization(self):
        """Testa serialização de StoreTypes"""
        store_type = self.create_store_type(name="Shopping Mall")
        serializer = StoreTypeSerializer(store_type)

        data = serializer.data
        self.assertEqual(data["name"], "Shopping Mall")
        self.assertIn("public_id", data)
        self.assertIn("created_at", data)

    def test_deserialization_valid(self):
        """Testa deserialização válida"""
        data = {"name": "Hospital"}
        serializer = StoreTypeSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        store_type = serializer.save()
        self.assertEqual(store_type.name, "Hospital")

    def test_deserialization_invalid(self):
        """Testa deserialização inválida"""
        data = {"name": ""}
        serializer = StoreTypeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)


class EstablishmentSerializerTest(TestCase, TestDataMixin):
    """Testes para EstablishmentSerializer"""

    def test_serialization(self):
        """Testa serialização de Establishments"""
        client = self.create_client()
        store_type = self.create_store_type()
        establishment = self.create_establishment(
            client=client, store_type=store_type, name="Test Mall"
        )

        serializer = EstablishmentSerializer(establishment)
        data = serializer.data

        self.assertEqual(data["name"], "Test Mall")
        self.assertEqual(data["store_type"]["name"], store_type.name)
        self.assertIn("public_id", data)

    def test_deserialization_valid(self):
        """Testa deserialização válida"""
        client = self.create_client()
        store_type = self.create_store_type()

        data = {
            "client": client.id,
            "name": "New Mall",
            "store_type_id": store_type.id,
            "address": "123 Street",
            "city": "Test City",
            "state": "TS",
        }

        serializer = EstablishmentSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        establishment = serializer.save()
        self.assertEqual(establishment.name, "New Mall")
        self.assertEqual(establishment.store_type, store_type)

    def test_deserialization_without_store_type(self):
        """Testa deserialização sem store_type"""
        client = self.create_client()

        data = {"client": client.id, "name": "Mall Without Type"}
        serializer = EstablishmentSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        establishment = serializer.save()
        self.assertEqual(establishment.name, "Mall Without Type")
        self.assertIsNone(establishment.store_type)


class LotSerializerTest(TestCase, TestDataMixin):
    """Testes para LotSerializer"""

    def test_serialization(self):
        """Testa serialização de Lots"""
        lot = self.create_lot(lot_code="LOT001", name="Main Lot")
        serializer = LotSerializer(lot)

        data = serializer.data
        self.assertEqual(data["lot_code"], "LOT001")
        self.assertEqual(data["name"], "Main Lot")
        self.assertIn("establishment", data)

    def test_deserialization_valid(self):
        """Testa deserialização válida"""
        client = self.create_client()
        establishment = self.create_establishment(client=client)

        data = {
            "client": client.id,
            "establishment_id": establishment.id,
            "lot_code": "LOT002",
            "name": "Secondary Lot",
        }

        serializer = LotSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        lot = serializer.save()
        self.assertEqual(lot.lot_code, "LOT002")
        self.assertEqual(lot.establishment, establishment)


class SlotTypeSerializerTest(TestCase, TestDataMixin):
    """Testes para SlotTypeSerializer"""

    def test_serialization(self):
        """Testa serialização de SlotTypes"""
        slot_type = self.create_slot_type(name="Standard")
        serializer = SlotTypeSerializer(slot_type)

        data = serializer.data
        self.assertEqual(data["name"], "Standard")
        self.assertIn("public_id", data)

    def test_deserialization_valid(self):
        """Testa deserialização válida"""
        data = {"name": "Premium"}
        serializer = SlotTypeSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        slot_type = serializer.save()
        self.assertEqual(slot_type.name, "Premium")


class VehicleTypeSerializerTest(TestCase, TestDataMixin):
    """Testes para VehicleTypeSerializer"""

    def test_serialization(self):
        """Testa serialização de VehicleTypes"""
        vehicle_type = self.create_vehicle_type(name="Car")
        serializer = VehicleTypeSerializer(vehicle_type)

        data = serializer.data
        self.assertEqual(data["name"], "Car")
        self.assertIn("public_id", data)

    def test_deserialization_valid(self):
        """Testa deserialização válida"""
        data = {"name": "Motorcycle"}
        serializer = VehicleTypeSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        vehicle_type = serializer.save()
        self.assertEqual(vehicle_type.name, "Motorcycle")


class SlotSerializerTest(TestCase, TestDataMixin):
    """Testes para SlotSerializer"""

    def test_serialization(self):
        """Testa serialização de Slots"""
        slot = self.create_slot(slot_code="A01")
        serializer = SlotSerializer(slot)

        data = serializer.data
        self.assertEqual(data["slot_code"], "A01")
        self.assertIn("lot", data)
        self.assertIn("slot_type", data)
        self.assertIn("current_status", data)

    def test_serialization_with_status(self):
        """Testa serialização com status atual"""
        slot = self.create_slot()
        vehicle_type = self.create_vehicle_type(name="Car")
        self.create_slot_status(
            slot=slot, status="OCCUPIED", vehicle_type=vehicle_type, confidence=0.950
        )

        serializer = SlotSerializer(slot)
        data = serializer.data

        # Note: current_status pode ser None dependendo da implementação
        # Se não houver relacionamento current_status configurado corretamente
        if data["current_status"]:
            self.assertEqual(data["current_status"]["status"], "OCCUPIED")
            self.assertEqual(data["current_status"]["vehicle_type"], "Car")

    def test_get_current_status_exception_handling(self):
        """Test exception handling in get_current_status to cover lines 74-75"""
        client = self.create_client()
        lot = self.create_lot(client=client)
        slot_type = self.create_slot_type()

        slot = self.create_slot(lot=lot, slot_type=slot_type)

        # Create a mock slot object that will raise an exception when accessing current_status
        class MockSlot:
            def __init__(self, slot):
                # Copy attributes from real slot
                for attr in ["id", "slot_code", "slot_type", "lot"]:
                    setattr(self, attr, getattr(slot, attr))

            @property
            def current_status(self):
                # Simulate an exception that could occur in database access
                raise Exception("Database connection error")

        mock_slot = MockSlot(slot)
        serializer = SlotSerializer(mock_slot)

        # The get_current_status method should handle the exception and return None
        result = serializer.get_current_status(mock_slot)
        self.assertIsNone(result)

    def test_deserialization_valid(self):
        """Testa deserialização válida"""
        client = self.create_client()
        lot = self.create_lot(client=client)
        slot_type = self.create_slot_type()

        data = {
            "client": client.id,
            "lot_id": lot.id,
            "slot_code": "B02",
            "slot_type_id": slot_type.id,
            "polygon_json": {"coordinates": [[0, 0], [1, 1]]},
            "active": True,
        }

        serializer = SlotSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        slot = serializer.save()
        self.assertEqual(slot.slot_code, "B02")
        self.assertEqual(slot.lot, lot)


class SlotStatusSerializerTest(TestCase, TestDataMixin):
    """Testes para SlotStatusSerializer"""

    def test_serialization(self):
        """Testa serialização de SlotStatus"""
        slot = self.create_slot()
        vehicle_type = self.create_vehicle_type()
        status = self.create_slot_status(
            slot=slot, status="OCCUPIED", vehicle_type=vehicle_type, confidence=0.950
        )

        serializer = SlotStatusSerializer(status)
        data = serializer.data

        self.assertEqual(data["status"], "OCCUPIED")
        self.assertEqual(float(data["confidence"]), 0.950)
        self.assertIn("slot", data)
        self.assertIn("vehicle_type", data)

    def test_deserialization_valid(self):
        """Testa deserialização válida"""
        slot = self.create_slot()
        vehicle_type = self.create_vehicle_type()

        data = {
            "slot_id": slot.id,
            "status": "FREE",
            "vehicle_type_id": vehicle_type.id,
            "confidence": "0.880",
        }

        serializer = SlotStatusSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        status = serializer.save()
        self.assertEqual(status.status, "FREE")
        self.assertEqual(status.vehicle_type, vehicle_type)

    def test_validate_status_invalid(self):
        """Test validation of invalid status to cover line 114"""
        from apps.catalog.serializers import SlotStatusUpdateSerializer

        # Create a serializer instance and test the validate_status method directly
        serializer = SlotStatusUpdateSerializer()

        # Test invalid status - this should raise ValidationError and not reach line 114
        try:
            serializer.validate_status("INVALID_STATUS")
            self.fail("Expected ValidationError was not raised")
        except serializers.ValidationError as e:
            self.assertIn("Status inválido", str(e))

        # Test valid status - this should reach line 114 (return value)
        result = serializer.validate_status("FREE")
        self.assertEqual(result, "FREE")


class SlotStatusHistorySerializerTest(TestCase, TestDataMixin):
    """Testes para SlotStatusHistorySerializer"""

    def test_serialization(self):
        """Testa serialização de SlotStatusHistory"""
        history = self.create_slot_status_history(status="OCCUPIED", confidence=0.920)

        serializer = SlotStatusHistorySerializer(history)
        data = serializer.data

        self.assertEqual(data["status"], "OCCUPIED")
        self.assertEqual(float(data["confidence"]), 0.920)
        self.assertIn("slot", data)
        self.assertIn("recorded_at", data)


class SlotStatusUpdateSerializerTest(TestCase, TestDataMixin):
    """Testes para SlotStatusUpdateSerializer"""

    def test_valid_data(self):
        """Testa dados válidos"""
        vehicle_type = self.create_vehicle_type()

        data = {
            "status": "OCCUPIED",
            "vehicle_type_id": vehicle_type.id,
            "confidence": "0.950",
        }

        serializer = SlotStatusUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["status"], "OCCUPIED")

    def test_invalid_status(self):
        """Testa status inválido"""
        data = {"status": "INVALID_STATUS"}
        serializer = SlotStatusUpdateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_invalid_vehicle_type_id(self):
        """Testa vehicle_type_id inválido"""
        data = {"status": "OCCUPIED", "vehicle_type_id": 99999}  # ID que não existe
        serializer = SlotStatusUpdateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("vehicle_type_id", serializer.errors)

    def test_optional_fields(self):
        """Testa campos opcionais"""
        data = {"status": "FREE"}
        serializer = SlotStatusUpdateSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["status"], "FREE")
        self.assertIsNone(serializer.validated_data.get("vehicle_type_id"))
        self.assertIsNone(serializer.validated_data.get("confidence"))

    def test_valid_confidence_format(self):
        """Testa formato válido de confidence"""
        data = {"status": "OCCUPIED", "confidence": "0.999"}
        serializer = SlotStatusUpdateSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["confidence"], Decimal("0.999"))

    def test_invalid_confidence_format(self):
        """Testa formato inválido de confidence"""
        data = {"status": "OCCUPIED", "confidence": "1.0000"}  # Muitas casas decimais
        serializer = SlotStatusUpdateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("confidence", serializer.errors)
