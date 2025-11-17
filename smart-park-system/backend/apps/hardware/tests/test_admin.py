from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock, patch

from apps.hardware.admin import (
    ApiKeysAdmin,
    CamerasAdmin,
    CameraHeartbeatsAdmin,
    CameraHeartbeatsInline,
)
from apps.hardware.models import ApiKeys, Cameras, CameraHeartbeats
from .test_utils import TestDataMixin


class MockRequest:
    """Mock request para testes de admin"""

    def __init__(self, user=None):
        self.user = user


class CameraHeartbeatsInlineTest(TestCase, TestDataMixin):
    """Testes para CameraHeartbeatsInline"""

    def setUp(self):
        """Setup para cada teste"""
        self.site = AdminSite()
        self.inline = CameraHeartbeatsInline(Cameras, self.site)
        self.user = self.create_admin_user()
        self.request = MockRequest(user=self.user)

        self.client_obj = self.create_client()
        self.api_key = self.create_api_key(client=self.client_obj)
        self.camera = self.create_camera(client=self.client_obj, api_key=self.api_key)

    def test_payload_summary_with_long_payload(self):
        """Testa payload_summary com payload longo - cobre linhas 18-24"""
        heartbeat = self.create_camera_heartbeat(
            camera=self.camera,
            payload_json={
                "very_long_key": "very_long_value_that_exceeds_fifty_characters_limit"
            },
        )

        result = self.inline.payload_summary(heartbeat)
        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 53)  # 50 chars + "..."

    def test_payload_summary_with_short_payload(self):
        """Testa payload_summary com payload curto"""
        heartbeat = self.create_camera_heartbeat(
            camera=self.camera, payload_json={"status": "ok"}
        )

        result = self.inline.payload_summary(heartbeat)
        self.assertEqual(result, "{'status': 'ok'}")
        self.assertNotIn("...", result)

    def test_payload_summary_with_none_payload(self):
        """Testa payload_summary com payload None"""
        heartbeat = CameraHeartbeats.objects.create(
            camera=self.camera, payload_json=None
        )

        result = self.inline.payload_summary(heartbeat)
        self.assertEqual(result, "-")

    def test_get_queryset_limits_to_five(self):
        """Testa que get_queryset limita a 5 registros - cobre linha 29"""
        # Criar mais de 5 heartbeats para ter dados suficientes
        for i in range(7):
            self.create_camera_heartbeat(camera=self.camera)

        # Mockear o método parent get_queryset para retornar um queryset
        from unittest.mock import Mock, patch

        with patch.object(
            self.inline.__class__.__bases__[0], "get_queryset"
        ) as mock_parent:
            from apps.hardware.models import CameraHeartbeats

            mock_parent.return_value = CameraHeartbeats.objects.all()

            # Chamar o método que queremos testar
            result = self.inline.get_queryset(self.request)

            # Verificar que o slice [:5] foi aplicado
            result_list = list(result)
            self.assertEqual(len(result_list), 5)


