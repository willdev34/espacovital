"""
Título: URLs do Sistema de Agendamento de Salas
Descrição: Configuração de rotas para o app de agendamentos
"""

from django.urls import path
from .views import (
    GetComodidadesEspacoView,
    AgendamentoCriarView,
    AgendamentoDetalheView,
    AgendamentoEditarView,
    AgendamentoCancelarView,
)

app_name = 'agendamentos'

urlpatterns = [
    # ==========================================
    # AJAX VIEWS
    # ==========================================
    path(
        'sala/get-comodidades/',
        GetComodidadesEspacoView.as_view(),
        name='get_comodidades_espaco'
    ),

    # ==========================================
    # CRUD DE AGENDAMENTOS
    # ==========================================

    # Criar novo agendamento
    # URL: /agendamentos/novo/
    path(
        'novo/',
        AgendamentoCriarView.as_view(),
        name='agendamento_create'
    ),

    # Ver detalhes do agendamento
    # URL: /agendamentos/<id>/
    path(
        '<int:pk>/',
        AgendamentoDetalheView.as_view(),
        name='agendamento_detail'
    ),

    # Editar agendamento existente
    # URL: /agendamentos/<id>/editar/
    path(
        '<int:pk>/editar/',
        AgendamentoEditarView.as_view(),
        name='agendamento_update'
    ),

    # Cancelar agendamento
    # URL: /agendamentos/<id>/cancelar/
    path(
        '<int:pk>/cancelar/',
        AgendamentoCancelarView.as_view(),
        name='agendamento_cancelar'
    ),
]