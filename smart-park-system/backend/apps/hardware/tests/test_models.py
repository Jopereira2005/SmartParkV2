from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from unittest.mock import patch

from apps.hardware.models import ApiKeys, Cameras, CameraHeartbeats
from .test_utils import TestDataMixin


class ApiKeysModelTest(TestCase, TestDataMixin):
    """Testes para o model ApiKeys"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()
        self.api_key_data = {
            "client": self.client,
            "name": "Test API Key",
            "key_id": "test_key_123",
            "hmac_secret_hash": "test_hash_value",
            "enabled": True,
        }

    def test_create_api_key(self):
        """Testa criação de API key"""
        api_key = ApiKeys.objects.create(**self.api_key_data)

        self.assertEqual(api_key.name, "Test API Key")
        self.assertEqual(api_key.key_id, "test_key_123")
        self.assertEqual(api_key.hmac_secret_hash, "test_hash_value")
        self.assertTrue(api_key.enabled)
        self.assertEqual(api_key.client, self.client)
        self.assertIsNotNone(api_key.public_id)
        self.assertIsNotNone(api_key.created_at)
        self.assertIsNotNone(api_key.updated_at)

    def test_api_key_str_method(self):
        """Testa método __str__ da API key"""
        api_key = ApiKeys.objects.create(**self.api_key_data)
        expected = f"Test API Key (test_key_123)"
        self.assertEqual(str(api_key), expected)

    def test_api_key_default_enabled(self):
        """Testa valor padrão do campo enabled"""
        api_key = ApiKeys.objects.create(
            client=self.client,
            name="Test Key",
            key_id="test_key",
            hmac_secret_hash="hash",
        )
        self.assertTrue(api_key.enabled)

    def test_api_key_unique_key_id(self):
        """Testa constraint de unicidade do key_id"""
        ApiKeys.objects.create(**self.api_key_data)

        # Tentar criar outra API key com mesmo key_id
        with self.assertRaises(IntegrityError):
            ApiKeys.objects.create(
                client=self.create_client(),
                name="Another Key",
                key_id="test_key_123",  # Mesmo key_id
                hmac_secret_hash="another_hash",
            )

    def test_api_key_name_max_length(self):
        """Testa validação de tamanho máximo do nome"""
        long_name = "a" * 101  # Excede o limite de 100
        with self.assertRaises(ValidationError):
            api_key = ApiKeys(
                client=self.client,
                name=long_name,
                key_id="test_key",
                hmac_secret_hash="hash",
            )
            api_key.full_clean()

    def test_api_key_key_id_max_length(self):
        """Testa validação de tamanho máximo do key_id"""
        long_key_id = "a" * 65  # Excede o limite de 64
        with self.assertRaises(ValidationError):
            api_key = ApiKeys(
                client=self.client,
                name="Test Key",
                key_id=long_key_id,
                hmac_secret_hash="hash",
            )
            api_key.full_clean()

    def test_api_key_soft_delete(self):
        """Testa soft delete da API key"""
        api_key = ApiKeys.objects.create(**self.api_key_data)
        self.assertFalse(api_key.is_deleted)

        api_key.soft_delete()
        self.assertTrue(api_key.is_deleted)
        self.assertIsNotNone(api_key.deleted_at)

        # Verifica que não aparece no queryset padrão
        self.assertNotIn(api_key, ApiKeys.objects.all())

        # Verifica que aparece no with_deleted
        self.assertIn(api_key, ApiKeys.objects.with_deleted())

    def test_api_key_restore(self):
        """Testa restore da API key"""
        api_key = ApiKeys.objects.create(**self.api_key_data)
        api_key.soft_delete()
        self.assertTrue(api_key.is_deleted)

        api_key.restore()
        self.assertFalse(api_key.is_deleted)
        self.assertIsNone(api_key.deleted_at)

        # Verifica que volta a aparecer no queryset padrão
        self.assertIn(api_key, ApiKeys.objects.all())


class CamerasModelTest(TestCase, TestDataMixin):
    """Testes para o model Cameras"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()
        self.api_key = self.create_api_key(client=self.client)
        self.camera_data = {
            "client": self.client,
            "camera_code": "CAM001",
            "api_key": self.api_key,
            "state": "ACTIVE",
        }

    def test_create_camera(self):
        """Testa criação de câmera"""
        camera = Cameras.objects.create(**self.camera_data)

        self.assertEqual(camera.camera_code, "CAM001")
        self.assertEqual(camera.api_key, self.api_key)
        self.assertEqual(camera.state, "ACTIVE")
        self.assertEqual(camera.client, self.client)
        self.assertIsNone(camera.establishment)
        self.assertIsNone(camera.lot)
        self.assertIsNone(camera.last_seen_at)
        self.assertIsNotNone(camera.public_id)
        self.assertIsNotNone(camera.created_at)

    def test_camera_str_method(self):
        """Testa método __str__ da câmera"""
        camera = Cameras.objects.create(**self.camera_data)
        expected = f"CAM001 - {self.client.name} (Ativa)"
        self.assertEqual(str(camera), expected)

    def test_camera_default_state(self):
        """Testa estado padrão da câmera"""
        camera = Cameras.objects.create(
            client=self.client, camera_code="CAM002", api_key=self.api_key
        )
        self.assertEqual(camera.state, "UNASSIGNED")

    def test_camera_state_choices(self):
        """Testa choices de estado da câmera"""
        states = [
            "UNASSIGNED",
            "ASSIGNED",
            "ACTIVE",
            "INACTIVE",
            "MAINTENANCE",
            "ERROR",
        ]

        for state in states:
            with self.subTest(state=state):
                camera = Cameras.objects.create(
                    client=self.client,
                    camera_code=f"CAM_{state}",
                    api_key=self.api_key,
                    state=state,
                )
                self.assertEqual(camera.state, state)

    def test_camera_unique_constraint(self):
        """Testa constraint de unicidade client-camera_code"""
        Cameras.objects.create(**self.camera_data)

        # Tentar criar outra câmera com mesmo client e camera_code
        with self.assertRaises(IntegrityError):
            Cameras.objects.create(
                client=self.client,
                camera_code="CAM001",  # Mesmo código
                api_key=self.create_api_key(client=self.client),
            )

    def test_camera_same_code_different_clients(self):
        """Testa que câmeras podem ter mesmo código em clientes diferentes"""
        Cameras.objects.create(**self.camera_data)

        # Criar câmera com mesmo código mas cliente diferente
        other_client = self.create_client()
        other_api_key = self.create_api_key(client=other_client)

        camera2 = Cameras.objects.create(
            client=other_client,
            camera_code="CAM001",  # Mesmo código
            api_key=other_api_key,
        )

        self.assertEqual(camera2.camera_code, "CAM001")
        self.assertNotEqual(camera2.client, self.client)

    def test_camera_camera_code_max_length(self):
        """Testa validação de tamanho máximo do camera_code"""
        long_code = "a" * 51  # Excede o limite de 50
        with self.assertRaises(ValidationError):
            camera = Cameras(
                client=self.client,
                camera_code=long_code,
                api_key=self.api_key,
            )
            camera.full_clean()

    def test_camera_soft_delete(self):
        """Testa soft delete da câmera"""
        camera = Cameras.objects.create(**self.camera_data)
        self.assertFalse(camera.is_deleted)

        camera.soft_delete()
        self.assertTrue(camera.is_deleted)
        self.assertIsNotNone(camera.deleted_at)

        # Verifica que não aparece no queryset padrão
        self.assertNotIn(camera, Cameras.objects.all())

        # Verifica que aparece no with_deleted
        self.assertIn(camera, Cameras.objects.with_deleted())

    def test_camera_protect_on_delete_api_key(self):
        """Testa proteção contra delete em cascata da API key"""
        camera = Cameras.objects.create(**self.camera_data)

        # Não deve permitir deletar api_key se existem câmeras
        with self.assertRaises(Exception):  # ProtectedError
            self.api_key.delete()

    def test_camera_with_establishment_and_lot(self):
        """Testa câmera com establishment e lot (se existirem)"""
        # Apenas testa que os campos podem ser None
        camera = Cameras.objects.create(**self.camera_data)
        self.assertIsNone(camera.establishment)
        self.assertIsNone(camera.lot)

        # Teste com last_seen_at
        now = timezone.now()
        camera.last_seen_at = now
        camera.save()
        camera.refresh_from_db()
        self.assertEqual(camera.last_seen_at, now)