class ApiKeysAdminTest(TestCase, TestDataMixin):
    """Testes para ApiKeysAdmin"""

    def setUp(self):
        """Setup para cada teste"""
        self.site = AdminSite()
        self.admin = ApiKeysAdmin(ApiKeys, self.site)
        self.factory = RequestFactory()
        self.user = self.create_admin_user()

        self.client_obj = self.create_client()
        self.api_key = self.create_api_key(
            client=self.client_obj, name="Test API Key", key_id="abcd1234efgh5678"
        )

    def test_get_queryset_annotates_cameras_count(self):
        """Testa que get_queryset adiciona annotação de contagem de câmeras - cobre linha 65"""
        request = self.factory.get("/")
        queryset = self.admin.get_queryset(request)

        # Verifica se a annotation foi adicionada
        api_key = queryset.get(id=self.api_key.id)
        self.assertTrue(hasattr(api_key, "cameras_count"))

    def test_key_id_masked_with_key(self):
        """Testa key_id_masked com chave presente - cobre linhas 68-70"""
        result = self.admin.key_id_masked(self.api_key)
        expected = f"{self.api_key.key_id[:8]}***{self.api_key.key_id[-4:]}"
        self.assertEqual(result, expected)

    def test_key_id_masked_without_key(self):
        """Testa key_id_masked sem chave"""
        api_key = ApiKeys(key_id=None)
        result = self.admin.key_id_masked(api_key)
        self.assertEqual(result, "-")

    def test_enabled_status_true(self):
        """Testa enabled_status quando habilitado - cobre linhas 75-77"""
        self.api_key.enabled = True
        result = self.admin.enabled_status(self.api_key)
        self.assertIn("color: green", result)
        self.assertIn("✓ Ativa", result)

    def test_enabled_status_false(self):
        """Testa enabled_status quando desabilitado"""
        self.api_key.enabled = False
        result = self.admin.enabled_status(self.api_key)
        self.assertIn("color: red", result)
        self.assertIn("✗ Inativa", result)

    def test_cameras_count_with_annotation(self):
        """Testa cameras_count com annotation - cobre linhas 82-91"""
        # Criar câmeras para a API key
        camera1 = self.create_camera(client=self.client_obj, api_key=self.api_key)
        camera2 = self.create_camera(client=self.client_obj, api_key=self.api_key)

        # Simular objeto com annotation
        self.api_key.cameras_count = 2

        result = self.admin.cameras_count(self.api_key)
        self.assertIn("2 câmeras", result)
        self.assertIn("href=", result)

    def test_cameras_count_without_annotation(self):
        """Testa cameras_count sem annotation"""
        # Criar câmeras para a API key
        camera1 = self.create_camera(client=self.client_obj, api_key=self.api_key)

        # Sem annotation, deve fazer query direta
        result = self.admin.cameras_count(self.api_key)
        self.assertIn("1 câmeras", result)

    def test_cameras_count_zero(self):
        """Testa cameras_count com zero câmeras"""
        self.api_key.cameras_count = 0
        result = self.admin.cameras_count(self.api_key)
        self.assertEqual(result, "0 câmeras")

    def test_enable_keys_action(self):
        """Testa ação enable_keys - cobre linhas 98-99"""
        request = self.factory.post("/")
        request.user = self.user
        request._messages = Mock()

        # Desabilitar a chave primeiro
        self.api_key.enabled = False
        self.api_key.save()

        queryset = ApiKeys.objects.filter(id=self.api_key.id)
        self.admin.enable_keys(request, queryset)

        # Verifica se foi habilitada
        self.api_key.refresh_from_db()
        self.assertTrue(self.api_key.enabled)

    def test_disable_keys_action(self):
        """Testa ação disable_keys - cobre linhas 104-105"""
        request = self.factory.post("/")
        request.user = self.user
        request._messages = Mock()

        # Habilitar a chave primeiro
        self.api_key.enabled = True
        self.api_key.save()

        queryset = ApiKeys.objects.filter(id=self.api_key.id)
        self.admin.disable_keys(request, queryset)

        # Verifica se foi desabilitada
        self.api_key.refresh_from_db()
        self.assertFalse(self.api_key.enabled)


