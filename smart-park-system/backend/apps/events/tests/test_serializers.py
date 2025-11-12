from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.events.models import SlotStatusEvents
from apps.events.serializers import (
    SlotStatusEventSerializer,
    SlotStatusEventCreateSerializer,
)
from .test_utils import TestDataMixin


class SlotStatusEventSerializerTest(TestCase, TestDataMixin):
    """Testes para SlotStatusEventSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_obj = self.create_client()
        self.slot = self.create_slot(client=self.client_obj)
        self.camera = self.create_camera(client=self.client_obj)
        self.vehicle_type = self.create_vehicle_type("Car")

        self.event = self.create_slot_status_event(
            slot=self.slot,
            camera=self.camera,
            prev_vehicle=self.vehicle_type,
            curr_vehicle=self.vehicle_type,
            confidence=0.95,
            source_model="YOLOv8",
            source_version="1.0.0",
        )

    def test_serialization(self):
        """Testa serialização do evento"""
        serializer = SlotStatusEventSerializer(self.event)
        data = serializer.data

        # Verificar campos básicos
        self.assertEqual(data["event_type"], self.event.event_type)
        self.assertEqual(data["curr_status"], self.event.curr_status)
        self.assertEqual(data["prev_status"], self.event.prev_status)
        self.assertEqual(float(data["confidence"]), float(self.event.confidence))
        self.assertEqual(data["source_model"], self.event.source_model)
        self.assertEqual(data["source_version"], self.event.source_version)

        # Verificar campos relacionados
        self.assertEqual(data["slot"], self.event.slot.id)
        self.assertEqual(data["lot"], self.event.lot.id)
        self.assertEqual(data["camera"], self.event.camera.id)
        self.assertEqual(data["prev_vehicle"], self.event.prev_vehicle.id)
        self.assertEqual(data["curr_vehicle"], self.event.curr_vehicle.id)

        # Verificar campos herdados
        self.assertEqual(data["client"], self.event.client.id)
        self.assertEqual(data["client_name"], self.event.client.name)
        self.assertIn("public_id", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertIn("is_deleted", data)

    def test_serializer_fields(self):
        """Testa que todos os campos esperados estão presentes"""
        serializer = SlotStatusEventSerializer(self.event)
        expected_fields = {
            "id",
            "public_id",
            "created_at",
            "updated_at",
            "is_deleted",
            "client",
            "client_name",
            "event_id",
            "event_type",
            "occurred_at",
            "lot",
            "camera",
            "sequence",
            "slot",
            "prev_status",
            "prev_vehicle",
            "curr_status",
            "curr_vehicle",
            "confidence",
            "source_model",
            "source_version",
            "received_at",
        }

        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_deserialization_read_only(self):
        """Testa que o serializer principal é read-only para criação"""
        data = {
            "event_type": "STATUS_CHANGE",
            "curr_status": "OCCUPIED",
            "slot": self.slot.id,
        }

        serializer = SlotStatusEventSerializer(data=data)
        # Este serializer é principalmente para leitura
        # A criação deve usar SlotStatusEventCreateSerializer


class SlotStatusEventCreateSerializerTest(TestCase, TestDataMixin):
    """Testes para SlotStatusEventCreateSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_obj = self.create_client()
        self.slot = self.create_slot(client=self.client_obj)
        self.camera = self.create_camera(client=self.client_obj)
        self.vehicle_type = self.create_vehicle_type("Car")

    def test_create_serializer_fields(self):
        """Testa campos do serializer de criação"""
        serializer = SlotStatusEventCreateSerializer()
        expected_fields = {
            "event_type",
            "occurred_at",
            "lot",
            "camera",
            "sequence",
            "slot",
            "prev_status",
            "prev_vehicle",
            "curr_status",
            "curr_vehicle",
            "confidence",
            "source_model",
            "source_version",
        }

        self.assertEqual(set(serializer.fields.keys()), expected_fields)

    def test_valid_serialization(self):
        """Testa serialização com dados válidos"""
        occurred_at = timezone.now()
        data = {
            "event_type": "STATUS_CHANGE",
            "occurred_at": occurred_at,
            "lot": self.slot.lot.id,
            "slot": self.slot.id,
            "curr_status": "OCCUPIED",
            "prev_status": "FREE",
            "confidence": 0.95,
        }

        serializer = SlotStatusEventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_create_method_sets_client(self):
        """Testa que o método create define o client baseado no slot - cobre linhas 27-29"""
        occurred_at = timezone.now()
        data = {
            "event_type": "VEHICLE_DETECTED",
            "occurred_at": occurred_at,
            "lot": self.slot.lot.id,
            "slot": self.slot.id,
            "curr_status": "OCCUPIED",
            "camera": self.camera.id,
            "sequence": 123,
            "confidence": 0.85,
            "source_model": "YOLOv8",
            "source_version": "1.0",
        }

        serializer = SlotStatusEventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Chamar create e verificar se o client foi definido
        event = serializer.save()

        self.assertEqual(event.client, self.slot.client)
        self.assertEqual(event.event_type, "VEHICLE_DETECTED")
        self.assertEqual(event.slot, self.slot)
        self.assertEqual(event.camera, self.camera)
        self.assertEqual(event.sequence, 123)
        self.assertEqual(float(event.confidence), 0.85)
        self.assertEqual(event.source_model, "YOLOv8")
        self.assertEqual(event.source_version, "1.0")

    def test_create_with_vehicle_types(self):
        """Testa criação com tipos de veículo"""
        car_type = self.create_vehicle_type("Car")
        truck_type = self.create_vehicle_type("Truck")

        data = {
            "event_type": "VEHICLE_DETECTED",
            "occurred_at": timezone.now(),
            "lot": self.slot.lot.id,
            "slot": self.slot.id,
            "prev_status": "FREE",
            "prev_vehicle": car_type.id,
            "curr_status": "OCCUPIED",
            "curr_vehicle": truck_type.id,
        }

        serializer = SlotStatusEventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        event = serializer.save()
        self.assertEqual(event.prev_vehicle, car_type)
        self.assertEqual(event.curr_vehicle, truck_type)

    def test_minimal_valid_data(self):
        """Testa criação com dados mínimos necessários"""
        data = {
            "event_type": "STATUS_CHANGE",
            "occurred_at": timezone.now(),
            "lot": self.slot.lot.id,
            "slot": self.slot.id,
            "curr_status": "OCCUPIED",
        }

        serializer = SlotStatusEventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        event = serializer.save()
        self.assertEqual(event.client, self.slot.client)
        self.assertEqual(event.curr_status, "OCCUPIED")
        self.assertIsNone(event.prev_status)

    def test_invalid_event_type(self):
        """Testa validação com tipo de evento inválido"""
        data = {
            "event_type": "INVALID_TYPE",
            "occurred_at": timezone.now(),
            "lot": self.slot.lot.id,
            "slot": self.slot.id,
            "curr_status": "OCCUPIED",
        }

        serializer = SlotStatusEventCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("event_type", serializer.errors)

    def test_missing_required_fields(self):
        """Testa validação com campos obrigatórios faltando"""
        data = {
            "event_type": "STATUS_CHANGE",
            # Faltando occurred_at, lot, slot, curr_status
        }

        serializer = SlotStatusEventCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        required_fields = ["occurred_at", "lot", "slot", "curr_status"]
        for field in required_fields:
            self.assertIn(field, serializer.errors)

    def test_confidence_validation(self):
        """Testa validação do campo confidence"""
        # Teste com valor válido
        data = {
            "event_type": "STATUS_CHANGE",
            "occurred_at": timezone.now(),
            "lot": self.slot.lot.id,
            "slot": self.slot.id,
            "curr_status": "OCCUPIED",
            "confidence": 0.999,
        }

        serializer = SlotStatusEventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        event = serializer.save()
        self.assertEqual(float(event.confidence), 0.999)

    def test_optional_fields_none(self):
        """Testa criação com campos opcionais como None"""
        data = {
            "event_type": "STATUS_CHANGE",
            "occurred_at": timezone.now(),
            "lot": self.slot.lot.id,
            "slot": self.slot.id,
            "curr_status": "OCCUPIED",
            "camera": None,
            "sequence": None,
            "prev_status": None,
            "prev_vehicle": None,
            "curr_vehicle": None,
            "confidence": None,
            "source_model": None,
            "source_version": None,
        }

        serializer = SlotStatusEventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        event = serializer.save()
        self.assertIsNone(event.camera)
        self.assertIsNone(event.sequence)
        self.assertIsNone(event.prev_status)
        self.assertIsNone(event.prev_vehicle)
        self.assertIsNone(event.curr_vehicle)
        self.assertIsNone(event.confidence)
        self.assertIsNone(event.source_model)
        self.assertIsNone(event.source_version)
