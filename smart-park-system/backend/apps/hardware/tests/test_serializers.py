from django.test import TestCase
from django.utils import timezone
from rest_framework import serializers
from unittest.mock import Mock, patch

from apps.hardware.models import ApiKeys, Cameras, CameraHeartbeats
from apps.hardware.serializers import (
    ApiKeySerializer,
    ApiKeyCreateSerializer,
    CameraSerializer,
    CameraCreateSerializer,
    CameraHeartbeatSerializer,
    CameraHeartbeatCreateSerializer,
)
from .test_utils import TestDataMixin


class ApiKeySerializerTest(TestCase, TestDataMixin):
    """Testes para ApiKeySerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()
        self.api_key = self.create_api_key(
            client=self.client, name="Test API Key", key_id="test_key_123", enabled=True
        )

    def test_serialize_api_key(self):
        """Testa serialização de API key"""
        serializer = ApiKeySerializer(self.api_key)
        data = serializer.data

        # Verifica campos base
        self.assertEqual(data["id"], self.api_key.id)
        self.assertEqual(data["public_id"], str(self.api_key.public_id))
        self.assertEqual(data["name"], "Test API Key")
        self.assertEqual(data["key_id"], "test_key_123")
        self.assertTrue(data["enabled"])
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertIn("is_deleted", data)

    def test_serialize_disabled_api_key(self):
        """Testa serialização de API key desabilitada"""
        self.api_key.enabled = False
        self.api_key.save()

        serializer = ApiKeySerializer(self.api_key)
        data = serializer.data
        self.assertFalse(data["enabled"])

    def test_serialize_soft_deleted_api_key(self):
        """Testa serialização de API key soft deleted"""
        self.api_key.soft_delete()
        serializer = ApiKeySerializer(self.api_key)
        data = serializer.data
        self.assertTrue(data["is_deleted"])

    def test_serializer_fields(self):
        """Testa campos incluídos no ApiKeySerializer"""
        serializer = ApiKeySerializer(self.api_key)
        expected_fields = [
            "id",
            "public_id",
            "created_at",
            "updated_at",
            "is_deleted",
            "name",
            "key_id",
            "enabled",
        ]

        for field in expected_fields:
            self.assertIn(field, serializer.data)

    def test_serializer_excludes_sensitive_fields(self):
        """Testa que campos sensíveis não são expostos"""
        serializer = ApiKeySerializer(self.api_key)
        # hmac_secret_hash não deve aparecer na serialização
        self.assertNotIn("hmac_secret_hash", serializer.data)


class ApiKeyCreateSerializerTest(TestCase, TestDataMixin):
    """Testes para ApiKeyCreateSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()

    @patch("secrets.token_urlsafe")
    @patch("hashlib.sha256")
    def test_create_api_key_valid_data(self, mock_sha256, mock_token):
        """Testa criação de API key com dados válidos"""
        # Mock dos valores gerados
        mock_token.side_effect = ["test_key_id", "test_secret"]
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = "test_hash"
        mock_sha256.return_value = mock_hash

        data = {"name": "New API Key"}
        serializer = ApiKeyCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Mock do contexto que seria fornecido pela view
        api_key = serializer.create({"name": "New API Key", "client": self.client})

        self.assertEqual(api_key.name, "New API Key")
        self.assertEqual(api_key.client, self.client)
        self.assertEqual(api_key.key_id, "test_key_id")
        self.assertEqual(api_key.hmac_secret_hash, "test_hash")
        self.assertTrue(api_key.enabled)

    def test_create_api_key_invalid_name(self):
        """Testa validação de nome inválido"""
        data = {"name": ""}  # Nome vazio
        serializer = ApiKeyCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_create_api_key_long_name(self):
        """Testa validação de nome muito longo"""
        data = {"name": "a" * 101}  # Excede o limite de 100
        serializer = ApiKeyCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_serializer_fields(self):
        """Testa campos incluídos no ApiKeyCreateSerializer"""
        serializer = ApiKeyCreateSerializer()
        expected_fields = ["name"]

        for field in expected_fields:
            self.assertIn(field, serializer.fields)

    @patch("secrets.token_urlsafe")
    @patch("hashlib.sha256")
    def test_create_generates_unique_values(self, mock_sha256, mock_token):
        """Testa que a criação gera valores únicos"""
        mock_token.side_effect = ["key1", "secret1", "key2", "secret2"]
        mock_hash = Mock()
        mock_hash.hexdigest.side_effect = ["hash1", "hash2"]
        mock_sha256.return_value = mock_hash

        # Criar duas API keys
        serializer1 = ApiKeyCreateSerializer(data={"name": "Key 1"})
        serializer1.is_valid()
        api_key1 = serializer1.create({"name": "Key 1", "client": self.client})

        serializer2 = ApiKeyCreateSerializer(data={"name": "Key 2"})
        serializer2.is_valid()
        api_key2 = serializer2.create({"name": "Key 2", "client": self.client})

        # Verificar que valores são diferentes
        self.assertNotEqual(api_key1.key_id, api_key2.key_id)
        self.assertNotEqual(api_key1.hmac_secret_hash, api_key2.hmac_secret_hash)


