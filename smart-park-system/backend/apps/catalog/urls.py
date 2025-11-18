from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Tipos de loja
    path('store-types/', views.StoreTypeListView.as_view(), name='store-type-list'),
    
    # Estabelecimentos
    path('establishments/', views.EstablishmentListCreateView.as_view(), name='establishment-list'),
    path('establishments/create-with-address/', views.EstablishmentCreateWithAddressView.as_view(), name='establishment-create-with-address'),
    path('establishments/<int:pk>/', views.EstablishmentDetailView.as_view(), name='establishment-detail'),
    path('establishments/<int:pk>/establishment-address/', views.UpdateEstablishmentAddressView.as_view(), name='establishment-address-update'),
    path('establishments/<int:pk>/update-with-address/', views.UpdateEstablishmentWithAddressView.as_view(), name='establishment-update-with-address'),
    
    # Lotes
    path('lots/', views.LotListCreateView.as_view(), name='lot-list'),
    path('lots/<int:pk>/', views.LotDetailView.as_view(), name='lot-detail'),
    
    # Vagas
    path('lots/<int:lot_id>/slots/', views.SlotListCreateView.as_view(), name='slot-list'),
    path('slots/<int:pk>/', views.SlotDetailView.as_view(), name='slot-detail'),
    
    # Tipos de vaga
    path('slot-types/', views.SlotTypeListView.as_view(), name='slot-type-list'),
    
    # Tipos de veículo
    path('vehicle-types/', views.VehicleTypeListView.as_view(), name='vehicle-type-list'),
    
    # Status das vagas
    path('slot-status/<int:pk>/', views.SlotStatusDetailView.as_view(), name='slot-status-detail'),
    path('slots/<int:slot_id>/history/', views.SlotStatusHistoryListView.as_view(), name='slot-status-history'),
    
    # Endpoints públicos
    path('public/establishments/', views.public_establishments_view, name='public-establishments'),
    path('public/establishments/<int:establishment_id>/slots/', views.public_slot_status_view, name='public-slot-status'),
    path('public/establishments/<int:establishment_id>/lots/', views.public_establishment_lots_view, name='public-establishment-lots'),
    path('public/establishments/lots/', views.public_all_establishments_lots_view, name='public-all-establishments-lots'),
]
