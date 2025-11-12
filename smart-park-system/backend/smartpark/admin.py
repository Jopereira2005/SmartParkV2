from django.contrib import admin
from django.contrib.admin import AdminSite


class SmartParkAdminSite(AdminSite):
    """
    AdminSite customizado para administradores do sistema SmartPark.

    Este admin é exclusivo para superusuários e membros da equipe,
    oferecendo acesso completo ao sistema. A interface visual é gerenciada
    pelo Jazzmin.
    """

    site_header = "🏗️ SmartPark - Admin Backoffice"
    site_title = "SmartPark Admin"
    index_title = "Central de Controle e Monitoramento"

    def has_permission(self, request):
        """
        Restringe acesso apenas para superusuários e staff.
        """
        return request.user.is_active and (
            request.user.is_superuser or request.user.is_staff
        )


# Registrar o site admin customizado
admin_site = SmartParkAdminSite(name="smartpark_admin")

# Nota: Os models User e Group são registrados em apps/accounts/admin.py
# para evitar duplicação e permitir customizações específicas

# Configurações globais do admin padrão (para fallback)
admin.site.site_header = "🏗️ SmartPark - Admin Backoffice"
admin.site.site_title = "SmartPark Admin"
admin.site.index_title = "Central de Controle e Monitoramento"
admin.site.enable_nav_sidebar = True