class CameraHeartbeatsModelTest(TestCase, TestDataMixin):
    """Testes para o model CameraHeartbeats"""

    def setUp(self):
        """Setup para cada teste"""
        self.camera = self.create_camera()
        self.heartbeat_data = {
            "camera": self.camera,
            "payload_json": {"status": "ok", "timestamp": "2023-01-01T00:00:00Z"},
        }

    def test_create_camera_heartbeat(self):
        """Testa criação de heartbeat de câmera"""
        heartbeat = CameraHeartbeats.objects.create(**self.heartbeat_data)

        self.assertEqual(heartbeat.camera, self.camera)
        self.assertEqual(heartbeat.payload_json["status"], "ok")
        self.assertIsNotNone(heartbeat.received_at)
        self.assertIsNotNone(heartbeat.public_id)
        self.assertIsNotNone(heartbeat.created_at)

    def test_heartbeat_str_method(self):
        """Testa método __str__ do heartbeat"""
        heartbeat = CameraHeartbeats.objects.create(**self.heartbeat_data)
        expected = f"Heartbeat {self.camera.camera_code} - {heartbeat.received_at}"
        self.assertEqual(str(heartbeat), expected)

    def test_heartbeat_received_at_auto_add(self):
        """Testa que received_at é definido automaticamente"""
        before_creation = timezone.now()
        heartbeat = CameraHeartbeats.objects.create(**self.heartbeat_data)
        after_creation = timezone.now()

        self.assertGreaterEqual(heartbeat.received_at, before_creation)
        self.assertLessEqual(heartbeat.received_at, after_creation)

    def test_heartbeat_payload_json_optional(self):
        """Testa que payload_json é opcional"""
        heartbeat = CameraHeartbeats.objects.create(camera=self.camera)
        self.assertIsNone(heartbeat.payload_json)

    def test_heartbeat_payload_json_structure(self):
        """Testa diferentes estruturas de payload_json"""
        payloads = [
            {"status": "ok"},
            {"temperature": 25.5, "humidity": 60},
            {"errors": ["connection_timeout"], "status": "error"},
            None,
        ]

        for payload in payloads:
            with self.subTest(payload=payload):
                heartbeat = CameraHeartbeats.objects.create(
                    camera=self.camera, payload_json=payload
                )
                self.assertEqual(heartbeat.payload_json, payload)

    def test_heartbeat_soft_delete(self):
        """Testa soft delete do heartbeat"""
        heartbeat = CameraHeartbeats.objects.create(**self.heartbeat_data)
        self.assertFalse(heartbeat.is_deleted)

        heartbeat.soft_delete()
        self.assertTrue(heartbeat.is_deleted)
        self.assertIsNotNone(heartbeat.deleted_at)

        # Verifica que não aparece no queryset padrão
        self.assertNotIn(heartbeat, CameraHeartbeats.objects.all())

        # Verifica que aparece no with_deleted
        self.assertIn(heartbeat, CameraHeartbeats.objects.with_deleted())

    def test_heartbeat_protect_on_delete_camera(self):
        """Testa proteção contra delete em cascata da câmera"""
        heartbeat = CameraHeartbeats.objects.create(**self.heartbeat_data)

        # Não deve permitir deletar camera se existem heartbeats
        with self.assertRaises(Exception):  # ProtectedError
            self.camera.delete()

    def test_heartbeat_multiple_for_same_camera(self):
        """Testa múltiplos heartbeats para a mesma câmera"""
        heartbeat1 = CameraHeartbeats.objects.create(
            camera=self.camera, payload_json={"seq": 1}
        )
        heartbeat2 = CameraHeartbeats.objects.create(
            camera=self.camera, payload_json={"seq": 2}
        )

        self.assertEqual(heartbeat1.camera, heartbeat2.camera)
        self.assertNotEqual(heartbeat1.id, heartbeat2.id)
        self.assertEqual(CameraHeartbeats.objects.filter(camera=self.camera).count(), 2)


