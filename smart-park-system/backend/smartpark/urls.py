from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .admin import admin_site


urlpatterns = [
    # Admin Backoffice - Restrito para superusuários e staff
    path("admin/", admin_site.urls),
    # Client Backoffice - Portal do cliente
    path("client/", include("apps.client_backoffice.urls")),
    # Páginas públicas - Home e institucionais
    path("", include("apps.public.urls")),
    # OpenAPI/Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    # APIs do projeto
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/tenants/", include("apps.tenants.urls")),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/hardware/", include("apps.hardware.urls")),
    path("api/events/", include("apps.events.urls")),
]
