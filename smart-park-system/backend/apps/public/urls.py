from django.urls import path
from . import views

app_name = "public"

urlpatterns = [
    # Página inicial
    path("", views.HomeView.as_view(), name="home"),
    # Páginas institucionais
    path("about/", views.AboutView.as_view(), name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    # Health check para monitoramento
    path("health/", views.health_check, name="health_check"),
]
