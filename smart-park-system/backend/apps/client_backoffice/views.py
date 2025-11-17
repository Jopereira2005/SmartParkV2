from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ClientBackofficeView(LoginRequiredMixin, TemplateView):
    """
    Classe base para todas as views do Client Backoffice.
    Garante que apenas usuários autenticados tenham acesso.
    """
    login_url = '/client/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_name'] = self.request.user.get_full_name() or self.request.user.username
        return context


# Views principais do Client Backoffice
class DashboardView(ClientBackofficeView):
    template_name = 'client_backoffice/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboard'
        return context


class EstablishmentsView(ClientBackofficeView):
    template_name = 'client_backoffice/establishments.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Meus Estabelecimentos'
        return context


class ParkingLotsView(ClientBackofficeView):
    template_name = 'client_backoffice/parking_lots.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Meus Estacionamentos'
        return context


class AnalyticsView(ClientBackofficeView):
    template_name = 'client_backoffice/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Analytics'
        return context


class SettingsView(ClientBackofficeView):
    template_name = 'client_backoffice/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Configurações'
        return context


# Views de autenticação
def client_login_view(request):
    """
    View de login específica para clientes.
    """
    if request.user.is_authenticated:
        return redirect('client_backoffice:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo ao Client Backoffice, {user.get_full_name() or user.username}!')
            return redirect('client_backoffice:dashboard')
        else:
            messages.error(request, 'Credenciais inválidas. Tente novamente.')
    
    return render(request, 'client_backoffice/login.html', {
        'page_title': 'Login - Client Backoffice'
    })


@login_required(login_url='/client/login/')
def client_logout_view(request):
    """
    View de logout para clientes.
    """
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('client_backoffice:login')
