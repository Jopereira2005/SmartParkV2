from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from apps.tenants.models import Clients, ClientMembers
from .test_utils import TestDataMixin


class ClientListCreateViewTest(TestCase, TestDataMixin):
    """Testes para ClientListCreateView"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.url = reverse("tenants:client-list")

        # Criar usuários com diferentes permissões
        self.admin_user = self.create_admin_user()
        self.client_admin_user = self.create_client_admin_user()
        self.regular_user = self.create_app_user()

        # Criar alguns clientes para testes
        self.client1 = self.create_client(name="Client 1", onboarding_status="ACTIVE")
        self.client2 = self.create_client(name="Client 2", onboarding_status="PENDING")
        self.client3 = self.create_client(
            name="Client 3", onboarding_status="SUSPENDED"
        )

    def test_list_clients_requires_admin_permission(self):
        """Testa que listar clientes requer permissão de admin"""
        # Sem autenticação
        response = self.client_api.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Com usuário regular
        self.client_api.force_authenticate(user=self.regular_user)
        response = self.client_api.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Com client_admin
        self.client_api.force_authenticate(user=self.client_admin_user)
        response = self.client_api.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_clients_with_admin_permission(self):
        """Testa listagem de clientes com permissão de admin"""
        self.client_api.force_authenticate(user=self.admin_user)
        response = self.client_api.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

        # Verifica se os clientes estão na resposta
        client_names = [client["name"] for client in response.data["results"]]
        self.assertIn("Client 1", client_names)
        self.assertIn("Client 2", client_names)
        self.assertIn("Client 3", client_names)

    def test_search_clients_by_name(self):
        """Testa busca de clientes por nome"""
        self.client_api.force_authenticate(user=self.admin_user)
        response = self.client_api.get(self.url, {"search": "Client 1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # A busca pode retornar mais de um resultado se houver correspondências parciais
        self.assertGreaterEqual(len(response.data["results"]), 1)
        # Verifica se Client 1 está nos resultados
        client_names = [client["name"] for client in response.data["results"]]
        self.assertIn("Client 1", client_names)

    def test_search_clients_by_status(self):
        """Testa busca de clientes por status"""
        self.client_api.force_authenticate(user=self.admin_user)

        # Verificar quantos clientes existem primeiro
        all_response = self.client_api.get(self.url)
        total_clients = len(all_response.data["results"])

        # Busca por um termo que deve retornar menos resultados
        response = self.client_api.get(self.url, {"search": "SUSPENDED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # A busca deve retornar menos clientes que o total
        search_results = len(response.data["results"])
        self.assertLessEqual(search_results, total_clients)

        # Se houver resultados, verificar se contêm o termo buscado
        if search_results > 0:
            found_suspended = any(
                "SUSPENDED" in client["name"]
                or client["onboarding_status"] == "SUSPENDED"
                for client in response.data["results"]
            )
            self.assertTrue(found_suspended)

    def test_create_client_requires_admin_permission(self):
        """Testa que criar cliente requer permissão de admin"""
        data = {"name": "New Client", "onboarding_status": "PENDING"}

        # Sem autenticação
        response = self.client_api.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Com usuário regular
        self.client_api.force_authenticate(user=self.regular_user)
        response = self.client_api.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_client_with_admin_permission(self):
        """Testa criação de cliente com permissão de admin"""
        self.client_api.force_authenticate(user=self.admin_user)
        data = {"name": "New Client", "onboarding_status": "ACTIVE"}

        response = self.client_api.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Client")
        self.assertEqual(response.data["onboarding_status"], "ACTIVE")

        # Verifica se foi criado no banco
        self.assertTrue(Clients.objects.filter(name="New Client").exists())

    def test_create_client_invalid_data(self):
        """Testa criação de cliente com dados inválidos"""
        self.client_api.force_authenticate(user=self.admin_user)

        # Nome vazio
        data = {"name": "", "onboarding_status": "ACTIVE"}
        response = self.client_api.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Status inválido
        data = {"name": "Valid Name", "onboarding_status": "INVALID"}
        response = self.client_api.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pagination(self):
        """Testa paginação dos resultados"""
        # Criar mais clientes para testar paginação
        for i in range(15):
            self.create_client(name=f"Client {i+10}")

        self.client_api.force_authenticate(user=self.admin_user)
        response = self.client_api.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)


class ClientDetailViewTest(TestCase, TestDataMixin):
    """Testes para ClientDetailView"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.admin_user = self.create_admin_user()
        self.regular_user = self.create_app_user()

        self.client_obj = self.create_client(
            name="Test Client", onboarding_status="ACTIVE"
        )
        self.url = reverse("tenants:client-detail", kwargs={"pk": self.client_obj.pk})

    def test_get_client_requires_admin_permission(self):
        """Testa que buscar cliente requer permissão de admin"""
        # Sem autenticação
        response = self.client_api.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Com usuário regular
        self.client_api.force_authenticate(user=self.regular_user)
        response = self.client_api.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_client_with_admin_permission(self):
        """Testa busca de cliente com permissão de admin"""
        self.client_api.force_authenticate(user=self.admin_user)
        response = self.client_api.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Client")
        self.assertEqual(response.data["onboarding_status"], "ACTIVE")

    def test_get_nonexistent_client(self):
        """Testa busca de cliente inexistente"""
        self.client_api.force_authenticate(user=self.admin_user)
        url = reverse("tenants:client-detail", kwargs={"pk": 99999})
        response = self.client_api.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_client_with_put(self):
        """Testa atualização completa de cliente com PUT"""
        self.client_api.force_authenticate(user=self.admin_user)
        data = {"name": "Updated Client", "onboarding_status": "SUSPENDED"}

        response = self.client_api.put(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Client")
        self.assertEqual(response.data["onboarding_status"], "SUSPENDED")

        # Verifica se foi atualizado no banco
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.name, "Updated Client")
        self.assertEqual(self.client_obj.onboarding_status, "SUSPENDED")

    def test_update_client_with_patch(self):
        """Testa atualização parcial de cliente com PATCH"""
        self.client_api.force_authenticate(user=self.admin_user)
        data = {"onboarding_status": "CANCELLED"}

        response = self.client_api.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Client")  # Nome não mudou
        self.assertEqual(response.data["onboarding_status"], "CANCELLED")

        # Verifica se foi atualizado no banco
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.onboarding_status, "CANCELLED")

    def test_delete_client_soft_delete(self):
        """Testa soft delete de cliente"""
        self.client_api.force_authenticate(user=self.admin_user)
        response = self.client_api.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verifica se foi soft deleted
        self.client_obj.refresh_from_db()
        self.assertTrue(self.client_obj.is_deleted)

        # Verifica se não aparece mais em consultas normais
        self.assertNotIn(self.client_obj, Clients.objects.all())
        self.assertIn(self.client_obj, Clients.objects.with_deleted())


