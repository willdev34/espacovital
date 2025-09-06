# ===============================================================
# Título: Views do App Core - Espaço Vital
# Descrição: Views principais da aplicação (home, sobre, etc.)
# Autor: Will
# Data: 30/08/2025
# ===============================================================

from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    View da página inicial do Espaço Vital
    Exibe hero section, terapeutas em destaque, espaços e benefícios
    """
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        """
        Adiciona contexto específico para a home
        Futuramente incluirá terapeutas em destaque, etc.
        """
        context = super().get_context_data(**kwargs)
        
        # Por enquanto contexto básico
        context['page_title'] = 'Espaço Vital - Conectando você ao cuidado terapêutico'
        context['meta_description'] = 'Encontre terapeutas e espaços terapêuticos verificados'
        
        return context


def home_view(request):
    #View função simples para a home (alternativa à classe)
    context = {
        'page_title': 'Espaço Vital - Conectando você ao cuidado terapêutico',
        'meta_description': 'Encontre terapeutas e espaços terapêuticos verificados'
    }
    return render(request, 'core/home.html', context)