# ===============================================================
# Título: URLs do App Espacos - Espaço Vital
# Descrição: Configuração de URLs para espaços terapêuticos
# Autor: Will | Empresa: Espaço Vital
# Data: 14/09/2025
# ===============================================================

from django.urls import path, include
from . import views

# Namespace do app espacos
app_name = 'espacos'

urlpatterns = [
    # ===============================================================
    # PÁGINA INICIAL DE ESPAÇOS
    # ===============================================================
    
    # Página inicial de espaços (redirecionamento)
    # IMPORTANTE: Deve vir primeiro para não conflitar
    path('', views.EspacoHomeView.as_view(), name='home'),
    
    # ===============================================================
    # DASHBOARD PRIVADO DO ESPAÇO (TAREFA 9)
    # IMPORTANTE: Deve vir ANTES de <slug:slug>/ para não conflitar
    # ===============================================================
    
    # Dashboard principal do espaço
    # URL: /espacos/dashboard/
    # Área privada com estatísticas e visão geral
    path(
        'dashboard/',
        views.DashboardEspacoView.as_view(),
        name='dashboard'
    ),
    
    # Editar perfil do espaço
    # URL: /espacos/dashboard/editar/
    # Formulário completo para edição de dados do espaço
    path(
        'dashboard/editar/',
        views.DashboardEditarEspacoView.as_view(),
        name='dashboard_editar'
    ),
    
    # Gerenciar terapeutas vinculados
    # URL: /espacos/dashboard/terapeutas/
    # Listar e aprovar terapeutas que usam o espaço
    path(
        'dashboard/terapeutas/',
        views.DashboardTerapeutasVinculadosView.as_view(),
        name='dashboard_terapeutas'
    ),
    
    # Gerenciar disponibilidade/calendário
    # URL: /espacos/dashboard/disponibilidade/
    # Configurar horários e reservas do espaço
    path(
        'dashboard/disponibilidade/',
        views.DashboardDisponibilidadeView.as_view(),
        name='dashboard_disponibilidade'
    ),
    
    # ===============================================================
    # DASHBOARD - GERENCIAMENTO DE SALAS (AGENDAMENTO)
    # ===============================================================
    
    # Listar salas do espaço
    # URL: /espacos/dashboard/salas/
    # Lista todas as salas cadastradas no espaço
    path(
        'dashboard/salas/',
        views.DashboardSalasView.as_view(),
        name='dashboard_salas'
    ),
    
    # Criar nova sala
    # URL: /espacos/dashboard/salas/nova/
    # Formulário para cadastrar nova sala
    path(
        'dashboard/salas/nova/',
        views.DashboardSalaCriarView.as_view(),
        name='dashboard_sala_criar'
    ),
    
    # Editar sala existente
    # URL: /espacos/dashboard/salas/<id>/editar/
    # Formulário para editar dados da sala
    path(
        'dashboard/salas/<int:pk>/editar/',
        views.DashboardSalaEditarView.as_view(),
        name='dashboard_sala_editar'
    ),
    
    # Ativar/Desativar sala
    # URL: /espacos/dashboard/salas/<id>/toggle/
    # Alterna status is_active da sala
    path(
        'dashboard/salas/<int:pk>/toggle/',
        views.DashboardSalaToggleView.as_view(),
        name='dashboard_sala_toggle'
    ),
    
    # Gerenciar pagamento recebidos
    # URL: /espacos/dashboard/pagamentos/
    # Ver pagamentos de terapeutas pelo uso do espaço
    path(
        'dashboard/pagamentos/',
        views.DashboardPagamentosEspacoView.as_view(),
        name='dashboard_pagamentos'
    ),
    
    # Gerenciar assinatura/plano
    # URL: /espacos/dashboard/assinatura/
    # Ver plano atual e opções de upgrade (Basic/Premium A/Premium S)
    path(
        'dashboard/assinatura/',
        views.DashboardAssinaturaEspacoView.as_view(),
        name='dashboard_assinatura'
    ),
    
    # ===============================================================
    # URLS PRINCIPAIS DE LISTAGEM E BUSCA
    # ===============================================================
    
    # Busca avançada de espaços (com filtros)
    path('buscar/', views.EspacoListView.as_view(), name='busca_avancada'),
    
    # Listagem simples de espaços (sem filtros)
    path('listagem/', views.EspacoListagemSimplesView.as_view(), name='listagem_simples'),
    
    # Listagem por região/cidade
    path('regiao/<slug:cidade_slug>/', views.EspacoPorRegiaoView.as_view(), name='por_regiao'),
    
    # ===============================================================
    # APIS AJAX PARA FILTROS DINÂMICOS
    # ===============================================================
    
    # API para carregar cidades por estado (AJAX)
    path('api/cidades/<int:estado_id>/', views.CidadesPorEstadoAPIView.as_view(), name='api_cidades'),
    
    # API para filtros de comodidades (AJAX)
    path('api/comodidades/', views.ComodidadesAPIView.as_view(), name='api_comodidades'),
    
    # API para especialidades disponíveis (AJAX)
    path('api/especialidades/', views.EspecialidadesAPIView.as_view(), name='api_especialidades'),
    
    # API para busca HTMX (filtros sem reload)
    path('api/buscar/', views.EspacoBuscaHTMXView.as_view(), name='api_busca_htmx'),
    
    # ===============================================================
    # URLS DE DETALHES E PERFIL (COM SLUG)
    # IMPORTANTE: Devem vir POR ÚLTIMO para não capturar outras rotas
    # ===============================================================
    
    # Perfil completo do espaço
    path('<slug:slug>/', views.EspacoDetailView.as_view(), name='detalhe'),
    
    # Galeria de fotos do espaço
    path('<slug:slug>/galeria/', views.EspacoGaleriaView.as_view(), name='galeria'),
    
    # Formulário de contato com o espaço
    path('<slug:slug>/contato/', views.ContatoEspacoView.as_view(), name='contato'),
    
    # Avaliação do espaço
    path('<slug:slug>/avaliar/', views.AvaliarEspacoView.as_view(), name='avaliar'),
    
    # Estatísticas do espaço (para proprietários)
    path('<slug:slug>/estatisticas/', views.EspacoEstatisticasView.as_view(), name='estatisticas'),
]

# ===============================================================
# PADRÕES DE URL SEGUINDO O LAYOUT:
# ===============================================================

# ESTRUTURA BASEADA NOS LAYOUTS COMPARTILHADOS:
# /espacos/buscar/ - Tela espacoComFiltro.pdf (busca avançada)
# /espacos/listagem/ - Tela espacoSemFiltro.pdf (listagem simples)
# /espacos/regiao/rio-de-janeiro/ - Listagem por região
# /espacos/centro-holistico-zen-rj/ - Perfil do espaço (slug)
# /espacos/centro-holistico-zen-rj/contato/ - Contato
# /espacos/centro-holistico-zen-rj/avaliar/ - Avaliação

# APIS AJAX PARA UX DINÂMICA:
# /espacos/api/cidades/1/ - Cidades do estado (filtro cascata)
# /espacos/api/buscar/ - HTMX para atualizar resultados sem reload