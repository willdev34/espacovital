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

# URLs do core (não mostrar todas, apenas o final do arquivo)
from .views_onboarding import WelcomeView, SelectPlanView, CreateProfileView

urlpatterns = [
    # Página inicial - rota vazia aponta para home
    path('', views.HomeView.as_view(), name='home'),

    # URLs de Onboarding
    path('onboarding/welcome/', WelcomeView.as_view(), name='onboarding_welcome'),
    path('onboarding/select-plan/', SelectPlanView.as_view(), name='onboarding_select_plan'),
    path('onboarding/create-profile/', CreateProfileView.as_view(), name='onboarding_create_profile'),

    # Seleção de perfil (terapeuta ou espaço)
    # URL: /selecionar-perfil/
    path(
        'selecionar-perfil/',
        views.SelecionarPerfilView.as_view(),
        name='selecionar_perfil'
    ),
    
    # ============================================
    # PÁGINAS INSTITUCIONAIS
    # ============================================
    # Página Sobre o Projeto
    path('sobre/', views.SobreView.as_view(), name='sobre'),
    # Termos de Uso
    path('termos/', views.TermosView.as_view(), name='termos'),
    # Política de Privacidade
    path('privacidade/', views.PrivacidadeView.as_view(), name='privacidade'),
    # Política de Cookies
    path('cookies/', views.CookiesView.as_view(), name='cookies'),
    # Seja um Parceiro
    path('parceiro/', views.ParceiroView.as_view(), name='parceiro'),
    # Perguntas Frequentes (FAQ)
    path('faq/', views.FaqView.as_view(), name='faq'),
    # Contato (Formulário)
    path('contato/', views.ContatoView.as_view(), name='contato'),
    # Indique uma Terapia (Formulário)
    path('indique-terapia/', views.IndiqueTerapiaView.as_view(), name='indique_terapia'),
    
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