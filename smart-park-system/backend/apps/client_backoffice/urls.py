from django.urls import path
from . import views

app_name = 'client_backoffice'

urlpatterns = [
    # Autenticação
    path('login/', views.client_login_view, name='login'),
    path('logout/', views.client_logout_view, name='logout'),
    
    # Dashboard principal
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard_alt'),
    
    # Seções principais
    path('establishments/', views.EstablishmentsView.as_view(), name='establishments'),
    path('parking-lots/', views.ParkingLotsView.as_view(), name='parking_lots'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]