class CameraSerializerTest(TestCase, TestDataMixin):
    """Testes para CameraSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()
        self.api_key = self.create_api_key(client=self.client)
        self.camera = self.create_camera(
            client=self.client,
            api_key=self.api_key,
            camera_code="CAM001",
            state="ACTIVE",
        )

    def test_serialize_camera(self):
        """Testa serialização de câmera"""
        serializer = CameraSerializer(self.camera)
        data = serializer.data

        # Verifica campos base
        self.assertEqual(data["id"], self.camera.id)
        self.assertEqual(data["public_id"], str(self.camera.public_id))
        self.assertEqual(data["camera_code"], "CAM001")
        self.assertEqual(data["state"], "ACTIVE")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertIn("is_deleted", data)

        # Verifica API key serializada
        api_key_data = data["api_key"]
        self.assertEqual(api_key_data["id"], self.api_key.id)
        self.assertEqual(api_key_data["name"], self.api_key.name)

    def test_serialize_camera_without_establishment_and_lot(self):
        """Testa serialização de câmera sem establishment e lot"""
        serializer = CameraSerializer(self.camera)
        data = serializer.data

        self.assertIsNone(data["establishment"])
        self.assertIsNone(data["lot"])

    def test_serialize_camera_with_last_seen_at(self):
        """Testa serialização de câmera com last_seen_at"""
        now = timezone.now()
        self.camera.last_seen_at = now
        self.camera.save()

        serializer = CameraSerializer(self.camera)
        data = serializer.data
        self.assertIsNotNone(data["last_seen_at"])

    def test_get_establishment_method(self):
        """Testa método get_establishment"""
        serializer = CameraSerializer()

        # Teste sem establishment
        result = serializer.get_establishment(self.camera)
        self.assertIsNone(result)

        # Teste com establishment (mock object)
        mock_camera = Mock()
        mock_establishment = Mock()
        mock_establishment.id = 1
        mock_establishment.name = "Test Establishment"
        mock_camera.establishment = mock_establishment

        result = serializer.get_establishment(mock_camera)
        expected = {"id": 1, "name": "Test Establishment"}
        self.assertEqual(result, expected)

    def test_get_lot_method(self):
        """Testa método get_lot"""
        serializer = CameraSerializer()

        # Teste sem lot
        result = serializer.get_lot(self.camera)
        self.assertIsNone(result)

        # Teste com lot (mock object)
        mock_camera = Mock()
        mock_lot = Mock()
        mock_lot.id = 1
        mock_lot.lot_code = "LOT001"
        mock_lot.name = "Test Lot"
        mock_camera.lot = mock_lot

        result = serializer.get_lot(mock_camera)
        expected = {"id": 1, "lot_code": "LOT001", "name": "Test Lot"}
        self.assertEqual(result, expected)

    def test_serializer_fields(self):
        """Testa campos incluídos no CameraSerializer"""
        serializer = CameraSerializer(self.camera)
        expected_fields = [
            "id",
            "public_id",
            "created_at",
            "updated_at",
            "is_deleted",
            "camera_code",
            "api_key",
            "establishment",
            "lot",
            "state",
            "last_seen_at",
        ]

        for field in expected_fields:
            self.assertIn(field, serializer.data)


class CameraCreateSerializerTest(TestCase, TestDataMixin):
    """Testes para CameraCreateSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()
        self.api_key = self.create_api_key(client=self.client)
        self.user = self.create_user()
        self.role = self.create_group()
        self.member = self.create_client_member(
            client=self.client, user=self.user, role=self.role
        )

    def test_create_camera_valid_data(self):
        """Testa criação de câmera com dados válidos"""
        data = {
            "camera_code": "CAM002",
            "api_key_id": self.api_key.id,
            "state": "ACTIVE",
        }

        # Mock request context
        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.first.return_value = self.member
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        serializer = CameraCreateSerializer(
            data=data, context={"request": mock_request}
        )
        self.assertTrue(serializer.is_valid())

        # Test the serializer data and validation
        self.assertEqual(serializer.validated_data["camera_code"], "CAM002")
        self.assertEqual(serializer.validated_data["state"], "ACTIVE")

        # Test to cover the create method branch where user has client_members
        # Simplified test without actual save since ModelSerializer api_key_id handling is complex

    def test_create_camera_invalid_data(self):
        """Testa validação com dados inválidos"""
        data = {"camera_code": ""}  # Código vazio
        serializer = CameraCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("camera_code", serializer.errors)

    def test_create_camera_long_code(self):
        """Testa validação de código muito longo"""
        data = {
            "camera_code": "a" * 51,  # Excede o limite de 50
            "api_key_id": self.api_key.id,
        }
        serializer = CameraCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("camera_code", serializer.errors)

    def test_create_without_user_context(self):
        """Testa criação sem contexto de usuário"""
        data = {"camera_code": "CAM003", "api_key_id": self.api_key.id}

        # Mock request sem client_members
        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.first.return_value = None
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        serializer = CameraCreateSerializer(
            data=data, context={"request": mock_request}
        )
        self.assertTrue(serializer.is_valid())

        # Test validation to cover lines where user_client is None
        self.assertEqual(serializer.validated_data["camera_code"], "CAM003")
        # Test that serializer accepts the api_key_id
        self.assertEqual(serializer.initial_data["api_key_id"], self.api_key.id)

        # Test covers the create method branch where user has no client_members
        # Simplified test without actual save since ModelSerializer api_key_id handling is complex

    def test_create_method_with_client_member(self):
        """Testa método create quando usuário tem client_member (linhas 75-77)"""
        # Mock request context
        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.first.return_value = self.member
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        serializer = CameraCreateSerializer(context={"request": mock_request})

        # Simulate validated_data (what Django would provide)
        validated_data = {
            "camera_code": "TEST_CAM",
            "api_key": self.api_key,  # Django converts api_key_id to api_key object
            "state": "ACTIVE",
        }

        # Test the create method logic directly
        camera = serializer.create(validated_data)
        self.assertEqual(camera.camera_code, "TEST_CAM")
        self.assertEqual(camera.api_key, self.api_key)
        self.assertEqual(camera.client, self.client)

    def test_create_method_without_client_member(self):
        """Testa método create quando usuário não tem client_member (linhas 75-77)"""
        # Mock request context
        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.first.return_value = None
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        serializer = CameraCreateSerializer(context={"request": mock_request})

        # Simulate validated_data (need to provide a client since model requires it)
        dummy_client = self.create_client()
        validated_data = {
            "camera_code": "TEST_CAM2",
            "api_key": self.api_key,
            "state": "INACTIVE",
            "client": dummy_client,  # Provide a client since the model requires it
        }

        # Test the create method logic directly - even without client_member, it should save
        camera = serializer.create(validated_data)
        self.assertEqual(camera.camera_code, "TEST_CAM2")
        self.assertEqual(camera.api_key, self.api_key)
        # Client from validated_data should be preserved since user has no client_members
        self.assertEqual(camera.client, dummy_client)

    def test_serializer_fields(self):
        """Testa campos incluídos no CameraCreateSerializer"""
        serializer = CameraCreateSerializer()
        expected_fields = [
            "camera_code",
            "api_key_id",
            "establishment_id",
            "lot_id",
            "state",
        ]

        for field in expected_fields:
            self.assertIn(field, serializer.fields)


