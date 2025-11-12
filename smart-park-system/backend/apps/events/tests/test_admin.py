from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock, patch

from apps.events.admin import SlotStatusEventsAdmin
from apps.events.models import SlotStatusEvents
from .test_utils import TestDataMixin


class SlotStatusEventsAdminTest(TestCase, TestDataMixin):
    """Testes para SlotStatusEventsAdmin"""

    def setUp(self):
        """Setup para cada teste"""
        self.site = AdminSite()
        self.admin = SlotStatusEventsAdmin(SlotStatusEvents, self.site)
        self.factory = RequestFactory()
        self.user = self.create_admin_user()

        self.client_obj = self.create_client()
        self.slot = self.create_slot(client=self.client_obj)
        self.camera = self.create_camera(client=self.client_obj)

        # Criar evento
        self.event = self.create_slot_status_event(
            slot=self.slot,
            camera=self.camera,
            event_type="STATUS_CHANGE",
            occurred_at=timezone.now() - timedelta(minutes=5),
            sequence=123,
            confidence=0.95,
            source_model="YOLOv8",
            source_version="1.0.0",
        )

    def test_get_queryset_with_select_related(self):
        """Testa que get_queryset faz select_related - cobre linha 53"""
        request = self.factory.get("/")
        queryset = self.admin.get_queryset(request)

        # Verificar se consegue acessar campos relacionados sem queries adicionais
        event = queryset.get(id=self.event.id)
        # Acessar campos relacionados deve estar pre-carregado
        client_name = event.client.name
        slot_code = event.slot.slot_code
        self.assertEqual(client_name, self.client_obj.name)
        self.assertEqual(slot_code, self.slot.slot_code)

    def test_event_id_short(self):
        """Testa event_id_short - cobre linha 65"""
        result = self.admin.event_id_short(self.event)
        expected = f"{str(self.event.event_id)[:8]}..."
        self.assertEqual(result, expected)

    def test_event_type_display_with_known_type(self):
        """Testa event_type_display para tipos conhecidos - cobre linhas 70-77"""
        # Teste para SLOT_OCCUPIED
        self.event.event_type = "SLOT_OCCUPIED"
        result = self.admin.event_type_display(self.event)
        self.assertIn("color: red", result)
        self.assertIn("SLOT_OCCUPIED", result)

        # Teste para SLOT_FREED
        self.event.event_type = "SLOT_FREED"
        result = self.admin.event_type_display(self.event)
        self.assertIn("color: green", result)

        # Teste para SLOT_RESERVED
        self.event.event_type = "SLOT_RESERVED"
        result = self.admin.event_type_display(self.event)
        self.assertIn("color: orange", result)

        # Teste para SLOT_MAINTENANCE
        self.event.event_type = "SLOT_MAINTENANCE"
        result = self.admin.event_type_display(self.event)
        self.assertIn("color: gray", result)

    def test_event_type_display_with_unknown_type(self):
        """Testa event_type_display para tipo desconhecido"""
        self.event.event_type = "UNKNOWN_TYPE"
        result = self.admin.event_type_display(self.event)
        self.assertIn("color: blue", result)  # cor padrão
        self.assertIn("UNKNOWN_TYPE", result)

    def test_slot_info_with_slot(self):
        """Testa slot_info com slot presente - cobre linhas 86-93"""
        result = self.admin.slot_info(self.event)
        expected = f"{self.slot.slot_code} ({self.slot.lot.establishment.name})"
        self.assertEqual(result, expected)

    def test_slot_info_with_lot_only(self):
        """Testa slot_info apenas com lot usando mock"""
        mock_event = Mock()
        mock_event.slot = None
        mock_lot = Mock()
        mock_lot.lot_code = "LOT001"
        mock_event.lot = mock_lot
        mock_event.establishment = None

        result = self.admin.slot_info(mock_event)
        expected = "Lote: LOT001"
        self.assertEqual(result, expected)

    def test_slot_info_with_establishment_only(self):
        """Testa slot_info apenas com establishment (via lot)"""
        mock_event = Mock()
        mock_event.slot = None
        mock_event.lot = None
        mock_establishment = Mock()
        mock_establishment.name = "Test Establishment"
        mock_event.establishment = mock_establishment

        result = self.admin.slot_info(mock_event)
        expected = "Estabelecimento: Test Establishment"
        self.assertEqual(result, expected)

    def test_slot_info_with_none(self):
        """Testa slot_info quando não há localização"""
        mock_event = Mock()
        mock_event.slot = None
        mock_event.lot = None
        mock_event.establishment = None

        result = self.admin.slot_info(mock_event)
        self.assertEqual(result, "N/A")

    def test_timing_info(self):
        """Testa timing_info - cobre linhas 98-109"""
        result = self.admin.timing_info(self.event)

        # Verificar que contém as informações de timing
        self.assertIn("Ocorreu:", result)
        self.assertIn("Recebido:", result)
        self.assertIn("Delay:", result)

        # Verificar formato HTML
        self.assertIn("<br>", result)
        self.assertIn("<span", result)
        self.assertIn("color:", result)

    def test_timing_info_color_logic(self):
        """Testa lógica de cores do timing_info"""
        # Teste delay rápido (< 5s) - verde
        now = timezone.now()
        self.event.occurred_at = now - timedelta(seconds=2)
        self.event.received_at = now

        result = self.admin.timing_info(self.event)
        self.assertIn("color: green", result)

        # Teste delay moderado (< 30s) - laranja
        self.event.occurred_at = now - timedelta(seconds=15)
        result = self.admin.timing_info(self.event)
        self.assertIn("color: orange", result)

        # Teste delay alto (> 30s) - vermelho
        self.event.occurred_at = now - timedelta(seconds=60)
        result = self.admin.timing_info(self.event)
        self.assertIn("color: red", result)

    def test_processed_time_instantaneous(self):
        """Testa processed_time para tempo instantâneo - cobre linhas 120-136"""
        now = timezone.now()
        self.event.occurred_at = now - timedelta(milliseconds=500)
        self.event.received_at = now

        result = self.admin.processed_time(self.event)
        self.assertIn("color: green", result)
        self.assertIn("Instantâneo", result)

    def test_processed_time_fast(self):
        """Testa processed_time para tempo rápido (< 5s)"""
        now = timezone.now()
        self.event.occurred_at = now - timedelta(seconds=3)
        self.event.received_at = now

        result = self.admin.processed_time(self.event)
        self.assertIn("color: green", result)
        self.assertIn("3.0s", result)

    def test_processed_time_moderate(self):
        """Testa processed_time para tempo moderado (< 30s)"""
        now = timezone.now()
        self.event.occurred_at = now - timedelta(seconds=15)
        self.event.received_at = now

        result = self.admin.processed_time(self.event)
        self.assertIn("color: orange", result)
        self.assertIn("15.0s", result)

    def test_processed_time_slow(self):
        """Testa processed_time para tempo lento (> 30s)"""
        now = timezone.now()
        self.event.occurred_at = now - timedelta(seconds=60)
        self.event.received_at = now

        result = self.admin.processed_time(self.event)
        self.assertIn("color: red", result)
        self.assertIn("60.0s", result)

    def test_processed_time_detail_fast(self):
        """Testa processed_time_detail para processamento rápido - cobre linhas 141-155"""
        now = timezone.now()
        self.event.occurred_at = now - timedelta(seconds=2)
        self.event.received_at = now

        result = self.admin.processed_time_detail(self.event)

        self.assertIn("Ocorrido em:", result)
        self.assertIn("Recebido em:", result)
        self.assertIn("Delay: 2.00 segundos", result)
        self.assertIn("color: green", result)
        self.assertIn("✓ Processamento rápido", result)

    def test_processed_time_detail_moderate(self):
        """Testa processed_time_detail para processamento moderado"""
        now = timezone.now()
        self.event.occurred_at = now - timedelta(seconds=15)
        self.event.received_at = now

        result = self.admin.processed_time_detail(self.event)

        self.assertIn("Delay: 15.00 segundos", result)
        self.assertIn("color: orange", result)
        self.assertIn("⚠️ Delay moderado", result)

    def test_processed_time_detail_slow(self):
        """Testa processed_time_detail para processamento lento"""
        now = timezone.now()
        self.event.occurred_at = now - timedelta(seconds=60)
        self.event.received_at = now

        result = self.admin.processed_time_detail(self.event)

        self.assertIn("Delay: 60.00 segundos", result)
        self.assertIn("color: red", result)
        self.assertIn("⚠️ Delay alto - verificar conectividade", result)

    def test_event_payload_formatted(self):
        """Testa event_payload_formatted - cobre linhas 160-168"""
        result = self.admin.event_payload_formatted(self.event)

        # Verificar que contém dados do evento (com HTML escaping)
        self.assertIn("&quot;event_type&quot;: &quot;STATUS_CHANGE&quot;", result)
        self.assertIn("&quot;confidence&quot;: 0.95", result)
        self.assertIn("&quot;source_model&quot;: &quot;YOLOv8&quot;", result)
        self.assertIn("&quot;source_version&quot;: &quot;1.0.0&quot;", result)

        # Verificar formato HTML
        self.assertIn("<pre>", result)
        self.assertIn("</pre>", result)

    def test_event_payload_formatted_with_none_values(self):
        """Testa event_payload_formatted com valores None"""
        # Criar evento com campos None
        event_minimal = self.create_slot_status_event(
            slot=self.slot,
            event_type="STATUS_CHANGE",
            confidence=None,
            source_model=None,
            source_version=None,
        )

        result = self.admin.event_payload_formatted(event_minimal)

        self.assertIn("&quot;confidence&quot;: null", result)
        self.assertIn("&quot;source_model&quot;: null", result)
        self.assertIn("&quot;source_version&quot;: null", result)

    def test_event_payload_formatted_json_error(self):
        """Testa event_payload_formatted quando json.dumps falha - cobre linhas 175-176"""
        # Criar um mock que vai causar erro no json.dumps
        mock_event = Mock()
        mock_event.event_type = "STATUS_CHANGE"
        mock_event.curr_status = "OCCUPIED"
        mock_event.prev_status = "FREE"
        mock_event.confidence = 0.95
        mock_event.source_model = "YOLOv8"
        mock_event.source_version = "1.0.0"

        # Mock json.dumps para lançar uma exceção
        with patch("json.dumps") as mock_dumps:
            mock_dumps.side_effect = Exception("JSON error")

            result = self.admin.event_payload_formatted(mock_event)

            # Deve retornar str(data) quando json.dumps falha
            self.assertIn("'event_type': 'STATUS_CHANGE'", result)
            self.assertIn("'confidence': 0.95", result)
            self.assertIn("'source_model': 'YOLOv8'", result)

    def test_admin_list_display(self):
        """Testa que list_display está configurado corretamente"""
        expected_fields = [
            "event_id_short",
            "event_type_display",
            "slot_info",
            "client",
            "timing_info",
            "processed_time",
        ]

        self.assertEqual(self.admin.list_display, expected_fields)

    def test_admin_readonly_fields(self):
        """Testa que readonly_fields está configurado corretamente"""
        expected_fields = [
            "event_id",
            "received_at",
            "processed_time_detail",
            "event_payload_formatted",
        ]

        self.assertEqual(self.admin.readonly_fields, expected_fields)

    def test_admin_search_fields(self):
        """Testa que search_fields está configurado corretamente"""
        expected_fields = [
            "event_id",
            "slot__slot_code",
            "client__name",
            "slot__lot__lot_code",
            "slot__lot__establishment__name",
        ]

        self.assertEqual(self.admin.search_fields, expected_fields)
