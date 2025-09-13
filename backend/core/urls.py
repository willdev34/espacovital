# ===============================================================
# Título: URLs do App Core - Espaço Vital (Versão Atualizada)  
# Descrição: Configuração de rotas do app core com novas funcionalidades
# Autor: Will | Empresa: Espaço VItal
# Data: 07/09/2025
# ===============================================================

from django.urls import path
from . import views

# Nome do app para namespace das URLs
app_name = 'core'

urlpatterns = [
    # Página inicial - rota vazia aponta para home
    path('', views.HomeView.as_view(), name='home'),
    
    # Busca AJAX para terapeutas (para autocomplete no hero)
    path('api/search/therapists/', views.search_therapists_ajax, name='search_therapists_ajax'),
    
    # Busca AJAX para espaços 
    path('api/search/spaces/', views.search_spaces_ajax, name='search_spaces_ajax'),
    
    # Páginas institucionais (para implementação futura)
    path('sobre/', views.AboutView.as_view(), name='about'),
    path('contato/', views.ContactView.as_view(), name='contact'),
    
    # View função alternativa para home (se preferir usar)
    # path('home-func/', views.home_view, name='home_function'),
]