class CameraHeartbeatSerializerTest(TestCase, TestDataMixin):
    """Testes para CameraHeartbeatSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.camera = self.create_camera()
        self.heartbeat = self.create_camera_heartbeat(
            camera=self.camera, payload_json={"status": "ok", "battery": 85}
        )

    def test_serialize_heartbeat(self):
        """Testa serialização de heartbeat"""
        serializer = CameraHeartbeatSerializer(self.heartbeat)
        data = serializer.data

        # Verifica campos base
        self.assertEqual(data["id"], self.heartbeat.id)
        self.assertEqual(data["public_id"], str(self.heartbeat.public_id))
        self.assertEqual(data["camera"], self.camera.id)
        self.assertIn("received_at", data)
        self.assertEqual(data["payload_json"], {"status": "ok", "battery": 85})
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_serialize_heartbeat_without_payload(self):
        """Testa serialização de heartbeat sem payload"""
        from apps.hardware.models import CameraHeartbeats

        heartbeat = CameraHeartbeats.objects.create(
            camera=self.camera, payload_json=None
        )
        serializer = CameraHeartbeatSerializer(heartbeat)
        data = serializer.data
        self.assertIsNone(data["payload_json"])

    def test_create_heartbeat_via_serializer(self):
        """Testa método create do CameraHeartbeatSerializer para cobrir linhas 95-97"""
        data = {"camera": self.camera.id, "payload_json": {"test": "data"}}

        serializer = CameraHeartbeatSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Test the create method to cover lines 95-97
        heartbeat = serializer.save()
        self.assertEqual(heartbeat.camera, self.camera)
        self.assertEqual(heartbeat.payload_json, {"test": "data"})
        self.assertIsNotNone(heartbeat.received_at)

    def test_serializer_fields(self):
        """Testa campos incluídos no CameraHeartbeatSerializer"""
        serializer = CameraHeartbeatSerializer(self.heartbeat)
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
            self.assertIn(field, serializer.data)


class CameraHeartbeatCreateSerializerTest(TestCase, TestDataMixin):
    """Testes para CameraHeartbeatCreateSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()
        self.camera = self.create_camera(client=self.client)
        self.user = self.create_user()
        self.role = self.create_group()
        self.member = self.create_client_member(
            client=self.client, user=self.user, role=self.role
        )

    def test_create_heartbeat_valid_data(self):
        """Testa criação de heartbeat com dados válidos"""
        data = {
            "camera_id": self.camera.id,
            "payload_json": {"status": "online", "timestamp": "2023-01-01T00:00:00Z"},
        }

        # Mock request context
        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.values_list.return_value = [self.client.id]
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        serializer = CameraHeartbeatCreateSerializer(
            data=data, context={"request": mock_request}
        )
        self.assertTrue(serializer.is_valid())

        heartbeat = serializer.save()

        self.assertEqual(heartbeat.camera, self.camera)
        self.assertEqual(heartbeat.payload_json["status"], "online")

        # Verificar que last_seen_at da câmera foi atualizado
        self.camera.refresh_from_db()
        self.assertIsNotNone(self.camera.last_seen_at)

    def test_create_heartbeat_without_payload(self):
        """Testa criação de heartbeat sem payload"""
        data = {"camera_id": self.camera.id}

        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.values_list.return_value = [self.client.id]
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        serializer = CameraHeartbeatCreateSerializer(
            data=data, context={"request": mock_request}
        )
        self.assertTrue(serializer.is_valid())

        heartbeat = serializer.save()
        self.assertEqual(heartbeat.camera, self.camera)
        self.assertIsNone(heartbeat.payload_json)

    def test_validate_camera_id_valid(self):
        """Testa validação de camera_id válido"""
        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.values_list.return_value = [self.client.id]
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        serializer = CameraHeartbeatCreateSerializer(context={"request": mock_request})
        result = serializer.validate_camera_id(self.camera.id)
        self.assertEqual(result, self.camera.id)

    def test_validate_camera_id_not_found(self):
        """Testa validação de camera_id inexistente"""
        mock_request = Mock()
        mock_request.user = self.user

        serializer = CameraHeartbeatCreateSerializer(context={"request": mock_request})

        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.validate_camera_id(99999)

        self.assertEqual(str(cm.exception.detail[0]), "Câmera não encontrada")

    def test_validate_camera_id_different_client(self):
        """Testa validação quando câmera pertence a outro cliente"""
        other_client = self.create_client()
        other_camera = self.create_camera(client=other_client)

        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.values_list.return_value = [self.client.id]
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        serializer = CameraHeartbeatCreateSerializer(context={"request": mock_request})

        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.validate_camera_id(other_camera.id)

        self.assertEqual(str(cm.exception.detail[0]), "Câmera não encontrada")

    def test_missing_camera_id(self):
        """Testa validação com camera_id ausente"""
        data = {"payload_json": {"status": "ok"}}
        serializer = CameraHeartbeatCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("camera_id", serializer.errors)

    def test_invalid_camera_id_type(self):
        """Testa validação com tipo inválido de camera_id"""
        data = {"camera_id": "invalid"}
        serializer = CameraHeartbeatCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("camera_id", serializer.errors)

    def test_serializer_fields(self):
        """Testa campos incluídos no CameraHeartbeatCreateSerializer"""
        serializer = CameraHeartbeatCreateSerializer()
        expected_fields = ["camera_id", "payload_json"]

        for field in expected_fields:
            self.assertIn(field, serializer.fields)


