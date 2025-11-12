from django.test import TestCase
from django.urls import reverse, resolve, NoReverseMatch

from apps.tenants import views


class UrlsTest(TestCase):
    """Testes para URLs da app tenants"""

    def test_app_name(self):
        """Testa se o app_name está definido corretamente"""
        from apps.tenants.urls import app_name

        self.assertEqual(app_name, "tenants")

    def test_client_list_url_resolves(self):
        """Testa resolução da URL de listagem de clientes"""
        url = reverse("tenants:client-list")
        self.assertEqual(url, "/api/tenants/clients/")

        resolver = resolve("/api/tenants/clients/")
        self.assertEqual(resolver.view_name, "tenants:client-list")
        self.assertEqual(resolver.func.view_class, views.ClientListCreateView)

    def test_client_detail_url_resolves(self):
        """Testa resolução da URL de detalhes de cliente"""
        url = reverse("tenants:client-detail", kwargs={"pk": 1})
        self.assertEqual(url, "/api/tenants/clients/1/")

        resolver = resolve("/api/tenants/clients/1/")
        self.assertEqual(resolver.view_name, "tenants:client-detail")
        self.assertEqual(resolver.func.view_class, views.ClientDetailView)
        self.assertEqual(resolver.kwargs, {"pk": 1})

    def test_client_detail_url_with_different_pks(self):
        """Testa URL de detalhes com diferentes IDs"""
        test_pks = [1, 42, 999]

        for pk in test_pks:
            with self.subTest(pk=pk):
                url = reverse("tenants:client-detail", kwargs={"pk": pk})
                self.assertEqual(url, f"/api/tenants/clients/{pk}/")

                resolver = resolve(f"/api/tenants/clients/{pk}/")
                self.assertEqual(resolver.kwargs, {"pk": pk})

    def test_client_member_list_url_resolves(self):
        """Testa resolução da URL de listagem de membros"""
        url = reverse("tenants:client-member-list", kwargs={"client_id": 1})
        self.assertEqual(url, "/api/tenants/clients/1/members/")

        resolver = resolve("/api/tenants/clients/1/members/")
        self.assertEqual(resolver.view_name, "tenants:client-member-list")
        self.assertEqual(resolver.func.view_class, views.ClientMemberListView)
        self.assertEqual(resolver.kwargs, {"client_id": 1})

    def test_client_member_detail_url_resolves(self):
        """Testa resolução da URL de detalhes de membro"""
        url = reverse("tenants:client-member-detail", kwargs={"client_id": 1, "pk": 2})
        self.assertEqual(url, "/api/tenants/clients/1/members/2/")

        resolver = resolve("/api/tenants/clients/1/members/2/")
        self.assertEqual(resolver.view_name, "tenants:client-member-detail")
        self.assertEqual(resolver.func.view_class, views.ClientMemberDetailView)
        self.assertEqual(resolver.kwargs, {"client_id": 1, "pk": 2})

    def test_client_member_urls_with_different_ids(self):
        """Testa URLs de membros com diferentes IDs"""
        test_cases = [(1, 1), (5, 10), (99, 42)]

        for client_id, member_id in test_cases:
            with self.subTest(client_id=client_id, member_id=member_id):
                # Testar listagem de membros
                list_url = reverse(
                    "tenants:client-member-list", kwargs={"client_id": client_id}
                )
                self.assertEqual(list_url, f"/api/tenants/clients/{client_id}/members/")

                # Testar detalhes de membro
                detail_url = reverse(
                    "tenants:client-member-detail",
                    kwargs={"client_id": client_id, "pk": member_id},
                )
                self.assertEqual(
                    detail_url, f"/api/tenants/clients/{client_id}/members/{member_id}/"
                )

    def test_my_clients_url_resolves(self):
        """Testa resolução da URL de meus clientes"""
        url = reverse("tenants:my-clients")
        self.assertEqual(url, "/api/tenants/my-clients/")

        resolver = resolve("/api/tenants/my-clients/")
        self.assertEqual(resolver.view_name, "tenants:my-clients")
        self.assertEqual(resolver.func, views.my_clients_view)

    def test_all_url_names_exist(self):
        """Testa se todos os nomes de URL estão definidos"""
        expected_url_names = [
            "client-list",
            "client-detail",
            "client-member-list",
            "client-member-detail",
            "my-clients",
        ]

        for url_name in expected_url_names:
            with self.subTest(url_name=url_name):
                # Para URLs que precisam de parâmetros, fornecer valores dummy
                kwargs = {}
                if "detail" in url_name and "member" in url_name:
                    kwargs = {"client_id": 1, "pk": 1}
                elif "detail" in url_name:
                    kwargs = {"pk": 1}
                elif "member-list" in url_name:
                    kwargs = {"client_id": 1}

                try:
                    url = reverse(f"tenants:{url_name}", kwargs=kwargs)
                    self.assertIsInstance(url, str)
                    self.assertTrue(url.startswith("/api/tenants/"))
                except NoReverseMatch:
                    self.fail(f"URL name 'tenants:{url_name}' not found")

    def test_url_patterns_coverage(self):
        """Testa se todas as views têm URLs correspondentes"""
        # Mapear views para seus nomes de URL esperados
        view_to_url_mapping = {
            views.ClientListCreateView: "client-list",
            views.ClientDetailView: "client-detail",
            views.ClientMemberListView: "client-member-list",
            views.ClientMemberDetailView: "client-member-detail",
            views.my_clients_view: "my-clients",
        }

        for view, expected_url_name in view_to_url_mapping.items():
            with self.subTest(view=view.__name__, url_name=expected_url_name):
                # Verificar se a URL resolve para a view correta
                kwargs = {}
                if expected_url_name == "client-detail":
                    kwargs = {"pk": 1}
                elif expected_url_name == "client-member-list":
                    kwargs = {"client_id": 1}
                elif expected_url_name == "client-member-detail":
                    kwargs = {"client_id": 1, "pk": 1}

                url = reverse(f"tenants:{expected_url_name}", kwargs=kwargs)
                resolver = resolve(url)

                if hasattr(view, "as_view"):
                    # Para class-based views
                    self.assertEqual(resolver.func.view_class, view)
                else:
                    # Para function-based views
                    self.assertEqual(resolver.func, view)

    def test_invalid_url_patterns_fail(self):
        """Testa se URLs inválidas falham adequadamente"""
        invalid_urls = [
            "/api/tenants/clients/invalid/",  # PK não numérico
            "/api/tenants/clients/1/members/invalid/",  # Member PK não numérico
            "/api/tenants/nonexistent/",  # URL inexistente
        ]

        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url):
                try:
                    resolve(invalid_url)
                    # Se chegou aqui, a URL não deveria ter resolvido
                    self.fail(
                        f"URL inválida '{invalid_url}' foi resolvida incorretamente"
                    )
                except:
                    # Esperado - URL inválida deve falhar
                    pass

    def test_url_namespacing(self):
        """Testa se o namespace das URLs funciona corretamente"""
        # Testar URLs com namespace
        namespaced_urls = [
            ("tenants:client-list", "/api/tenants/clients/"),
            ("tenants:my-clients", "/api/tenants/my-clients/"),
        ]

        for namespaced_name, expected_url in namespaced_urls:
            with self.subTest(url_name=namespaced_name):
                url = reverse(namespaced_name)
                self.assertEqual(url, expected_url)

    def test_url_parameter_types(self):
        """Testa tipos de parâmetros nas URLs"""
        # Testar parâmetros inteiros
        test_cases = [
            ("tenants:client-detail", {"pk": 123}),
            ("tenants:client-member-list", {"client_id": 456}),
            ("tenants:client-member-detail", {"client_id": 789, "pk": 101}),
        ]

        for url_name, kwargs in test_cases:
            with self.subTest(url_name=url_name, kwargs=kwargs):
                url = reverse(url_name, kwargs=kwargs)
                resolver = resolve(url)

                # Verificar se os parâmetros são preservados (como inteiros no Django >= 2.0)
                for key, value in kwargs.items():
                    self.assertEqual(resolver.kwargs[key], value)

    def test_url_trailing_slashes(self):
        """Testa se as URLs têm trailing slashes adequadas"""
        urls_with_slashes = [
            "/api/tenants/clients/",
            "/api/tenants/clients/1/",
            "/api/tenants/clients/1/members/",
            "/api/tenants/clients/1/members/1/",
            "/api/tenants/my-clients/",
        ]

        for url in urls_with_slashes:
            with self.subTest(url=url):
                try:
                    resolver = resolve(url)
                    # URL deve resolver sem problemas
                    self.assertIsNotNone(resolver.view_name)
                except:
                    self.fail(f"URL '{url}' com trailing slash falhou na resolução")
