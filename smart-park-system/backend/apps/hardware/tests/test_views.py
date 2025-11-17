from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from apps.hardware.models import ApiKeys, Cameras, CameraHeartbeats
from .test_utils import TestDataMixin


class ApiKeyViewsTest(TestCase, TestDataMixin):
    """Testes para views de API Keys"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.user = self.create_client_admin_user()
        self.client_obj = self.create_client()
        self.role = self.create_group(name="client_admin")
        self.member = self.create_client_member(
            client=self.client_obj, user=self.user, role=self.role
        )
        self.api_key = self.create_api_key(client=self.client_obj, name="Test API Key")

    def test_list_api_keys(self):
        """Testa listagem de API keys"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:api-key-list")
        response = self.client_api.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test API Key")

    @patch("secrets.token_urlsafe")
    @patch("hashlib.sha256")
    def test_create_api_key(self, mock_sha256, mock_token):
        """Testa criação de API key"""
        mock_token.side_effect = ["test_key_id", "test_secret"]
        mock_hash = mock_sha256.return_value
        mock_hash.hexdigest.return_value = "test_hash"

        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:api-key-list")
        data = {"name": "New API Key"}

        response = self.client_api.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New API Key")
        self.assertTrue(ApiKeys.objects.filter(name="New API Key").exists())

    def test_get_api_key_detail(self):
        """Testa busca de API key específica"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:api-key-detail", kwargs={"pk": self.api_key.pk})
        response = self.client_api.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test API Key")

    def test_update_api_key(self):
        """Testa atualização de API key"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:api-key-detail", kwargs={"pk": self.api_key.pk})
        data = {"name": "Updated API Key"}

        response = self.client_api.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated API Key")

    def test_delete_api_key(self):
        """Testa soft delete de API key"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:api-key-detail", kwargs={"pk": self.api_key.pk})
        response = self.client_api.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.api_key.refresh_from_db()
        self.assertTrue(self.api_key.is_deleted)

    def test_unauthorized_access(self):
        """Testa acesso sem autenticação"""
        url = reverse("hardware:api-key-list")
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CameraViewsTest(TestCase, TestDataMixin):
    """Testes para views de Cameras"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.user = self.create_client_admin_user()
        self.client_obj = self.create_client()
        self.role = self.create_group(name="client_admin")
        self.member = self.create_client_member(
            client=self.client_obj, user=self.user, role=self.role
        )
        self.api_key = self.create_api_key(client=self.client_obj)
        self.camera = self.create_camera(
            client=self.client_obj, api_key=self.api_key, camera_code="CAM001"
        )

    def test_list_cameras(self):
        """Testa listagem de câmeras"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:camera-list")
        response = self.client_api.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["camera_code"], "CAM001")

    def test_create_camera_invalid_data(self):
        """Testa criação de câmera com dados inválidos"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:camera-list")
        data = {"camera_code": ""}  # Empty code

        response = self.client_api.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_camera_detail(self):
        """Testa busca de câmera específica"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:camera-detail", kwargs={"pk": self.camera.pk})
        response = self.client_api.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["camera_code"], "CAM001")

    def test_update_camera(self):
        """Testa atualização de câmera"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:camera-detail", kwargs={"pk": self.camera.pk})
        data = {"state": "MAINTENANCE"}

        response = self.client_api.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["state"], "MAINTENANCE")

    def test_delete_camera(self):
        """Testa soft delete de câmera"""
        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:camera-detail", kwargs={"pk": self.camera.pk})
        response = self.client_api.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.camera.refresh_from_db()
        self.assertTrue(self.camera.is_deleted)


