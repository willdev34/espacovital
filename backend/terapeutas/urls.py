# ===============================================================
# Título: URLs do App Terapeutas - Espaço Vital
# Descrição: Configuração de rotas para busca e perfil de terapeutas
# Autor: Will | Empresa: Espaço VItal
# Data: 13/09/2025
# ===============================================================

from django.urls import path
from . import views

# Nome do app para namespace das URLs
app_name = 'terapeutas'

urlpatterns = [
    # ============================================
    # PÁGINAS PRINCIPAIS
    # ============================================
    
    # Busca avançada de terapeutas (página principal)
    # URL: /terapeutas/
    # Baseada no layout da busca avançada compartilhado
    path(
        '', 
        views.TerapeutaListView.as_view(), 
        name='busca_avancada'
    ),
    
    # Busca avançada com parâmetros específicos
    # URL: /terapeutas/buscar/
    path(
        'buscar/', 
        views.TerapeutaListView.as_view(), 
        name='buscar'
    ),
    
    # Listagem simples sem filtros
    # URL: /terapeutas/lista/
    # Baseada no layout sem filtro compartilhado
    path(
        'lista/', 
        views.terapeutas_sem_filtro, 
        name='listagem_simples'
    ),
    
    # Listagem por especialidade (sem filtros)
    # URL: /terapeutas/especialidade/massoterapia/
    path(
        'especialidade/<slug:especialidade_slug>/', 
        views.terapeutas_sem_filtro, 
        name='por_especialidade'
    ),
    
    # ============================================
    # PERFIL DO TERAPEUTA
    # ============================================
    
    # Perfil completo do terapeuta
    # URL: /terapeutas/perfil/ana-silva/
    path(
        'perfil/<slug:slug>/', 
        views.TerapeutaDetailView.as_view(), 
        name='profile'
    ),
    
    # Formulário de contato com terapeuta
    # URL: /terapeutas/contatar/ana-silva/
    path(
        'contatar/<slug:terapeuta_slug>/', 
        views.contatar_terapeuta, 
        name='contatar'
    ),
    
    # ============================================
    # APIS AJAX
    # ============================================
    
    # API para buscar cidades por estado
    # URL: /terapeutas/api/cidades-por-estado/
    # Para filtro de localização dinâmico
    path(
        'api/cidades-por-estado/', 
        views.cidades_por_estado_ajax, 
        name='cidades_por_estado_ajax'
    ),
    
    # API para busca de terapeutas (autocomplete)
    # URL: /terapeutas/api/buscar/
    # Para o campo de busca do hero section
    path(
        'api/buscar/', 
        views.busca_terapeutas_ajax, 
        name='busca_ajax'
    ),
    
    # ============================================
    # URLs DE LOCALIZAÇÃO (para SEO)
    # ============================================
    
    # Terapeutas por cidade
    # URL: /terapeutas/rio-de-janeiro-rj/
    # Futura implementação para SEO local
    # path(
    #     '<slug:cidade_slug>-<slug:estado_slug>/',
    #     views.terapeutas_por_cidade,
    #     name='por_cidade'
    # ),
    
    # ============================================
    # URLs PARA CATEGORIAS/FILTROS ESPECÍFICOS
    # ============================================
    
    # Terapeutas em destaque (para home)
    # URL: /terapeutas/destaques/
    # path(
    #     'destaques/',
    #     views.terapeutas_destaque,
    #     name='destaques'
    # ),
    
    # Terapeutas premium/VIP
    # URL: /terapeutas/premium/
    # path(
    #     'premium/',
    #     views.terapeutas_premium,
    #     name='premium'
    # ),
    
    # ============================================
    # URLs DE AVALIAÇÃO (futuras)
    # ============================================
    
    # Avaliar terapeuta (apenas usuários logados)
    # URL: /terapeutas/avaliar/ana-silva/
    # path(
    #     'avaliar/<slug:terapeuta_slug>/',
    #     views.avaliar_terapeuta,
    #     name='avaliar'
    # ),
]

# ============================================
# COMENTÁRIOS SOBRE AS URLs
# ============================================

"""
ESTRUTURA DAS URLs DO APP TERAPEUTAS:

1. PÁGINAS PRINCIPAIS:
   - '' → Busca avançada (página principal)
   - 'buscar/' → Mesma busca avançada (URL alternativa)
   - 'lista/' → Listagem simples sem filtros
   - 'especialidade/<slug>/' → Filtro por especialidade

2. PERFIL:
   - 'perfil/<slug>/' → Perfil completo
   - 'contatar/<slug>/' → Formulário de contato

3. APIs AJAX:
   - 'api/cidades-por-estado/' → Filtro dinâmico
   - 'api/buscar/' → Autocomplete do hero

4. FUTURAS IMPLEMENTAÇÕES (comentadas):
   - URLs por localização (SEO)
   - Categorias específicas (destaque, premium)
   - Sistema de avaliações

EXEMPLOS DE USO:
- Busca geral: /terapeutas/
- Com filtros: /terapeutas/?cidade=1&especialidades=1,2&acessibilidade=sim
- Por especialidade: /terapeutas/especialidade/massoterapia/
- Perfil: /terapeutas/perfil/ana-silva/
- Contato: /terapeutas/contatar/ana-silva/
- AJAX cidades: /terapeutas/api/cidades-por-estado/?estado_id=1
- AJAX busca: /terapeutas/api/buscar/?q=ana

INTEGRAÇÃO COM URLS PRINCIPAIS:
No arquivo espacovital/urls.py, adicionar:
path('terapeutas/', include('terapeutas.urls')),
"""