class CamerasAdminTest(TestCase, TestDataMixin):
    """Testes para CamerasAdmin"""

    def setUp(self):
        """Setup para cada teste"""
        self.site = AdminSite()
        self.admin = CamerasAdmin(Cameras, self.site)
        self.factory = RequestFactory()
        self.user = self.create_admin_user()

        self.client_obj = self.create_client()
        self.api_key = self.create_api_key(client=self.client_obj)

        self.camera = self.create_camera(client=self.client_obj, api_key=self.api_key)

    def test_get_queryset_with_select_related_and_annotate(self):
        """Testa que get_queryset faz select_related e annotate - cobre linha 145"""
        request = self.factory.get("/")
        queryset = self.admin.get_queryset(request)

        camera = queryset.get(id=self.camera.id)
        # Verifica se a annotation foi adicionada
        self.assertTrue(hasattr(camera, "heartbeats_count"))

    def test_location_info_empty(self):
        """Testa location_info sem establishment e lot"""
        # Câmera sem establishment e lot (padrão do create_camera)
        result = self.admin.location_info(self.camera)
        self.assertEqual(result, "Não definido")

    def test_location_info_with_establishment_and_lot(self):
        """Testa location_info com establishment e lot - cobre linhas 155, 157"""
        # Criar objetos mock simples para testar as linhas
        from unittest.mock import Mock

        mock_establishment = Mock()
        mock_establishment.name = "Test Establishment"

        mock_lot = Mock()
        mock_lot.lot_code = "LOT001"

        mock_camera = Mock()
        mock_camera.establishment = mock_establishment
        mock_camera.lot = mock_lot

        result = self.admin.location_info(mock_camera)
        self.assertIn("Test Establishment", result)
        self.assertIn("Lote: LOT001", result)
        self.assertIn(" | ", result)

    def test_state_display_active(self):
        """Testa state_display para ACTIVE - cobre linhas 163-170"""
        self.camera.state = "ACTIVE"
        result = self.admin.state_display(self.camera)
        self.assertIn("color: green", result)

    def test_state_display_inactive(self):
        """Testa state_display para INACTIVE"""
        self.camera.state = "INACTIVE"
        result = self.admin.state_display(self.camera)
        self.assertIn("color: red", result)

    def test_state_display_maintenance(self):
        """Testa state_display para MAINTENANCE"""
        self.camera.state = "MAINTENANCE"
        result = self.admin.state_display(self.camera)
        self.assertIn("color: orange", result)

    def test_state_display_error(self):
        """Testa state_display para ERROR"""
        self.camera.state = "ERROR"
        result = self.admin.state_display(self.camera)
        self.assertIn("color: red", result)

    def test_state_display_unknown(self):
        """Testa state_display para estado desconhecido"""
        self.camera.state = "UNKNOWN"
        result = self.admin.state_display(self.camera)
        self.assertIn("color: gray", result)

    def test_last_heartbeat_online(self):
        """Testa last_heartbeat online (< 5 min) - cobre linhas 179-191"""
        # Definir last_seen_at há 2 minutos
        self.camera.last_seen_at = timezone.now() - timedelta(minutes=2)
        result = self.admin.last_heartbeat(self.camera)
        self.assertIn("color: green", result)
        self.assertIn("Online", result)

    def test_last_heartbeat_recent(self):
        """Testa last_heartbeat recente (< 1 hora)"""
        # Definir last_seen_at há 30 minutos
        self.camera.last_seen_at = timezone.now() - timedelta(minutes=30)
        result = self.admin.last_heartbeat(self.camera)
        self.assertIn("color: orange", result)
        self.assertIn("30 min atrás", result)

    def test_last_heartbeat_old(self):
        """Testa last_heartbeat antigo (> 1 hora)"""
        # Definir last_seen_at há 3 horas
        self.camera.last_seen_at = timezone.now() - timedelta(hours=3)
        result = self.admin.last_heartbeat(self.camera)
        self.assertIn("color: red", result)
        self.assertIn("3h atrás", result)

    def test_last_heartbeat_never(self):
        """Testa last_heartbeat quando nunca conectou"""
        self.camera.last_seen_at = None
        result = self.admin.last_heartbeat(self.camera)
        self.assertEqual(result, "Nunca conectada")

    def test_heartbeats_count_with_annotation(self):
        """Testa heartbeats_count com annotation - cobre linhas 196-207"""
        # Criar heartbeats
        heartbeat1 = self.create_camera_heartbeat(camera=self.camera)
        heartbeat2 = self.create_camera_heartbeat(camera=self.camera)

        # Simular annotation
        self.camera.heartbeats_count = 2

        result = self.admin.heartbeats_count(self.camera)
        self.assertIn("2", result)
        self.assertIn("href=", result)

    def test_heartbeats_count_without_annotation(self):
        """Testa heartbeats_count sem annotation"""
        heartbeat = self.create_camera_heartbeat(camera=self.camera)

        result = self.admin.heartbeats_count(self.camera)
        self.assertIn("1", result)

    def test_heartbeats_count_zero(self):
        """Testa heartbeats_count com zero"""
        self.camera.heartbeats_count = 0
        result = self.admin.heartbeats_count(self.camera)
        self.assertEqual(result, "0")

    def test_activate_cameras_action(self):
        """Testa ação activate_cameras - cobre linhas 214-215"""
        request = self.factory.post("/")
        request.user = self.user
        request._messages = Mock()

        self.camera.state = "INACTIVE"
        self.camera.save()

        queryset = Cameras.objects.filter(id=self.camera.id)
        self.admin.activate_cameras(request, queryset)

        self.camera.refresh_from_db()
        self.assertEqual(self.camera.state, "ACTIVE")

    def test_deactivate_cameras_action(self):
        """Testa ação deactivate_cameras - cobre linhas 220-221"""
        request = self.factory.post("/")
        request.user = self.user
        request._messages = Mock()

        self.camera.state = "ACTIVE"
        self.camera.save()

        queryset = Cameras.objects.filter(id=self.camera.id)
        self.admin.deactivate_cameras(request, queryset)

        self.camera.refresh_from_db()
        self.assertEqual(self.camera.state, "INACTIVE")

    def test_set_maintenance_action(self):
        """Testa ação set_maintenance - cobre linhas 226-227"""
        request = self.factory.post("/")
        request.user = self.user
        request._messages = Mock()

        self.camera.state = "ACTIVE"
        self.camera.save()

        queryset = Cameras.objects.filter(id=self.camera.id)
        self.admin.set_maintenance(request, queryset)

        self.camera.refresh_from_db()
        self.assertEqual(self.camera.state, "MAINTENANCE")


