from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import uuid

from apps.events.models import SlotStatusEvents
from apps.core.models import TenantManager
from .test_utils import TestDataMixin


class SlotStatusEventsModelTest(TestCase, TestDataMixin):
    """Testes para o model SlotStatusEvents"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_obj = self.create_client()
        self.slot = self.create_slot(client=self.client_obj)
        self.lot = self.slot.lot
        self.camera = self.create_camera(client=self.client_obj)

    def test_create_slot_status_event(self):
        """Testa criação de evento de status de slot"""
        event_time = timezone.now()
        event = SlotStatusEvents.objects.create(
            event_type="STATUS_CHANGE",
            occurred_at=event_time,
            lot=self.lot,
            slot=self.slot,
            client=self.client_obj,
            prev_status="FREE",
            curr_status="OCCUPIED",
        )

        self.assertIsNotNone(event.id)
        self.assertEqual(event.event_type, "STATUS_CHANGE")
        self.assertEqual(event.occurred_at, event_time)
        self.assertEqual(event.lot, self.lot)
        self.assertEqual(event.slot, self.slot)
        self.assertEqual(event.client, self.client_obj)
        self.assertEqual(event.prev_status, "FREE")
        self.assertEqual(event.curr_status, "OCCUPIED")
        self.assertIsInstance(event.event_id, uuid.UUID)

    def test_event_id_unique_default(self):
        """Testa que event_id é único e gerado automaticamente"""
        event1 = self.create_slot_status_event()
        event2 = self.create_slot_status_event()

        self.assertIsInstance(event1.event_id, uuid.UUID)
        self.assertIsInstance(event2.event_id, uuid.UUID)
        self.assertNotEqual(event1.event_id, event2.event_id)

    def test_event_type_choices(self):
        """Testa os tipos de evento disponíveis"""
        choices = dict(SlotStatusEvents.EVENT_TYPE_CHOICES)
        expected_types = [
            "STATUS_CHANGE",
            "VEHICLE_DETECTED",
            "VEHICLE_LEFT",
            "MAINTENANCE_START",
            "MAINTENANCE_END",
            "RESERVATION_START",
            "RESERVATION_END",
        ]

        for event_type in expected_types:
            self.assertIn(event_type, choices)

    def test_optional_fields(self):
        """Testa campos opcionais"""
        event = SlotStatusEvents.objects.create(
            event_type="STATUS_CHANGE",
            occurred_at=timezone.now(),
            lot=self.lot,
            slot=self.slot,
            client=self.client_obj,
            curr_status="OCCUPIED",
            # Campos opcionais
            camera=self.camera,
            sequence=123,
            prev_status="FREE",
            confidence=0.95,
            source_model="YOLOv8",
            source_version="1.0.0",
        )

        self.assertEqual(event.camera, self.camera)
        self.assertEqual(event.sequence, 123)
        self.assertEqual(event.prev_status, "FREE")
        self.assertEqual(float(event.confidence), 0.95)
        self.assertEqual(event.source_model, "YOLOv8")
        self.assertEqual(event.source_version, "1.0.0")

    def test_received_at_auto_now_add(self):
        """Testa que received_at é definido automaticamente"""
        before_creation = timezone.now()
        event = self.create_slot_status_event()
        after_creation = timezone.now()

        self.assertGreaterEqual(event.received_at, before_creation)
        self.assertLessEqual(event.received_at, after_creation)

    def test_vehicle_type_relationships(self):
        """Testa relacionamentos com tipos de veículo"""
        car_type = self.create_vehicle_type("Car")
        truck_type = self.create_vehicle_type("Truck")

        event = SlotStatusEvents.objects.create(
            event_type="VEHICLE_DETECTED",
            occurred_at=timezone.now(),
            lot=self.lot,
            slot=self.slot,
            client=self.client_obj,
            prev_vehicle=car_type,
            curr_vehicle=truck_type,
            curr_status="OCCUPIED",
        )

        self.assertEqual(event.prev_vehicle, car_type)
        self.assertEqual(event.curr_vehicle, truck_type)

    def test_foreign_key_relationships(self):
        """Testa todos os relacionamentos de chave estrangeira"""
        event = self.create_slot_status_event(
            camera=self.camera, lot=self.lot, slot=self.slot
        )

        self.assertEqual(event.lot, self.lot)
        self.assertEqual(event.camera, self.camera)
        self.assertEqual(event.slot, self.slot)
        self.assertEqual(event.client, self.client_obj)

    def test_str_method(self):
        """Testa o método __str__ do modelo - cobre linha 77"""
        event_time = timezone.now()
        event = self.create_slot_status_event(
            event_type="STATUS_CHANGE", occurred_at=event_time
        )

        expected_str = f"STATUS_CHANGE - {event.slot.slot_code} ({event_time})"
        self.assertEqual(str(event), expected_str)

    def test_meta_options(self):
        """Testa as opções Meta do modelo"""
        self.assertEqual(SlotStatusEvents._meta.db_table, "slot_status_events")

        # Verifica se o índice foi criado
        indexes = SlotStatusEvents._meta.indexes
        self.assertEqual(len(indexes), 1)
        self.assertEqual(indexes[0].name, "ix_slot_sts_events_occ_at")
        self.assertEqual(indexes[0].fields, ["slot", "occurred_at"])

    def test_decimal_field_precision(self):
        """Testa precisão do campo confidence"""
        event = self.create_slot_status_event(confidence=0.999)

        # Confidence deve ter 4 dígitos total, 3 decimais
        self.assertEqual(float(event.confidence), 0.999)

        # Testa valor com mais precisão
        event.confidence = 0.9999
        event.save()
        event.refresh_from_db()
        # Deve ser truncado para 3 casas decimais
        self.assertEqual(float(event.confidence), 1.000)


class SlotStatusEventsTenantManagerTest(TestCase, TestDataMixin):
    """Testes para o TenantManager do SlotStatusEvents"""

    def setUp(self):
        """Setup para cada teste"""
        self.client1 = self.create_client("Client 1")
        self.client2 = self.create_client("Client 2")

        self.slot1 = self.create_slot(client=self.client1)
        self.slot2 = self.create_slot(client=self.client2)

    def test_objects_manager_is_tenant_manager(self):
        """Testa se o manager padrão é TenantManager"""
        self.assertIsInstance(SlotStatusEvents.objects, TenantManager)

    def test_for_user_filters_by_client(self):
        """Testa filtro por cliente do usuário"""
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")

        self.create_client_member(user1, self.client1)
        self.create_client_member(user2, self.client2)

        # Criar eventos para cada cliente
        event1 = self.create_slot_status_event(slot=self.slot1, client=self.client1)
        event2 = self.create_slot_status_event(slot=self.slot2, client=self.client2)

        # Testar filtro por usuário
        events_user1 = SlotStatusEvents.objects.for_user(user1)
        events_user2 = SlotStatusEvents.objects.for_user(user2)

        self.assertIn(event1, events_user1)
        self.assertNotIn(event2, events_user1)

        self.assertIn(event2, events_user2)
        self.assertNotIn(event1, events_user2)

    def test_for_user_without_client(self):
        """Testa for_user com usuário sem cliente"""
        user_without_client = self.create_user("user_no_client")

        # Criar eventos
        self.create_slot_status_event(slot=self.slot1, client=self.client1)

        # Usuário sem cliente não deve ver nenhum evento
        events = SlotStatusEvents.objects.for_user(user_without_client)
        self.assertEqual(events.count(), 0)

    def test_for_user_with_multiple_clients(self):
        """Testa usuário com múltiplos clientes"""
        user = self.create_user("multi_client_user")

        # Usuário membro de ambos os clientes
        self.create_client_member(user, self.client1)
        self.create_client_member(user, self.client2)

        # Criar eventos para ambos os clientes
        event1 = self.create_slot_status_event(slot=self.slot1, client=self.client1)
        event2 = self.create_slot_status_event(slot=self.slot2, client=self.client2)

        # Usuário deve ver eventos de ambos os clientes
        events = SlotStatusEvents.objects.for_user(user)
        self.assertIn(event1, events)
        self.assertIn(event2, events)
        self.assertEqual(events.count(), 2)
