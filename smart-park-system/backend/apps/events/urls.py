from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Eventos de status de vagas
    path('slot-status-events/', views.SlotStatusEventListCreateView.as_view(), name='slot-status-event-list'),
    path('slot-status-events/<int:pk>/', views.SlotStatusEventDetailView.as_view(), name='slot-status-event-detail'),
]