class CameraHeartbeatsAdminTest(TestCase, TestDataMixin):
    """Testes para CameraHeartbeatsAdmin"""

    def setUp(self):
        """Setup para cada teste"""
        self.site = AdminSite()
        self.admin = CameraHeartbeatsAdmin(CameraHeartbeats, self.site)
        self.factory = RequestFactory()

        self.client_obj = self.create_client()
        self.api_key = self.create_api_key(client=self.client_obj)
        self.camera = self.create_camera(
            client=self.client_obj, api_key=self.api_key, camera_code="CAM001"
        )
        self.heartbeat = self.create_camera_heartbeat(
            camera=self.camera, payload_json={"status": "online", "battery": 85}
        )

    def test_get_queryset_select_related(self):
        """Testa que get_queryset faz select_related - cobre linha 241"""
        request = self.factory.get("/")
        queryset = self.admin.get_queryset(request)

        # Verifica se consegue acessar campos relacionados sem queries adicionais
        heartbeat = queryset.get(id=self.heartbeat.id)
        # Acesso à camera.client deve estar pre-carregado
        client_name = heartbeat.camera.client.name
        self.assertEqual(client_name, self.client_obj.name)

    def test_camera_info(self):
        """Testa camera_info - cobre linha 244"""
        result = self.admin.camera_info(self.heartbeat)
        expected = f"{self.camera.camera_code} ({self.client_obj.name})"
        self.assertEqual(result, expected)

    def test_payload_preview_long(self):
        """Testa payload_preview com payload longo - cobre linhas 249-252"""
        long_payload = {"key": "x" * 120}  # Mais de 100 caracteres
        heartbeat = self.create_camera_heartbeat(
            camera=self.camera, payload_json=long_payload
        )

        result = self.admin.payload_preview(heartbeat)
        self.assertTrue(result.endswith("..."))
        self.assertLessEqual(len(result), 103)  # 100 chars + "..."

    def test_payload_preview_short(self):
        """Testa payload_preview com payload curto"""
        result = self.admin.payload_preview(self.heartbeat)
        self.assertNotIn("...", result)
        self.assertIn("status", result)

    def test_payload_preview_none(self):
        """Testa payload_preview com payload None"""
        heartbeat = CameraHeartbeats.objects.create(
            camera=self.camera, payload_json=None
        )

        result = self.admin.payload_preview(heartbeat)
        self.assertEqual(result, "-")

    def test_time_since_now(self):
        """Testa time_since para agora - cobre linhas 257-265"""
        # Heartbeat muito recente (< 1 minuto)
        recent_time = timezone.now() - timedelta(seconds=30)
        self.heartbeat.received_at = recent_time

        result = self.admin.time_since(self.heartbeat)
        self.assertEqual(result, "Agora")

    def test_time_since_minutes(self):
        """Testa time_since para minutos atrás"""
        # Heartbeat há 30 minutos
        time_30min = timezone.now() - timedelta(minutes=30)
        self.heartbeat.received_at = time_30min

        result = self.admin.time_since(self.heartbeat)
        self.assertIn("30 min atrás", result)

    def test_time_since_hours(self):
        """Testa time_since para horas atrás"""
        # Heartbeat há 5 horas
        time_5h = timezone.now() - timedelta(hours=5)
        self.heartbeat.received_at = time_5h

        result = self.admin.time_since(self.heartbeat)
        self.assertIn("5h atrás", result)

    def test_time_since_days(self):
        """Testa time_since para dias atrás"""
        # Heartbeat há 3 dias
        time_3d = timezone.now() - timedelta(days=3)
        self.heartbeat.received_at = time_3d

        result = self.admin.time_since(self.heartbeat)
        self.assertIn("3 dias atrás", result)
