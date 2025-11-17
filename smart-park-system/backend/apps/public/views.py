from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse


def home_view(request):
    """
    View simples para testar se as URLs estão funcionando.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SmartPark - Home</title>
    </head>
    <body>
        <h1>🅿️ SmartPark - Sistema funcionando!</h1>
        <p>Esta é a página inicial do SmartPark.</p>
        <ul>
            <li><a href="/about/">Sobre</a></li>
            <li><a href="/contact/">Contato</a></li>
            <li><a href="/admin/">Admin Backoffice</a></li>
            <li><a href="/api/docs/">API Docs</a></li>
        </ul>
    </body>
    </html>
    """
    return HttpResponse(html)


class HomeView(TemplateView):
    """
    Página inicial pública do SmartPark.
    """

    template_name = "public/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "SmartPark - Sistema Inteligente de Estacionamento",
                "page_type": "public",
                "features": [
                    {
                        "title": "Monitoramento em Tempo Real",
                        "description": "Acompanhe a ocupação das vagas em tempo real através de câmeras inteligentes.",
                        "icon": "📹",
                    },
                    {
                        "title": "Dashboard Intuitivo",
                        "description": "Interface moderna e fácil de usar para gestão completa do estacionamento.",
                        "icon": "📊",
                    },
                    {
                        "title": "API Robusta",
                        "description": "Integração simples com sistemas existentes através de nossa API RESTful.",
                        "icon": "🔌",
                    },
                ],
            }
        )
        return context


class AboutView(TemplateView):
    """
    Página sobre o SmartPark.
    """

    template_name = "public/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Sobre o SmartPark",
                "page_type": "public",
            }
        )
        return context


class ContactView(TemplateView):
    """
    Página de contato.
    """

    template_name = "public/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Contato - SmartPark",
                "page_type": "public",
            }
        )
        return context


def health_check(request):
    """
    Endpoint simples para verificação de saúde do sistema.
    """
    return JsonResponse(
        {"status": "ok", "service": "SmartPark API", "version": "1.0.0"}
    )