class TenantManagerTest(TestCase, TestDataMixin):
    """Testes para o TenantManager usado nos models hardware"""

    def test_tenant_manager_for_user(self):
        """Testa que TenantManager filtra por usuário"""
        # Criar clientes separados para este teste
        client1 = self.create_client(name="Client Test 1")
        client2 = self.create_client(name="Client Test 2")

        # Criar API keys e câmeras para cada cliente
        api_key1 = self.create_api_key(client=client1, name="Key Test 1")
        api_key2 = self.create_api_key(client=client2, name="Key Test 2")

        camera1 = self.create_camera(
            client=client1, api_key=api_key1, camera_code="CAMTEST1"
        )
        camera2 = self.create_camera(
            client=client2, api_key=api_key2, camera_code="CAMTEST2"
        )

        # Criar usuários e memberships
        user1 = self.create_user()
        user2 = self.create_user()
        role = self.create_group()

        # Associar user1 com client1
        self.create_client_member(client=client1, user=user1, role=role)

        # Associar user2 com client2
        self.create_client_member(client=client2, user=user2, role=role)

        # Teste filtro para user1 (deve ver apenas client1)
        api_keys_user1 = ApiKeys.objects.for_user(user1)
        cameras_user1 = Cameras.objects.for_user(user1)

        self.assertEqual(api_keys_user1.count(), 1)
        self.assertEqual(cameras_user1.count(), 1)
        self.assertEqual(api_keys_user1.first().client, client1)
        self.assertEqual(cameras_user1.first().client, client1)

        # Teste filtro para user2 (deve ver apenas client2)
        api_keys_user2 = ApiKeys.objects.for_user(user2)
        cameras_user2 = Cameras.objects.for_user(user2)

        self.assertEqual(api_keys_user2.count(), 1)
        self.assertEqual(cameras_user2.count(), 1)
        self.assertEqual(api_keys_user2.first().client, client2)
        self.assertEqual(cameras_user2.first().client, client2)

    def test_soft_delete_manager_methods(self):
        """Testa métodos específicos do SoftDeleteManager"""
        camera = self.create_camera()
        heartbeat1 = self.create_camera_heartbeat(camera=camera)
        heartbeat2 = self.create_camera_heartbeat(camera=camera)
        heartbeat3 = self.create_camera_heartbeat(camera=camera)

        # Soft delete alguns heartbeats
        heartbeat2.soft_delete()
        heartbeat3.soft_delete()

        # Teste queryset padrão (exclui deletados)
        active_heartbeats = CameraHeartbeats.objects.all()
        self.assertEqual(active_heartbeats.count(), 1)
        self.assertIn(heartbeat1, active_heartbeats)

        # Teste with_deleted (inclui todos)
        all_heartbeats = CameraHeartbeats.objects.with_deleted()
        self.assertEqual(all_heartbeats.count(), 3)
        self.assertIn(heartbeat1, all_heartbeats)
        self.assertIn(heartbeat2, all_heartbeats)
        self.assertIn(heartbeat3, all_heartbeats)

        # Teste only_deleted (apenas deletados)
        deleted_heartbeats = CameraHeartbeats.objects.only_deleted()
        self.assertEqual(deleted_heartbeats.count(), 2)
        self.assertNotIn(heartbeat1, deleted_heartbeats)
        self.assertIn(heartbeat2, deleted_heartbeats)
        self.assertIn(heartbeat3, deleted_heartbeats)


