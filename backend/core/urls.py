# ===============================================================
# Título: URLs do App Core - Espaço Vital
# Descrição: Configuração de rotas do app core (home, sobre, etc.)
# Autor: Will
# Data: 30/08/2025
# ===============================================================

from django.urls import path
from . import views

# Nome do app para namespace das URLs
app_name = 'core'

urlpatterns = [
    # Página inicial - rota vazia aponta para home
    path('', views.HomeView.as_view(), name='home'),
    
    # URLs futuras do core
    # path('sobre/', views.SobreView.as_view(), name='sobre'),
    # path('contato/', views.ContatoView.as_view(), name='contato'),
]