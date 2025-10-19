# ===============================================================
# Título: URLs Principal - Espaço Vital
# Descrição: Configuração principal de rotas da aplicação
# Autor: Will | Empresa: Espaço Vital
# Data: 12/10/2025
# ===============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import api_estados, api_cidades

# ===============================================================
# URLs Principais da Aplicação
# ===============================================================

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),
    
    # Sistema de autenticação (allauth)
    path('accounts/', include('allauth.urls')),
    
    # App core - páginas principais (home, sobre, etc.)
    path('', include('core.urls')),
    
    # Apps principais
    path('terapeutas/', include('terapeutas.urls')),
    path('espacos/', include('espacos.urls')),
    
    # APIs públicas
    path('api/estados/', api_estados, name='api_estados'),
    path('api/cidades/', api_cidades, name='api_cidades'),
    
    # URLs futuras
    # path('terapias/', include('terapias.urls')),
    # path('blog/', include('blog.urls')),
]

# ===============================================================
# Django Debug Toolbar (apenas em ambiente de desenvolvimento)
# ===============================================================

if settings.DEBUG:
    # Tenta importar e configurar o debug toolbar se estiver instalado
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include('debug_toolbar.urls')),
        ] + urlpatterns
    except ImportError:
        # Debug toolbar não instalado, apenas ignora
        pass

# ===============================================================
# Servir arquivos estáticos e media em desenvolvimento
# ===============================================================

# Arquivos estáticos apenas em desenvolvimento
if settings.DEBUG:
    # Arquivos estáticos (CSS, JS, imagens do projeto)
    # Verifica se STATICFILES_DIRS existe e tem conteúdo antes de usar
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    else:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)