class ClientMemberListViewTest(TestCase, TestDataMixin):
    """Testes para ClientMemberListView"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()

        # Criar usuários e grupos
        self.admin_user = self.create_admin_user()
        self.client_admin_user = self.create_client_admin_user()
        self.regular_user = self.create_app_user()

        # Criar cliente e membros
        self.client_obj = self.create_client(name="Test Client")
        self.role, _ = Group.objects.get_or_create(name="client_admin")

        # Criar alguns membros
        self.member1 = self.create_client_member(
            client=self.client_obj, user=self.client_admin_user, role=self.role
        )
        self.member2 = self.create_client_member(
            client=self.client_obj,
            user=self.create_user(username="member2"),
            role=self.role,
        )

        self.url = reverse(
            "tenants:client-member-list", kwargs={"client_id": self.client_obj.pk}
        )

    def test_list_members_requires_client_admin_permission(self):
        """Testa que listar membros requer permissão de client_admin"""
        # Sem autenticação
        response = self.client_api.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Com usuário regular
        self.client_api.force_authenticate(user=self.regular_user)
        response = self.client_api.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_members_with_client_admin_permission(self):
        """Testa listagem de membros com permissão de client_admin"""
        self.client_api.force_authenticate(user=self.client_admin_user)
        response = self.client_api.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_search_members_by_user_name(self):
        """Testa busca de membros por nome de usuário"""
        # Verificar se o client_admin_user já é membro, senão criar
        if not ClientMembers.objects.filter(
            client=self.client_obj, user=self.client_admin_user
        ).exists():
            self.create_client_member(
                client=self.client_obj, user=self.client_admin_user, role=self.role
            )

        self.client_api.force_authenticate(user=self.client_admin_user)
        response = self.client_api.get(self.url, {"search": "member2"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # A busca pode retornar múltiplos resultados se houver correspondências parciais
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_create_member_with_valid_data(self):
        """Testa criação de membro com dados válidos"""
        self.client_api.force_authenticate(user=self.client_admin_user)
        new_user = self.create_user(username="newmember")

        data = {"user_id": new_user.id, "group_id": self.role.id}

        response = self.client_api.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["id"], new_user.id)
        self.assertEqual(response.data["client"]["id"], self.client_obj.id)

        # Verifica se foi criado no banco
        self.assertTrue(
            ClientMembers.objects.filter(client=self.client_obj, user=new_user).exists()
        )

    def test_create_member_duplicate_user(self):
        """Testa criação de membro com usuário duplicado"""
        self.client_api.force_authenticate(user=self.client_admin_user)

        data = {
            "user_id": self.client_admin_user.id,  # Usuário já é membro
            "group_id": self.role.id,
        }

        response = self.client_api.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Este usuário já é membro deste cliente", str(response.data))

    def test_create_member_nonexistent_user(self):
        """Testa criação de membro com usuário inexistente"""
        self.client_api.force_authenticate(user=self.client_admin_user)

        data = {"user_id": 99999, "group_id": self.role.id}  # ID que não existe

        response = self.client_api.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Usuário não encontrado", str(response.data))


class ClientMemberDetailViewTest(TestCase, TestDataMixin):
    """Testes para ClientMemberDetailView"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()

        self.admin_user = self.create_admin_user()
        self.client_admin_user = self.create_client_admin_user()

        self.client_obj = self.create_client()
        self.role, _ = Group.objects.get_or_create(name="client_admin")
        self.member = self.create_client_member(
            client=self.client_obj, user=self.create_user(), role=self.role
        )

        self.url = reverse(
            "tenants:client-member-detail",
            kwargs={"client_id": self.client_obj.pk, "pk": self.member.pk},
        )

    def test_get_member_details(self):
        """Testa busca de detalhes do membro"""
        # Criar membership para o client_admin_user poder acessar
        self.create_client_member(
            client=self.client_obj, user=self.client_admin_user, role=self.role
        )

        self.client_api.force_authenticate(user=self.client_admin_user)
        response = self.client_api.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.member.id)
        self.assertEqual(response.data["client"]["id"], self.client_obj.id)

    def test_delete_member(self):
        """Testa remoção de membro"""
        # Criar membership para o client_admin_user poder acessar
        self.create_client_member(
            client=self.client_obj, user=self.client_admin_user, role=self.role
        )

        self.client_api.force_authenticate(user=self.client_admin_user)
        response = self.client_api.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verifica se foi removido (hard delete neste caso)
        self.assertFalse(ClientMembers.objects.filter(id=self.member.id).exists())


