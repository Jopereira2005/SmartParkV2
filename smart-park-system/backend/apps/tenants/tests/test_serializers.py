from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from apps.tenants.models import Clients, ClientMembers
from apps.tenants.serializers import (
    ClientSerializer,
    ClientCreateSerializer,
    ClientMemberSerializer,
    ClientMemberCreateSerializer,
)
from .test_utils import TestDataMixin


class ClientSerializerTest(TestCase, TestDataMixin):
    """Testes para ClientSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client(
            name="Test Company", onboarding_status="ACTIVE"
        )

    def test_serialize_client(self):
        """Testa serialização de cliente"""
        serializer = ClientSerializer(self.client)
        data = serializer.data

        # Verifica campos base
        self.assertEqual(data["id"], self.client.id)
        self.assertEqual(data["public_id"], str(self.client.public_id))
        self.assertEqual(data["name"], "Test Company")
        self.assertEqual(data["onboarding_status"], "ACTIVE")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertIn("is_deleted", data)

    def test_serialize_deleted_at_null(self):
        """Testa serialização com is_deleted False"""
        serializer = ClientSerializer(self.client)
        data = serializer.data
        self.assertFalse(data["is_deleted"])

    def test_serialize_soft_deleted_client(self):
        """Testa serialização de cliente soft deleted"""
        self.client.soft_delete()
        serializer = ClientSerializer(self.client)
        data = serializer.data
        self.assertTrue(data["is_deleted"])


class ClientCreateSerializerTest(TestCase, TestDataMixin):
    """Testes para ClientCreateSerializer"""

    def test_create_client_valid_data(self):
        """Testa criação de cliente com dados válidos"""
        data = {"name": "New Company", "onboarding_status": "PENDING"}
        serializer = ClientCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        client = serializer.save()
        self.assertEqual(client.name, "New Company")
        self.assertEqual(client.onboarding_status, "PENDING")

    def test_create_client_default_status(self):
        """Testa criação de cliente com status padrão"""
        data = {"name": "New Company"}
        serializer = ClientCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        client = serializer.save()
        self.assertEqual(client.onboarding_status, "PENDING")

    def test_create_client_invalid_name(self):
        """Testa validação de nome inválido"""
        data = {"name": ""}  # Nome vazio
        serializer = ClientCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_create_client_invalid_status(self):
        """Testa validação de status inválido"""
        data = {"name": "Test Company", "onboarding_status": "INVALID_STATUS"}
        serializer = ClientCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("onboarding_status", serializer.errors)

    def test_create_client_long_name(self):
        """Testa validação de nome muito longo"""
        data = {
            "name": "a" * 121,  # Excede o limite de 120
            "onboarding_status": "ACTIVE",
        }
        serializer = ClientCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)


class ClientMemberSerializerTest(TestCase, TestDataMixin):
    """Testes para ClientMemberSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client(name="Test Company")
        self.user = self.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        self.role = self.create_group(name="client_admin")
        self.member = self.create_client_member(
            client=self.client, user=self.user, role=self.role
        )

    def test_serialize_client_member(self):
        """Testa serialização de membro de cliente"""
        serializer = ClientMemberSerializer(self.member)
        data = serializer.data

        # Verifica campos base
        self.assertEqual(data["id"], self.member.id)
        self.assertEqual(data["public_id"], str(self.member.public_id))
        self.assertIn("joined_at", data)

        # Verifica dados do usuário
        user_data = data["user"]
        self.assertEqual(user_data["id"], self.user.id)
        self.assertEqual(user_data["name"], "Test User")
        self.assertEqual(user_data["email"], "test@example.com")

        # Verifica dados do role
        role_data = data["role"]
        self.assertEqual(role_data["id"], self.role.id)
        self.assertEqual(role_data["name"], "client_admin")

        # Verifica dados do cliente
        client_data = data["client"]
        self.assertEqual(client_data["id"], self.client.id)
        self.assertEqual(client_data["name"], "Test Company")

    def test_user_name_with_username_fallback(self):
        """Testa nome do usuário quando não tem first/last name"""
        user_no_name = self.create_user(username="noname", first_name="", last_name="")
        member = self.create_client_member(
            client=self.client, user=user_no_name, role=self.role
        )

        serializer = ClientMemberSerializer(member)
        data = serializer.data

        user_data = data["user"]
        self.assertEqual(user_data["name"], "noname")


