from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import Mock, patch

from apps.catalog.admin import *
from apps.catalog.models import *
from .test_utils import TestDataMixin

User = get_user_model()


class AdminTestCase(TestCase, TestDataMixin):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client_obj = self.create_client()

    def get_request(self):
        request = self.factory.get("/admin/")
        request.user = self.user
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))
        return request


class InlineTests(AdminTestCase):
    def test_lots_inline_slots_count(self):
        """Test LotsInline slots_count method"""
        establishment = self.create_establishment(client=self.client_obj)
        lot = self.create_lot(establishment=establishment)
        self.create_slot(lot=lot)
        self.create_slot(lot=lot)

        inline = LotsInline(Lots, self.site)
        self.assertEqual(inline.slots_count(lot), 2)

        # Test with no pk
        new_lot = Lots(establishment=establishment)
        self.assertEqual(inline.slots_count(new_lot), 0)

    def test_slots_inline_current_status_display(self):
        """Test SlotsInline current_status_display method"""
        lot = self.create_lot(client=self.client_obj)
        slot = self.create_slot(lot=lot)
        inline = SlotsInline(Slots, self.site)

        # Test FREE status
        self.create_slot_status(slot=slot, status="FREE")
        result = inline.current_status_display(slot)
        self.assertIn("green", result)

        # Test OCCUPIED status
        slot.current_status.all().delete()
        self.create_slot_status(slot=slot, status="OCCUPIED")
        result = inline.current_status_display(slot)
        self.assertIn("red", result)

        # Test no status
        slot.current_status.all().delete()
        result = inline.current_status_display(slot)
        self.assertIn("Sem status", result)

        # Test new slot (no pk)
        new_slot = Slots(lot=lot)
        self.assertEqual(inline.current_status_display(new_slot), "-")

        # Test exception by mocking the first() method
        slot.current_status.all().delete()
        original_first = slot.current_status.first
        slot.current_status.first = Mock(side_effect=Exception())
        result = inline.current_status_display(slot)
        self.assertIn("Sem status", result)
        # Restore
        slot.current_status.first = original_first


class StoreTypesAdminTest(AdminTestCase):
    def test_admin_methods(self):
        """Test StoreTypesAdmin methods"""
        admin = StoreTypesAdmin(StoreTypes, self.site)
        store_type = self.create_store_type()

        # Test get_queryset
        queryset = admin.get_queryset(self.get_request())
        self.assertTrue(
            hasattr(queryset.first() or queryset.model(), "establishments_count")
        )

        # Test establishments_count with establishments
        store_type.establishments_count = 2
        result = admin.establishments_count(store_type)
        self.assertIn("2", result)
        self.assertIn("href", result)

        # Test establishments_count without establishments
        store_type.establishments_count = 0
        self.assertEqual(admin.establishments_count(store_type), "0")


class EstablishmentsAdminTest(AdminTestCase):
    def test_admin_methods(self):
        """Test EstablishmentsAdmin methods"""
        admin = EstablishmentsAdmin(Establishments, self.site)
        establishment = self.create_establishment(
            client=self.client_obj, city="SP", state="SP"
        )

        # Test location_info
        self.assertEqual(admin.location_info(establishment), "SP, SP")

        # Test lots_count with annotation
        establishment.lots_count = 2
        result = admin.lots_count(establishment)
        self.assertIn("2", result)

        # Test lots_count without annotation (fallback)
        delattr(establishment, "lots_count")
        self.create_lot(establishment=establishment)
        result = admin.lots_count(establishment)
        self.assertIn("1", result)

        # Test lots_count zero
        establishment.lots_count = 0
        self.assertEqual(admin.lots_count(establishment), "0")

        # Test total_slots with annotation
        establishment.total_slots = 5
        self.assertEqual(admin.total_slots(establishment), 5)

        # Test total_slots fallback
        delattr(establishment, "total_slots")
        lot = self.create_lot(establishment=establishment)
        self.create_slot(lot=lot)
        self.assertEqual(admin.total_slots(establishment), 1)

        # Test occupied_slots - high occupancy (>80%)
        establishment.occupied_slots_count = 9
        admin.total_slots = Mock(return_value=10)
        result = admin.occupied_slots(establishment)
        self.assertIn("red", result)

        # Test occupied_slots - medium occupancy (50-80%)
        establishment.occupied_slots_count = 6
        result = admin.occupied_slots(establishment)
        self.assertIn("orange", result)

        # Test occupied_slots - low occupancy (<50%)
        establishment.occupied_slots_count = 3
        result = admin.occupied_slots(establishment)
        self.assertIn("green", result)

        # Test occupied_slots - no slots
        admin.total_slots = Mock(return_value=0)
        self.assertEqual(admin.occupied_slots(establishment), "0/0")


