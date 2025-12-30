"""
Título: URLs do Sistema de Agendamento de Salas
Descrição: Configuração de rotas para o app de agendamentos
Autor: Will
Data: 29/12/2024
"""

from django.urls import path
from .views import GetComodidadesEspacoView

app_name = 'agendamentos'

urlpatterns = [
    # AJAX Views
    path(
        'sala/get-comodidades/',
        GetComodidadesEspacoView.as_view(),
        name='get_comodidades_espaco'
    ),
]