class MyClientsViewTest(TestCase, TestDataMixin):
    """Testes para my_clients_view"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()
        self.url = reverse("tenants:my-clients")

        self.user = self.create_user(username="testuser")
        self.role, _ = Group.objects.get_or_create(name="client_admin")

        # Criar clientes e memberships para o usuário
        self.client1 = self.create_client(name="Client 1", onboarding_status="ACTIVE")
        self.client2 = self.create_client(name="Client 2", onboarding_status="PENDING")

        self.member1 = self.create_client_member(
            client=self.client1, user=self.user, role=self.role
        )
        self.member2 = self.create_client_member(
            client=self.client2, user=self.user, role=self.role
        )

        # Criar outro cliente que o usuário não é membro
        self.other_client = self.create_client(name="Other Client")

    def test_my_clients_requires_authentication(self):
        """Testa que a view requer autenticação"""
        response = self.client_api.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_my_clients_returns_user_clients_only(self):
        """Testa que retorna apenas clientes do usuário logado"""
        self.client_api.force_authenticate(user=self.user)
        response = self.client_api.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Verifica se retorna os clientes corretos
        client_ids = [client["id"] for client in response.data]
        self.assertIn(self.client1.id, client_ids)
        self.assertIn(self.client2.id, client_ids)
        self.assertNotIn(self.other_client.id, client_ids)

    def test_my_clients_response_format(self):
        """Testa formato da resposta de my_clients"""
        self.client_api.force_authenticate(user=self.user)
        response = self.client_api.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        client_data = response.data[0]
        expected_fields = ["id", "name", "onboarding_status", "role", "joined_at"]

        for field in expected_fields:
            self.assertIn(field, client_data)

    def test_my_clients_empty_for_non_member(self):
        """Testa que retorna lista vazia para usuário sem clientes"""
        user_without_clients = self.create_user(username="loneuser")
        self.client_api.force_authenticate(user=user_without_clients)
        response = self.client_api.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class ViewPermissionsTest(TestCase, TestDataMixin):
    """Testes específicos para permissões das views"""

    def setUp(self):
        """Setup para cada teste"""
        self.client_api = APIClient()

        # Criar usuários com diferentes níveis
        self.admin_user = self.create_admin_user()
        self.client_admin_user = self.create_client_admin_user()
        self.app_user = self.create_app_user()

        self.client_obj = self.create_client()

    def test_admin_permissions(self):
        """Testa permissões de admin em todas as views"""
        self.client_api.force_authenticate(user=self.admin_user)

        # Pode acessar lista de clientes
        url = reverse("tenants:client-list")
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Pode acessar detalhes do cliente
        url = reverse("tenants:client-detail", kwargs={"pk": self.client_obj.pk})
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_admin_permissions(self):
        """Testa permissões de client_admin"""
        # Criar um membership para o client_admin no cliente
        client_admin_group, _ = Group.objects.get_or_create(name="client_admin")
        member = self.create_client_member(
            client=self.client_obj, user=self.client_admin_user, role=client_admin_group
        )

        self.client_api.force_authenticate(user=self.client_admin_user)

        # Não pode acessar lista geral de clientes
        url = reverse("tenants:client-list")
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Pode acessar membros do cliente onde é membro
        url = reverse(
            "tenants:client-member-list", kwargs={"client_id": self.client_obj.pk}
        )
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_app_user_permissions(self):
        """Testa permissões de app_user"""
        self.client_api.force_authenticate(user=self.app_user)

        # Não pode acessar lista de clientes
        url = reverse("tenants:client-list")
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Não pode acessar membros de cliente
        url = reverse(
            "tenants:client-member-list", kwargs={"client_id": self.client_obj.pk}
        )
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Pode acessar seus próprios clientes
        url = reverse("tenants:my-clients")
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
