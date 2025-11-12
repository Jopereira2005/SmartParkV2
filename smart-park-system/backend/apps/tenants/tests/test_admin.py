from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse
from unittest.mock import Mock
from model_bakery import baker

from apps.tenants.admin import ClientsAdmin, ClientMembersAdmin, ClientMembersInline
from apps.tenants.models import Clients, ClientMembers
from .test_utils import TestDataMixin

User = get_user_model()


class AdminTestBase(TestCase, TestDataMixin):
    """Classe base para testes de admin"""

    def setUp(self):
        """Setup base para testes de admin"""
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.superuser = baker.make(User, is_superuser=True, is_staff=True)

        # Registrar os admins no site de teste
        from apps.tenants.admin import ClientsAdmin, ClientMembersAdmin

        self.site.register(Clients, ClientsAdmin)
        self.site.register(ClientMembers, ClientMembersAdmin)

        # Criar dados básicos quando necessário para alguns testes
        self.client = self.create_client()
        self.user = self.create_user()
        self.group = self.create_group()
        self.client_member = self.create_client_member(
            client=self.client, user=self.user, role=self.group
        )

    def create_request(self, url="/", user=None, method="GET", **kwargs):
        """Cria uma request mock para testes"""
        if method == "GET":
            request = self.factory.get(url, **kwargs)
        elif method == "POST":
            request = self.factory.post(url, **kwargs)
        else:
            request = getattr(self.factory, method.lower())(url, **kwargs)

        request.user = user or self.superuser

        # Adicionar messages framework
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        return request


