from django.urls import path
from . import views

app_name = 'hardware'

urlpatterns = [
    # API Keys
    path('api-keys/', views.ApiKeyListCreateView.as_view(), name='api-key-list'),
    path('api-keys/<int:pk>/', views.ApiKeyDetailView.as_view(), name='api-key-detail'),
    
    # Câmeras
    path('cameras/', views.CameraListCreateView.as_view(), name='camera-list'),
    path('cameras/<int:pk>/', views.CameraDetailView.as_view(), name='camera-detail'),
    
    # Heartbeats
    path('heartbeats/', views.CameraHeartbeatCreateView.as_view(), name='heartbeat-create'),
    path('cameras/<int:camera_id>/heartbeats/', views.CameraHeartbeatListView.as_view(), name='heartbeat-list'),
    
    # Eventos de status de vagas
    path('events/slot-status/', views.slot_status_event_view, name='slot-status-event'),
]