class LotsAdminTest(AdminTestCase):
    def test_admin_methods(self):
        """Test LotsAdmin methods"""
        admin = LotsAdmin(Lots, self.site)
        establishment = self.create_establishment(client=self.client_obj)
        lot = self.create_lot(establishment=establishment)

        # Test client_info
        self.assertEqual(admin.client_info(lot), self.client_obj.name)

        # Test slots_count with annotation
        lot.slots_count = 2
        result = admin.slots_count(lot)
        self.assertIn("2", result)

        # Test slots_count fallback
        delattr(lot, "slots_count")
        self.create_slot(lot=lot)
        result = admin.slots_count(lot)
        self.assertIn("1", result)

        # Test slots_count zero
        lot.slots_count = 0
        self.assertEqual(admin.slots_count(lot), "0")

        # Test occupied_slots colors
        lot.occupied_slots_count = 9
        lot.slots_count = 10
        result = admin.occupied_slots(lot)
        self.assertIn("red", result)

        lot.occupied_slots_count = 6
        result = admin.occupied_slots(lot)
        self.assertIn("orange", result)

        lot.occupied_slots_count = 3
        result = admin.occupied_slots(lot)
        self.assertIn("green", result)

        lot.slots_count = 0
        self.assertEqual(admin.occupied_slots(lot), "0/0")


class SlotsAdminTest(AdminTestCase):
    def test_admin_methods(self):
        """Test SlotsAdmin methods"""
        admin = SlotsAdmin(Slots, self.site)
        lot = self.create_lot(client=self.client_obj)
        slot = self.create_slot(lot=lot)
        # Create initial status
        self.create_slot_status(slot=slot, status="FREE")

        # Test lot_info
        expected = f"{lot.lot_code} ({lot.establishment.name})"
        self.assertEqual(admin.lot_info(slot), expected)

        # Test current_status_display for all status types
        statuses = {
            "FREE": "green",
            "OCCUPIED": "red",
            "RESERVED": "orange",
            "MAINTENANCE": "gray",
        }

        for status_code, color in statuses.items():
            # Clear existing status and create new one
            SlotStatus.objects.filter(slot=slot).delete()
            status = self.create_slot_status(slot=slot, status=status_code)
            slot.refresh_from_db()  # Refresh to update the current_status relation
            result = admin.current_status_display(slot)
            self.assertIn(color, result)

        # Test exception by deleting current_status attribute
        SlotStatus.objects.filter(slot=slot).delete()
        result = admin.current_status_display(slot)
        self.assertIn("Sem status", result)

        # Test last_status_change
        status = self.create_slot_status(slot=slot, status="FREE")
        result = admin.last_status_change(slot)
        self.assertRegex(result, r"\d{2}/\d{2} \d{2}:\d{2}")

        # Test last_status_change exception
        SlotStatus.objects.filter(slot=slot).delete()
        self.assertEqual(admin.last_status_change(slot), "-")

        # Test current_status_info complete
        vehicle_type = self.create_vehicle_type(name="Car")
        # Clear existing status and create new one with vehicle type
        SlotStatus.objects.filter(slot=slot).delete()
        status = SlotStatus.objects.create(
            slot=slot, status="OCCUPIED", vehicle_type=vehicle_type, confidence=9.55
        )
        result = admin.current_status_info(slot)
        self.assertIn("Car", result)
        self.assertIn("9.55", result)

        # Test current_status_info exception
        SlotStatus.objects.filter(slot=slot).delete()
        self.assertEqual(admin.current_status_info(slot), "Nenhum status registrado")

        # Test actions
        slot1 = self.create_slot(lot=lot, active=False)
        slot2 = self.create_slot(lot=lot, active=False)
        queryset = Slots.objects.filter(id__in=[slot1.id, slot2.id])

        admin.activate_slots(self.get_request(), queryset)
        slot1.refresh_from_db()
        self.assertTrue(slot1.active)

        admin.deactivate_slots(self.get_request(), queryset)
        slot1.refresh_from_db()
        self.assertFalse(slot1.active)


