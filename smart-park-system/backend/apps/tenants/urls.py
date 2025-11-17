from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Clientes
    path('clients/', views.ClientListCreateView.as_view(), name='client-list'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client-detail'),
    
    # Membros de clientes
    path('clients/<int:client_id>/members/', views.ClientMemberListView.as_view(), name='client-member-list'),
    path('clients/<int:client_id>/members/<int:pk>/', views.ClientMemberDetailView.as_view(), name='client-member-detail'),
    
    # Meus clientes
    path('my-clients/', views.my_clients_view, name='my-clients'),
]
