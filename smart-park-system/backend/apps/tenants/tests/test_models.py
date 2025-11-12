from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User, Group
from django.utils import timezone

from apps.tenants.models import Clients, ClientMembers
from .test_utils import TestDataMixin


class ClientsModelTest(TestCase, TestDataMixin):
    """Testes para o model Clients"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_data = {"name": "Test Company", "onboarding_status": "ACTIVE"}

    def test_create_client(self):
        """Testa criação de cliente"""
        client = Clients.objects.create(**self.client_data)

        self.assertEqual(client.name, "Test Company")
        self.assertEqual(client.onboarding_status, "ACTIVE")
        self.assertIsNotNone(client.public_id)
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.updated_at)
        self.assertIsNone(client.deleted_at)

    def test_client_str_method(self):
        """Testa método __str__ do cliente"""
        client = Clients.objects.create(**self.client_data)
        expected = f"Test Company (Ativo)"
        self.assertEqual(str(client), expected)

    def test_client_default_status(self):
        """Testa status padrão do cliente"""
        client = Clients.objects.create(name="Test Company")
        self.assertEqual(client.onboarding_status, "PENDING")

    def test_client_status_choices(self):
        """Testa choices de status do cliente"""
        client = Clients.objects.create(
            name="Test Company", onboarding_status="SUSPENDED"
        )
        self.assertEqual(client.onboarding_status, "SUSPENDED")

        client.onboarding_status = "CANCELLED"
        client.save()
        self.assertEqual(client.onboarding_status, "CANCELLED")

    def test_client_soft_delete(self):
        """Testa soft delete do cliente"""
        client = Clients.objects.create(**self.client_data)
        self.assertFalse(client.is_deleted)

        client.soft_delete()
        self.assertTrue(client.is_deleted)
        self.assertIsNotNone(client.deleted_at)

        # Verifica que não aparece no queryset padrão
        self.assertNotIn(client, Clients.objects.all())

        # Verifica que aparece no with_deleted
        self.assertIn(client, Clients.objects.with_deleted())

    def test_client_restore(self):
        """Testa restore do cliente"""
        client = Clients.objects.create(**self.client_data)
        client.soft_delete()
        self.assertTrue(client.is_deleted)

        client.restore()
        self.assertFalse(client.is_deleted)
        self.assertIsNone(client.deleted_at)

        # Verifica que volta a aparecer no queryset padrão
        self.assertIn(client, Clients.objects.all())

    def test_client_name_max_length(self):
        """Testa validação de tamanho máximo do nome"""
        long_name = "a" * 121  # Excede o limite de 120
        with self.assertRaises(ValidationError):
            client = Clients(name=long_name)
            client.full_clean()


class ClientMembersModelTest(TestCase, TestDataMixin):
    """Testes para o model ClientMembers"""

    def setUp(self):
        """Setup para cada teste"""
        self.client = self.create_client()
        self.user = self.create_user()
        self.role = self.create_group(name="client_admin")

    def test_create_client_member(self):
        """Testa criação de membro de cliente"""
        member = ClientMembers.objects.create(
            client=self.client, user=self.user, role=self.role
        )

        self.assertEqual(member.client, self.client)
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, self.role)
        self.assertIsNotNone(member.joined_at)
        self.assertIsNotNone(member.public_id)

    def test_client_member_str_method(self):
        """Testa método __str__ do membro de cliente"""
        member = ClientMembers.objects.create(
            client=self.client, user=self.user, role=self.role
        )
        expected = f"{self.user.username} - {self.client.name} ({self.role.name})"
        self.assertEqual(str(member), expected)

    def test_client_member_unique_constraint(self):
        """Testa constraint de unicidade cliente-usuário"""
        # Cria primeiro membro
        ClientMembers.objects.create(client=self.client, user=self.user, role=self.role)

        # Tenta criar segundo membro com mesmo cliente e usuário
        role2 = self.create_group(name="admin")
        with self.assertRaises(IntegrityError):
            ClientMembers.objects.create(client=self.client, user=self.user, role=role2)

    def test_client_member_relationships(self):
        """Testa relacionamentos do modelo"""
        member = ClientMembers.objects.create(
            client=self.client, user=self.user, role=self.role
        )

        # Testa relacionamento inverso do cliente
        self.assertIn(member, self.client.client_members.all())

        # Testa relacionamento inverso do usuário
        self.assertIn(member, self.user.client_members.all())

        # Testa relacionamento inverso do role
        self.assertIn(member, self.role.client_members.all())

    def test_client_member_soft_delete(self):
        """Testa soft delete do membro de cliente"""
        member = ClientMembers.objects.create(
            client=self.client, user=self.user, role=self.role
        )

        self.assertFalse(member.is_deleted)

        member.soft_delete()
        self.assertTrue(member.is_deleted)

        # Verifica que não aparece no queryset padrão
        self.assertNotIn(member, ClientMembers.objects.all())

        # Verifica que aparece no with_deleted
        self.assertIn(member, ClientMembers.objects.with_deleted())

    def test_client_member_joined_at_auto_add(self):
        """Testa que joined_at é definido automaticamente"""
        before_creation = timezone.now()
        member = ClientMembers.objects.create(
            client=self.client, user=self.user, role=self.role
        )
        after_creation = timezone.now()

        self.assertGreaterEqual(member.joined_at, before_creation)
        self.assertLessEqual(member.joined_at, after_creation)

    def test_protect_on_delete(self):
        """Testa proteção contra delete em cascata"""
        member = ClientMembers.objects.create(
            client=self.client, user=self.user, role=self.role
        )

        # Não deve permitir deletar client se existem membros
        with self.assertRaises(Exception):  # ProtectedError
            self.client.delete()

        # Não deve permitir deletar user se existem memberships
        with self.assertRaises(Exception):  # ProtectedError
            self.user.delete()

        # Não deve permitir deletar role se existem memberships
        with self.assertRaises(Exception):  # ProtectedError
            self.role.delete()


class SoftDeleteManagerTest(TestCase, TestDataMixin):
    """Testes para o SoftDeleteManager"""

    def setUp(self):
        """Setup para cada teste"""
        self.client1 = self.create_client(name="Client 1")
        self.client2 = self.create_client(name="Client 2")
        self.client3 = self.create_client(name="Client 3")

    def test_default_queryset_excludes_deleted(self):
        """Testa que queryset padrão exclui objetos deletados"""
        # Soft delete um cliente
        self.client2.soft_delete()

        active_clients = Clients.objects.all()
        self.assertEqual(active_clients.count(), 2)
        self.assertIn(self.client1, active_clients)
        self.assertNotIn(self.client2, active_clients)
        self.assertIn(self.client3, active_clients)

    def test_with_deleted_includes_all(self):
        """Testa que with_deleted inclui todos os objetos"""
        # Soft delete um cliente
        self.client2.soft_delete()

        all_clients = Clients.objects.with_deleted()
        self.assertEqual(all_clients.count(), 3)
        self.assertIn(self.client1, all_clients)
        self.assertIn(self.client2, all_clients)
        self.assertIn(self.client3, all_clients)

    def test_only_deleted_returns_only_deleted(self):
        """Testa que only_deleted retorna apenas objetos deletados"""
        # Soft delete dois clientes
        self.client1.soft_delete()
        self.client3.soft_delete()

        deleted_clients = Clients.objects.only_deleted()
        self.assertEqual(deleted_clients.count(), 2)
        self.assertIn(self.client1, deleted_clients)
        self.assertNotIn(self.client2, deleted_clients)
        self.assertIn(self.client3, deleted_clients)
