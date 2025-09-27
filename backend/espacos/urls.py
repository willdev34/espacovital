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
    # URLS PRINCIPAIS DE LISTAGEM E BUSCA
    # ===============================================================
    
    # Busca avançada de espaços (com filtros)
    path('buscar/', views.EspacoListView.as_view(), name='busca_avancada'),
    
    # Listagem simples de espaços (sem filtros)
    path('listagem/', views.EspacoListagemSimplesView.as_view(), name='listagem_simples'),
    
    # Listagem por região/cidade
    path('regiao/<slug:cidade_slug>/', views.EspacoPorRegiaoView.as_view(), name='por_regiao'),
    
    # ===============================================================
    # URLS DE DETALHES E PERFIL
    # ===============================================================
    
    # Perfil completo do espaço
    path('<slug:slug>/', views.EspacoDetailView.as_view(), name='detalhe'),
    
    # Galeria de fotos do espaço
    path('<slug:slug>/galeria/', views.EspacoGaleriaView.as_view(), name='galeria'),
    
    # ===============================================================
    # URLS DE CONTATO E INTERAÇÃO
    # ===============================================================
    
    # Formulário de contato com o espaço
    path('<slug:slug>/contato/', views.ContatoEspacoView.as_view(), name='contato'),
    
    # Avaliação do espaço
    path('<slug:slug>/avaliar/', views.AvaliarEspacoView.as_view(), name='avaliar'),
    
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
    # URLS DE ESTATÍSTICAS E DADOS
    # ===============================================================
    
    # Estatísticas do espaço (para proprietários)
    path('<slug:slug>/estatisticas/', views.EspacoEstatisticasView.as_view(), name='estatisticas'),
    
    # ===============================================================
    # URLS AUXILIARES
    # ===============================================================
    
    # Página inicial de espaços (redirecionamento)
    path('', views.EspacoHomeView.as_view(), name='home'),
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