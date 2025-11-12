from django.test import TestCase
from django.urls import reverse, resolve
from apps.events import views


class EventsUrlsTest(TestCase):
    """Testes para URLs da app events"""

    def test_slot_status_event_list_url(self):
        """Testa URL de listagem de eventos de status de slot"""
        url = reverse("events:slot-status-event-list")
        self.assertEqual(url, "/api/events/slot-status-events/")

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.SlotStatusEventListCreateView)

    def test_slot_status_event_detail_url(self):
        """Testa URL de detalhes de evento de status de slot"""
        url = reverse("events:slot-status-event-detail", kwargs={"pk": 123})
        self.assertEqual(url, "/api/events/slot-status-events/123/")

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.SlotStatusEventDetailView)
        self.assertEqual(resolver.kwargs["pk"], 123)

    def test_app_name(self):
        """Testa se o app_name está definido corretamente"""
        # Verificar se o namespace funciona
        url = reverse("events:slot-status-event-list")
        self.assertIn("slot-status-events", url)

    def test_url_patterns_count(self):
        """Testa que temos o número esperado de URLs"""
        from apps.events.urls import urlpatterns

        self.assertEqual(len(urlpatterns), 2)

    def test_all_view_classes_resolvable(self):
        """Testa que todas as views podem ser resolvidas"""
        # Lista de eventos
        url1 = "/api/events/slot-status-events/"
        resolver1 = resolve(url1)
        self.assertEqual(resolver1.func.view_class, views.SlotStatusEventListCreateView)

        # Detalhe de evento
        url2 = "/api/events/slot-status-events/456/"
        resolver2 = resolve(url2)
        self.assertEqual(resolver2.func.view_class, views.SlotStatusEventDetailView)
        self.assertEqual(resolver2.kwargs["pk"], 456)