class SlotTypesAdminTest(AdminTestCase):
    def test_admin_methods(self):
        """Test SlotTypesAdmin methods"""
        admin = SlotTypesAdmin(SlotTypes, self.site)
        slot_type = self.create_slot_type()

        # Test slots_count with slots
        slot_type.slots_count = 2
        result = admin.slots_count(slot_type)
        self.assertIn("2", result)

        # Test slots_count without slots
        slot_type.slots_count = 0
        self.assertEqual(admin.slots_count(slot_type), "0")


class VehicleTypesAdminTest(AdminTestCase):
    def test_admin_methods(self):
        """Test VehicleTypesAdmin methods"""
        admin = VehicleTypesAdmin(VehicleTypes, self.site)
        vehicle_type = self.create_vehicle_type()
        vehicle_type.active_slots_count = 5

        result = admin.active_slots_count(vehicle_type)
        self.assertEqual(result, "5 vagas ocupadas")


class SlotStatusAdminTest(AdminTestCase):
    def test_admin_methods(self):
        """Test SlotStatusAdmin methods"""
        admin = SlotStatusAdmin(SlotStatus, self.site)
        slot = self.create_slot(client=self.client_obj)

        # Test slot_info
        status = self.create_slot_status(slot=slot, status="FREE")
        expected = f"{slot.slot_code} ({slot.lot.establishment.name})"
        self.assertEqual(admin.slot_info(status), expected)

        # Test confidence_display colors
        test_cases = [(9.5, "green"), (8.0, "orange"), (6.5, "red"), (None, "-")]

        for confidence, expected in test_cases:
            # Clear existing status before creating new one
            SlotStatus.objects.filter(slot=slot).delete()
            status = self.create_slot_status(
                slot=slot, status="FREE", confidence=confidence
            )
            result = admin.confidence_display(status)
            if confidence:
                self.assertIn(expected, result)
                self.assertIn(str(confidence), result)
            else:
                self.assertEqual(result, expected)


class SlotStatusHistoryAdminTest(AdminTestCase):
    def test_admin_methods(self):
        """Test SlotStatusHistoryAdmin methods"""
        admin = SlotStatusHistoryAdmin(SlotStatusHistory, self.site)
        slot = self.create_slot(client=self.client_obj)

        # Test slot_info
        history = self.create_slot_status_history(slot=slot, status="FREE")
        expected = f"{slot.slot_code} ({slot.lot.establishment.name})"
        self.assertEqual(admin.slot_info(history), expected)

        # Test confidence_display (same logic as SlotStatusAdmin)
        history = self.create_slot_status_history(
            slot=slot, status="FREE", confidence=9.5
        )
        result = admin.confidence_display(history)
        self.assertIn("green", result)

        history = self.create_slot_status_history(
            slot=slot, status="FREE", confidence=None
        )
        self.assertEqual(admin.confidence_display(history), "-")