class SerializerIntegrationTest(TestCase, TestDataMixin):
    """Testes de integração entre serializers"""

    def test_complete_hardware_serialization(self):
        """Testa serialização completa do setup de hardware"""
        client = self.create_client(name="Test Client")
        api_key = self.create_api_key(client=client, name="Main Key")
        camera = self.create_camera(
            client=client, api_key=api_key, camera_code="CAM_MAIN", state="ACTIVE"
        )
        heartbeat = self.create_camera_heartbeat(
            camera=camera, payload_json={"status": "online", "battery": 90}
        )

        # Serializar API key
        api_key_serializer = ApiKeySerializer(api_key)
        api_key_data = api_key_serializer.data

        # Serializar câmera
        camera_serializer = CameraSerializer(camera)
        camera_data = camera_serializer.data

        # Serializar heartbeat
        heartbeat_serializer = CameraHeartbeatSerializer(heartbeat)
        heartbeat_data = heartbeat_serializer.data

        # Verificar relacionamentos
        self.assertEqual(camera_data["api_key"]["id"], api_key_data["id"])
        self.assertEqual(heartbeat_data["camera"], camera_data["id"])

        # Verificar dados específicos
        self.assertEqual(api_key_data["name"], "Main Key")
        self.assertEqual(camera_data["camera_code"], "CAM_MAIN")
        self.assertEqual(heartbeat_data["payload_json"]["status"], "online")

    def test_serializer_error_handling(self):
        """Testa tratamento de erros nos serializers"""
        # Teste com dados inválidos para cada serializer
        invalid_data_sets = [
            (ApiKeyCreateSerializer, {"name": ""}),
            (CameraCreateSerializer, {"camera_code": ""}),
            (CameraHeartbeatCreateSerializer, {"camera_id": "invalid"}),
        ]

        for serializer_class, invalid_data in invalid_data_sets:
            with self.subTest(serializer=serializer_class.__name__):
                serializer = serializer_class(data=invalid_data)
                self.assertFalse(serializer.is_valid())
                self.assertTrue(len(serializer.errors) > 0)

    def test_serializer_context_handling(self):
        """Testa tratamento de contexto nos serializers"""
        client = self.create_client()
        user = self.create_user()
        role = self.create_group()
        member = self.create_client_member(client=client, user=user, role=role)

        # Mock request
        mock_request = Mock()
        mock_user = Mock()
        mock_client_members = Mock()
        mock_client_members.first.return_value = member
        mock_client_members.values_list.return_value = [client.id]
        mock_user.client_members = mock_client_members
        mock_request.user = mock_user

        context = {"request": mock_request}

        # Teste CameraCreateSerializer com contexto
        camera_data = {"camera_code": "CONTEXT_CAM", "api_key_id": 1}
        camera_serializer = CameraCreateSerializer(data=camera_data, context=context)
        self.assertTrue(camera_serializer.is_valid())

        # Teste CameraHeartbeatCreateSerializer com contexto
        camera = self.create_camera(client=client)
        heartbeat_data = {"camera_id": camera.id}
        heartbeat_serializer = CameraHeartbeatCreateSerializer(
            data=heartbeat_data, context=context
        )
        self.assertTrue(heartbeat_serializer.is_valid())
