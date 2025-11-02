# ===============================================================
# Título: URLs do App Terapias
# Descrição: Rotas para listagem e detalhes de terapias/especialidades
# Autor: Will
# Data: Novembro 2025
# ===============================================================

from django.urls import path
from . import views

app_name = 'terapias'

urlpatterns = [
    # Página de terapias em destaque (hero section)
    path('', views.TerapiasDestaquesView.as_view(), name='destaques'),
    
    # Listagem alfabética (A-Z)
    path('todas/', views.TerapiasListagemView.as_view(), name='listagem'),
    
    # Página individual da terapia
    path('<slug:slug>/', views.TerapiaDetalheView.as_view(), name='detalhe'),
]