class ClientMemberCreateSerializerTest(TestCase, TestDataMixin):
    """Testes para ClientMemberCreateSerializer"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()
        self.user = self.create_user()
        self.group = self.create_group(name="client_admin")
        self.context = {"client_id": self.client.id}

    def test_create_member_valid_data(self):
        """Testa criação de membro com dados válidos"""
        data = {"user_id": self.user.id, "group_id": self.group.id}
        serializer = ClientMemberCreateSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        member = serializer.save()
        self.assertEqual(member.client_id, self.client.id)
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, self.group)

    def test_validate_nonexistent_user(self):
        """Testa validação de usuário inexistente"""
        data = {"user_id": 99999, "group_id": self.group.id}  # ID que não existe
        serializer = ClientMemberCreateSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_id", serializer.errors)
        self.assertEqual(serializer.errors["user_id"][0], "Usuário não encontrado")

    def test_validate_nonexistent_group(self):
        """Testa validação de grupo inexistente"""
        data = {"user_id": self.user.id, "group_id": 99999}  # ID que não existe
        serializer = ClientMemberCreateSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("group_id", serializer.errors)
        self.assertEqual(serializer.errors["group_id"][0], "Group não encontrado")

    def test_validate_duplicate_membership(self):
        """Testa validação de membership duplicada"""
        # Cria um membro primeiro
        self.create_client_member(client=self.client, user=self.user, role=self.group)

        # Tenta criar outro membro com mesmo cliente e usuário
        data = {"user_id": self.user.id, "group_id": self.group.id}
        serializer = ClientMemberCreateSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            serializer.errors["non_field_errors"][0],
            "Este usuário já é membro deste cliente",
        )

    def test_missing_user_id(self):
        """Testa validação com user_id ausente"""
        data = {"group_id": self.group.id}
        serializer = ClientMemberCreateSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_id", serializer.errors)

    def test_missing_group_id(self):
        """Testa validação com group_id ausente"""
        data = {"user_id": self.user.id}
        serializer = ClientMemberCreateSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("group_id", serializer.errors)

    def test_missing_client_id_in_context(self):
        """Testa comportamento sem client_id no context - deve falhar"""
        data = {"user_id": self.user.id, "group_id": self.group.id}
        serializer = ClientMemberCreateSerializer(data=data, context={})
        self.assertTrue(serializer.is_valid())

        # Deve falhar ao tentar salvar sem client_id
        with self.assertRaises(Exception):  # IntegrityError ou similar
            serializer.save()

    def test_invalid_data_types(self):
        """Testa validação com tipos de dados inválidos"""
        data = {"user_id": "invalid", "group_id": "invalid"}
        serializer = ClientMemberCreateSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_id", serializer.errors)
        self.assertIn("group_id", serializer.errors)


class SerializerFieldsTest(TestCase, TestDataMixin):
    """Testes para campos específicos dos serializers"""

    def test_client_serializer_fields(self):
        """Testa campos incluídos no ClientSerializer"""
        client = self.create_client()
        serializer = ClientSerializer(client)
        expected_fields = [
            "id",
            "public_id",
            "created_at",
            "updated_at",
            "is_deleted",
            "name",
            "onboarding_status",
        ]

        for field in expected_fields:
            self.assertIn(field, serializer.data)

    def test_client_create_serializer_fields(self):
        """Testa campos incluídos no ClientCreateSerializer"""
        serializer = ClientCreateSerializer()
        expected_fields = ["name", "onboarding_status"]

        for field in expected_fields:
            self.assertIn(field, serializer.fields)

    def test_client_member_serializer_fields(self):
        """Testa campos incluídos no ClientMemberSerializer"""
        member = self.create_client_member()
        serializer = ClientMemberSerializer(member)
        expected_fields = [
            "id",
            "public_id",
            "created_at",
            "updated_at",
            "is_deleted",
            "client",
            "user",
            "role",
            "joined_at",
        ]

        for field in expected_fields:
            self.assertIn(field, serializer.data)

    def test_client_member_create_serializer_fields(self):
        """Testa campos incluídos no ClientMemberCreateSerializer"""
        serializer = ClientMemberCreateSerializer()
        expected_fields = ["user_id", "group_id"]

        for field in expected_fields:
            self.assertIn(field, serializer.fields)
