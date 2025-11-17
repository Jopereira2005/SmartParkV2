from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Este app core agora contém utilitários e mixins compartilhados
# As URLs específicas de cada domínio ficam em seus respectivos apps

urlpatterns = [
    # URLs vazias - todas foram movidas para apps específicos
    # O core serve como base para funcionalidades compartilhadas
]