class HeartbeatViewsTest(TestCase, TestDataMixin):
    """Testes para views de Heartbeats"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.user = self.create_client_admin_user()
        self.client_obj = self.create_client()
        self.role = self.create_group(name="client_admin")
        self.member = self.create_client_member(
            client=self.client_obj, user=self.user, role=self.role
        )
        self.api_key = self.create_api_key(client=self.client_obj)
        self.camera = self.create_camera(client=self.client_obj, api_key=self.api_key)

    def test_create_heartbeat_with_valid_data(self):
        """Testa criação de heartbeat com dados válidos - cobre linhas 138-142"""
        # Authenticate as user who owns the camera to avoid AnonymousUser issue
        self.client_api.force_authenticate(user=self.user)

        url = reverse("hardware:heartbeat-create")
        data = {
            "camera_id": self.camera.id,
            "payload_json": {"status": "online", "battery": 90},
        }

        response = self.client_api.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["camera"], self.camera.id)
        self.assertEqual(response.data["payload_json"]["status"], "online")
        # Verifica se usa CameraHeartbeatSerializer (tem todos os campos)
        expected_fields = [
            "id",
            "public_id",
            "created_at",
            "updated_at",
            "is_deleted",
            "camera",
            "received_at",
            "payload_json",
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_create_heartbeat_missing_camera_id(self):
        """Testa criação de heartbeat sem camera_id"""
        url = reverse("hardware:heartbeat-create")
        data = {"payload_json": {"status": "online"}}

        response = self.client_api.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_heartbeat_invalid_camera(self):
        """Testa criação de heartbeat com câmera inválida"""
        url = reverse("hardware:heartbeat-create")
        data = {"camera_id": 99999, "payload_json": {"status": "online"}}

        response = self.client_api.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_heartbeats(self):
        """Testa listagem de heartbeats de uma câmera"""
        # Criar heartbeat
        heartbeat = self.create_camera_heartbeat(camera=self.camera)

        self.client_api.force_authenticate(user=self.user)
        url = reverse("hardware:heartbeat-list", kwargs={"camera_id": self.camera.id})
        response = self.client_api.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["camera"], self.camera.id)


class SlotStatusEventViewTest(TestCase, TestDataMixin):
    """Testes para slot_status_event_view"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.url = reverse("hardware:slot-status-event")

    def test_missing_required_fields(self):
        """Testa validação de campos obrigatórios"""
        # Sem slot_id
        data = {"status": "OCCUPIED"}
        response = self.client_api.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("slot_id e status são obrigatórios", response.data["error"])

        # Sem status
        data = {"slot_id": 1}
        response = self.client_api.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.hardware.views.get_object_or_404")
    @patch("apps.hardware.views.SlotStatus")
    @patch("apps.hardware.views.SlotStatusHistory")
    def test_successful_status_create(self, mock_history, mock_status, mock_get_slot):
        """Testa criação de novo status de slot"""
        # Mock básico
        from unittest.mock import Mock

        mock_slot = Mock()
        mock_slot.id = 1
        mock_get_slot.return_value = mock_slot

        mock_slot_status = Mock()
        mock_status.objects.get_or_create.return_value = (
            mock_slot_status,
            True,
        )  # created=True
        mock_history.objects.create.return_value = Mock()

        data = {"slot_id": 1, "status": "OCCUPIED"}

        response = self.client_api.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Status atualizado com sucesso")
        self.assertEqual(str(response.data["slot_id"]), "1")
        self.assertEqual(response.data["status"], "OCCUPIED")

    @patch("apps.hardware.views.get_object_or_404")
    @patch("apps.hardware.views.SlotStatus")
    @patch("apps.hardware.views.SlotStatusHistory")
    @patch("apps.hardware.views.timezone")
    def test_successful_status_update(
        self, mock_timezone, mock_history, mock_status, mock_get_slot
    ):
        """Testa atualização de status existente - cobre linhas 229-233"""
        # Mock básico
        from unittest.mock import Mock

        mock_slot = Mock()
        mock_slot.id = 1
        mock_get_slot.return_value = mock_slot

        mock_slot_status = Mock()
        mock_status.objects.get_or_create.return_value = (
            mock_slot_status,
            False,
        )  # created=False
        mock_history.objects.create.return_value = Mock()

        mock_now = Mock()
        mock_timezone.now.return_value = mock_now

        data = {
            "slot_id": 1,
            "status": "FREE",
            "vehicle_type_id": 2,
            "confidence": 0.85,
        }

        response = self.client_api.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verifica se os campos foram atualizados
        self.assertEqual(mock_slot_status.status, "FREE")
        self.assertEqual(mock_slot_status.vehicle_type_id, "2")  # String conversion
        self.assertEqual(mock_slot_status.confidence, "0.85")  # String conversion
        self.assertEqual(mock_slot_status.changed_at, mock_now)
        mock_slot_status.save.assert_called_once()

    @patch("apps.hardware.views.get_object_or_404")
    def test_nonexistent_slot(self, mock_get_slot):
        """Testa resposta para slot inexistente"""
        from django.http import Http404

        mock_get_slot.side_effect = Http404()

        data = {"slot_id": 99999, "status": "OCCUPIED"}
        response = self.client_api.post(self.url, data)
        # Should return 500 since Http404 is caught in exception handler
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ViewPermissionsTest(TestCase, TestDataMixin):
    """Testes de permissões das views"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.regular_user = self.create_app_user()
        self.admin_user = self.create_client_admin_user()

        self.client_obj = self.create_client()
        self.role = self.create_group(name="client_admin")
        self.member = self.create_client_member(
            client=self.client_obj, user=self.admin_user, role=self.role
        )
        self.api_key = self.create_api_key(client=self.client_obj)
        self.camera = self.create_camera(client=self.client_obj, api_key=self.api_key)

    def test_unauthenticated_access_denied(self):
        """Testa que usuários não autenticados não podem acessar endpoints protegidos"""
        protected_urls = [
            reverse("hardware:api-key-list"),
            reverse("hardware:camera-list"),
            reverse("hardware:heartbeat-list", kwargs={"camera_id": self.camera.id}),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client_api.get(url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_access_denied(self):
        """Testa que usuários regulares não podem acessar endpoints de cliente"""
        self.client_api.force_authenticate(user=self.regular_user)

        protected_urls = [
            reverse("hardware:api-key-list"),
            reverse("hardware:camera-list"),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client_api.get(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_access_granted(self):
        """Testa que usuários admin podem acessar endpoints"""
        self.client_api.force_authenticate(user=self.admin_user)

        # Pode acessar listagem
        response = self.client_api.get(reverse("hardware:api-key-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Pode acessar detalhes
        response = self.client_api.get(
            reverse("hardware:api-key-detail", kwargs={"pk": self.api_key.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_endpoints_allow_anonymous(self):
        """Testa que endpoints públicos permitem acesso anônimo"""
        public_urls = [
            reverse("hardware:heartbeat-create"),
            reverse("hardware:slot-status-event"),
        ]

        for url in public_urls:
            with self.subTest(url=url):
                response = self.client_api.post(url, {})
                # Não deve ser 401, mas pode ser 400 (bad request)
                self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ViewIntegrationTest(TestCase, TestDataMixin):
    """Teste de integração simples"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.user = self.create_client_admin_user()
        self.client_obj = self.create_client()
        self.role = self.create_group(name="client_admin")
        self.member = self.create_client_member(
            client=self.client_obj, user=self.user, role=self.role
        )

    @patch("secrets.token_urlsafe")
    @patch("hashlib.sha256")
    def test_hardware_workflow(self, mock_sha256, mock_token):
        """Testa fluxo básico: criar API key -> criar câmera -> enviar heartbeat"""
        mock_token.side_effect = ["test_key", "test_secret"]
        mock_hash = mock_sha256.return_value
        mock_hash.hexdigest.return_value = "test_hash"

        self.client_api.force_authenticate(user=self.user)

        # 1. Criar API key
        api_key_data = {"name": "Integration API Key"}
        response = self.client_api.post(reverse("hardware:api-key-list"), api_key_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2. Teste simples de listagem
        response = self.client_api.get(reverse("hardware:api-key-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que a API key foi criada
        self.assertTrue(ApiKeys.objects.filter(name="Integration API Key").exists())