class ModelIntegrationTest(TestCase, TestDataMixin):
    """Testes de integração entre os models"""

    def test_complete_hardware_setup(self):
        """Testa configuração completa de hardware"""
        # Criar cliente
        client = self.create_client(name="Test Client")

        # Criar API key
        api_key = self.create_api_key(client=client, name="Main API Key")

        # Criar câmera
        camera = self.create_camera(
            client=client, api_key=api_key, camera_code="CAM_MAIN", state="ACTIVE"
        )

        # Criar heartbeats
        heartbeat1 = self.create_camera_heartbeat(
            camera=camera, payload_json={"status": "online", "battery": 85}
        )
        heartbeat2 = self.create_camera_heartbeat(
            camera=camera, payload_json={"status": "online", "battery": 84}
        )

        # Verificar relacionamentos
        self.assertEqual(camera.client, client)
        self.assertEqual(camera.api_key, api_key)
        self.assertEqual(api_key.cameras.count(), 1)
        self.assertEqual(camera.heartbeats.count(), 2)

        # Verificar dados
        self.assertIn(camera, api_key.cameras.all())
        self.assertIn(heartbeat1, camera.heartbeats.all())
        self.assertIn(heartbeat2, camera.heartbeats.all())

    def test_cascade_protection(self):
        """Testa proteção contra deleção em cascata"""
        client = self.create_client()
        api_key = self.create_api_key(client=client)
        camera = self.create_camera(client=client, api_key=api_key)
        heartbeat = self.create_camera_heartbeat(camera=camera)

        # Tentar deletar api_key (deve falhar por causa da câmera)
        with self.assertRaises(Exception):  # ProtectedError
            api_key.delete()

        # Tentar deletar camera (deve falhar por causa do heartbeat)
        with self.assertRaises(Exception):  # ProtectedError
            camera.delete()

        # Deletar heartbeat primeiro, depois camera, depois api_key
        heartbeat.delete()
        camera.delete()
        api_key.delete()

        # Verificar que foram deletados
        self.assertFalse(CameraHeartbeats.objects.filter(id=heartbeat.id).exists())
        self.assertFalse(Cameras.objects.filter(id=camera.id).exists())
        self.assertFalse(ApiKeys.objects.filter(id=api_key.id).exists())
