from django.test import TestCase
from django.urls import reverse, resolve
from apps.hardware import views


class HardwareUrlsTest(TestCase):
    """Testes para URLs da app hardware"""

    def test_api_key_list_url(self):
        """Testa URL de listagem de API keys"""
        url = reverse("hardware:api-key-list")
        self.assertEqual(url, "/api/hardware/api-keys/")

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.ApiKeyListCreateView)

    def test_api_key_detail_url(self):
        """Testa URL de detalhes de API key"""
        url = reverse("hardware:api-key-detail", kwargs={"pk": 1})
        self.assertEqual(url, "/api/hardware/api-keys/1/")

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.ApiKeyDetailView)
        self.assertEqual(resolver.kwargs["pk"], 1)

    def test_camera_list_url(self):
        """Testa URL de listagem de câmeras"""
        url = reverse("hardware:camera-list")
        self.assertEqual(url, "/api/hardware/cameras/")

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CameraListCreateView)

    def test_camera_detail_url(self):
        """Testa URL de detalhes de câmera"""
        url = reverse("hardware:camera-detail", kwargs={"pk": 42})
        self.assertEqual(url, "/api/hardware/cameras/42/")

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CameraDetailView)
        self.assertEqual(resolver.kwargs["pk"], 42)

    def test_heartbeat_create_url(self):
        """Testa URL de criação de heartbeat"""
        url = reverse("hardware:heartbeat-create")
        self.assertEqual(url, "/api/hardware/heartbeats/")

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CameraHeartbeatCreateView)

    def test_heartbeat_list_url(self):
        """Testa URL de listagem de heartbeats"""
        url = reverse("hardware:heartbeat-list", kwargs={"camera_id": 123})
        self.assertEqual(url, "/api/hardware/cameras/123/heartbeats/")

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CameraHeartbeatListView)
        self.assertEqual(resolver.kwargs["camera_id"], 123)

    def test_slot_status_event_url(self):
        """Testa URL de eventos de status de slot"""
        url = reverse("hardware:slot-status-event")
        self.assertEqual(url, "/api/hardware/events/slot-status/")

        resolver = resolve(url)
        self.assertEqual(resolver.func, views.slot_status_event_view)

    def test_all_url_names_exist(self):
        """Testa que todos os nomes de URL existem"""
        url_names = [
            "api-key-list",
            "api-key-detail",
            "camera-list",
            "camera-detail",
            "heartbeat-create",
            "heartbeat-list",
            "slot-status-event",
        ]

        for name in url_names:
            with self.subTest(url_name=name):
                # Deve conseguir fazer reverse sem erro
                if name in ["api-key-detail", "camera-detail"]:
                    reverse(f"hardware:{name}", kwargs={"pk": 1})
                elif name == "heartbeat-list":
                    reverse(f"hardware:{name}", kwargs={"camera_id": 1})
                else:
                    reverse(f"hardware:{name}")
