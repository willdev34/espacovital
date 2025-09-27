# ===============================================================
# Título: URLs do App Core - Espaço Vital (Versão Simples)
# Descrição: Configuração básica de rotas do app core
# Autor: Will | Empresa: Espaço Vital
# Data: 14/09/2025
# ===============================================================

from django.urls import path
from . import views

# Nome do app para namespace das URLs
app_name = 'core'

urlpatterns = [
    # Página inicial - rota vazia aponta para home
    path('', views.HomeView.as_view(), name='home'),
    
    # Páginas institucionais (comentadas até implementar)
    # path('sobre/', views.AboutView.as_view(), name='about'),
    # path('contato/', views.ContactView.as_view(), name='contact'),
    
    # APIs AJAX (comentadas até implementar)
    # path('api/search/therapists/', views.search_therapists_ajax, name='search_therapists_ajax'),
    # path('api/search/spaces/', views.search_spaces_ajax, name='search_spaces_ajax'),
]

# ===============================================================
# NOTAS SOBRE AS URLs:
# ===============================================================

"""
ESTRUTURA DAS URLs DO APP CORE:

1. PÁGINA PRINCIPAL:
   - '' → HomeView (página inicial)

2. APIs AJAX:
   - 'api/search/therapists/' → Busca terapeutas (autocomplete)
   - 'api/search/spaces/' → Busca espaços (autocomplete)

3. PÁGINAS INSTITUCIONAIS:
   - 'sobre/' → Página sobre (AboutView)
   - 'contato/' → Página de contato (ContactView)

EXEMPLOS DE USO:
- Home: / (raiz do site)
- AJAX terapeutas: /api/search/therapists/?q=ana
- AJAX espaços: /api/search/spaces/?q=centro
- Sobre: /sobre/
- Contato: /contato/

INTEGRAÇÃO COM OUTRAS APPS:
- Terapeutas: /terapeutas/ (definido em espacovital/urls.py)
- Espaços: /espacos/ (definido em espacovital/urls.py)
- Blog: /blog/ (quando implementar)
"""