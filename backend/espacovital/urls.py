# ===============================================================
# Título: URLs Principal - Espaço Vital
# Descrição: Configuração principal de rotas da aplicação
# Autor: Will | Empresa: Espaço VItal
# Data: 30/08/2025
# ===============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import api_estados, api_cidades

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

    path('api/estados/', api_estados, name='api_estados'),

    path('api/cidades/', api_cidades, name='api_cidades'),

    
    # URLs futuras
    # path('terapias/', include('terapias.urls')),
    # path('blog/', include('blog.urls')),
]

# Servir arquivos de media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])