class ClientsAdminTest(AdminTestBase):
    """Testes para ClientsAdmin"""

    def setUp(self):
        super().setUp()
        self.admin = ClientsAdmin(Clients, self.site)

    def test_admin_registration(self):
        """Testa se o admin está registrado corretamente"""
        self.assertIn(Clients, self.site._registry)
        self.assertIsInstance(self.site._registry[Clients], ClientsAdmin)

    def test_list_display_fields(self):
        """Testa campos exibidos na lista"""
        expected_fields = [
            "name",
            "onboarding_status",
            "members_count",
            "establishments_count",
            "created_at",
        ]
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_list_filter_fields(self):
        """Testa campos de filtro"""
        expected_filters = ["onboarding_status", "created_at"]
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """Testa campos de busca"""
        expected_search = ["name"]
        self.assertEqual(self.admin.search_fields, expected_search)

    def test_readonly_fields(self):
        """Testa campos readonly"""
        expected_readonly = ["created_at", "updated_at"]
        self.assertEqual(self.admin.readonly_fields, expected_readonly)

    def test_inlines_configuration(self):
        """Testa configuração de inlines"""
        self.assertEqual(len(self.admin.inlines), 1)
        self.assertEqual(self.admin.inlines[0], ClientMembersInline)

    def test_fieldsets_configuration(self):
        """Testa configuração de fieldsets"""
        expected_fieldsets = (
            ("Informações Básicas", {"fields": ("name", "onboarding_status")}),
            (
                "Dados de Auditoria",
                {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
            ),
        )
        self.assertEqual(self.admin.fieldsets, expected_fieldsets)

    def test_get_queryset_with_annotations(self):
        """Testa queryset com anotações"""
        request = self.create_request()
        queryset = self.admin.get_queryset(request)

        # Verificar se as anotações estão presentes
        first_client = queryset.first()
        self.assertTrue(hasattr(first_client, "members_count"))
        self.assertTrue(hasattr(first_client, "establishments_count"))

    def test_members_count_method(self):
        """Testa método members_count"""
        # Testar com objeto que tem anotação
        client_with_annotation = Mock()
        client_with_annotation.members_count = 5
        result = self.admin.members_count(client_with_annotation)
        self.assertIn("5 membros", result)
        self.assertIn("href=", result)

    def test_establishments_count_method_with_count(self):
        """Testa método establishments_count com estabelecimentos"""
        client_with_annotation = Mock()
        client_with_annotation.establishments_count = 3
        client_with_annotation.id = 1
        result = self.admin.establishments_count(client_with_annotation)
        self.assertIn("3 estabelecimentos", result)
        self.assertIn("href=", result)

    def test_establishments_count_method_without_count(self):
        """Testa método establishments_count sem estabelecimentos"""
        client_with_annotation = Mock()
        client_with_annotation.establishments_count = 0
        result = self.admin.establishments_count(client_with_annotation)
        self.assertEqual(result, "0 estabelecimentos")

    def test_actions_configuration(self):
        """Testa configuração de actions"""
        expected_actions = ["activate_clients", "deactivate_clients"]
        self.assertEqual(self.admin.actions, expected_actions)

    def test_activate_clients_action(self):
        """Testa action de ativar clientes"""
        # Criar clientes inativos
        inactive_clients = baker.make(
            Clients, onboarding_status="INACTIVE", _quantity=3
        )

        request = self.create_request()
        queryset = Clients.objects.filter(id__in=[c.id for c in inactive_clients])

        # Executar action
        self.admin.activate_clients(request, queryset)

        # Verificar se foram ativados
        for client in inactive_clients:
            client.refresh_from_db()
            self.assertEqual(client.onboarding_status, "ACTIVE")

    def test_deactivate_clients_action(self):
        """Testa action de desativar clientes"""
        # Criar clientes ativos
        active_clients = baker.make(Clients, onboarding_status="ACTIVE", _quantity=2)

        request = self.create_request()
        queryset = Clients.objects.filter(id__in=[c.id for c in active_clients])

        # Executar action
        self.admin.deactivate_clients(request, queryset)

        # Verificar se foram desativados
        for client in active_clients:
            client.refresh_from_db()
            self.assertEqual(client.onboarding_status, "INACTIVE")


class ClientMembersInlineTest(AdminTestBase):
    """Testes para ClientMembersInline"""

    def setUp(self):
        super().setUp()
        self.inline = ClientMembersInline(ClientMembers, self.site)

    def test_inline_configuration(self):
        """Testa configuração do inline"""
        self.assertEqual(self.inline.model, ClientMembers)
        self.assertEqual(self.inline.extra, 0)

        expected_fields = ["user", "role", "joined_at"]
        self.assertEqual(self.inline.fields, expected_fields)

        expected_readonly = ["joined_at"]
        self.assertEqual(self.inline.readonly_fields, expected_readonly)


class ClientMembersAdminTest(AdminTestBase):
    """Testes para ClientMembersAdmin"""

    def setUp(self):
        super().setUp()
        self.admin = ClientMembersAdmin(ClientMembers, self.site)

    def test_admin_registration(self):
        """Testa se o admin está registrado corretamente"""
        self.assertIn(ClientMembers, self.site._registry)
        self.assertIsInstance(self.site._registry[ClientMembers], ClientMembersAdmin)

    def test_list_display_fields(self):
        """Testa campos exibidos na lista"""
        expected_fields = ["client", "user_info", "role", "joined_at"]
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_list_filter_fields(self):
        """Testa campos de filtro"""
        expected_filters = ["role", "joined_at", "client"]
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """Testa campos de busca"""
        expected_search = ["client__name", "user__username", "user__email"]
        self.assertEqual(self.admin.search_fields, expected_search)

    def test_user_info_method(self):
        """Testa método user_info"""
        # Usar o membro existente do setUp
        result = self.admin.user_info(self.client_member)
        expected = (
            f"{self.client_member.user.username} ({self.client_member.user.email})"
        )
        self.assertEqual(result, expected)

    def test_user_info_short_description(self):
        """Testa short_description do método user_info"""
        self.assertEqual(self.admin.user_info.short_description, "Usuário")


class AdminIntegrationTest(AdminTestBase):
    """Testes de integração para funcionalidades do admin"""

    def test_admin_site_access(self):
        """Testa acesso ao site admin"""
        # Este teste verifica se o admin está configurado corretamente
        # sem fazer requisições HTTP reais

        # Verificar se os modelos estão registrados
        self.assertIn(Clients, self.site._registry)
        self.assertIn(ClientMembers, self.site._registry)

        # Verificar tipos corretos de admin
        self.assertIsInstance(self.site._registry[Clients], ClientsAdmin)
        self.assertIsInstance(self.site._registry[ClientMembers], ClientMembersAdmin)

    def test_admin_permissions(self):
        """Testa configurações de permissões do admin"""
        clients_admin = self.site._registry[Clients]
        members_admin = self.site._registry[ClientMembers]

        # Verificar se admins têm configurações básicas
        self.assertTrue(hasattr(clients_admin, "list_display"))
        self.assertTrue(hasattr(clients_admin, "list_filter"))
        self.assertTrue(hasattr(clients_admin, "search_fields"))

        self.assertTrue(hasattr(members_admin, "list_display"))
        self.assertTrue(hasattr(members_admin, "list_filter"))
        self.assertTrue(hasattr(members_admin, "search_fields"))

    def test_custom_methods_exist(self):
        """Testa se métodos customizados existem"""
        clients_admin = self.site._registry[Clients]
        members_admin = self.site._registry[ClientMembers]

        # Métodos do ClientsAdmin
        self.assertTrue(hasattr(clients_admin, "members_count"))
        self.assertTrue(hasattr(clients_admin, "establishments_count"))
        self.assertTrue(hasattr(clients_admin, "activate_clients"))
        self.assertTrue(hasattr(clients_admin, "deactivate_clients"))

        # Métodos do ClientMembersAdmin
        self.assertTrue(hasattr(members_admin, "user_info"))
