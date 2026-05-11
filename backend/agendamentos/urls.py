"""
Título: URLs do Sistema de Agendamento de Salas
Descrição: Configuração de rotas para o app de agendamentos
Autor: Will
Data: 29/12/2024
Atualizado: 19/01/2026 - Adicionadas rotas do dashboard de agendamentos
"""

from django.urls import path
from .views import GetComodidadesEspacoView

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
    # DASHBOARD - CRUD DE AGENDAMENTOS
    # ==========================================
    
    # Criar novo agendamento
    # URL: /agendamentos/novo/
    # Formulário para criar agendamento de sala
    # path(
    #     'novo/',
    #     AgendamentoCriarView.as_view(),
    #     name='agendamento_create'
    # ),
    
    # Ver detalhes do agendamento
    # URL: /agendamentos/<id>/
    # Página com todos os detalhes do agendamento
    # path(
    #     '<int:pk>/',
    #     AgendamentoDetalheView.as_view(),
    #     name='agendamento_detail'
    # ),
    
    # Editar agendamento existente
    # URL: /agendamentos/<id>/editar/
    # Formulário para editar dados do agendamento
    # path(
    #     '<int:pk>/editar/',
    #     AgendamentoEditarView.as_view(),
    #     name='agendamento_update'
    # ),
    
    # Cancelar agendamento
    # URL: /agendamentos/<id>/cancelar/
    # Action para cancelar um agendamento
    # path(
    #     '<int:pk>/cancelar/',
    #     AgendamentoCancelarView.as_view(),
    #     name='agendamento_cancelar'
    # ),
]