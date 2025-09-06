# ===============================================================
# Título: URLs Principal - Espaço Vital
# Descrição: Configuração principal de rotas da aplicação
# Autor: Will
# Data: 30/08/2025
# ===============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),
    
    # Sistema de autenticação (allauth)
    path('accounts/', include('allauth.urls')),
    
    # App core - páginas principais (home, sobre, etc.)
    path('', include('core.urls')),
    
    # Apps principais - URLs futuras
    # path('terapeutas/', include('terapeutas.urls')),
    # path('espacos/', include('espacos.urls')),
    # path('terapias/', include('terapias.urls')),
    # path('blog/', include('blog.urls')),
]

# Servir arquivos de media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])