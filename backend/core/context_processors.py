# ===============================================================
# Título: Context Processors - Espaço Vital
# Descrição: Dados globais disponíveis em todos os templates
# Autor: Will | Empresa: Espaço Vital
# Data: 07/09/2025
# ===============================================================

from django.conf import settings
from terapeutas.models import Especialidade
from core.models import Pais, Estado, Cidade


def global_context(request):
    """
    Context processor que adiciona dados globais a todos os templates
    Inclui informações do site, navegação, etc.
    """
    
    # Menu principal de navegação
    main_navigation = [
        {
            'name': 'Buscar Terapeuta',
            'url': '#',
            'icon': 'user',
            'active': False
        },
        {
            'name': 'Terapias',
            'url': '#',
            'icon': 'heart',
            'active': False
        },
        {
            'name': 'Espaços',
            'url': '#',
            'icon': 'map-pin',
            'active': False
        },
        {
            'name': 'Blog',
            'url': '#',
            'icon': 'book-open',
            'active': False
        },
        {
            'name': 'Sobre',
            'url': '#',
            'icon': 'info',
            'active': False
        }
    ]
    
    # Links do footer organizados por seção
    footer_links = {
        'para_voce': [
            {'name': 'Busque um terapeuta', 'url': '#'},
            {'name': 'Encontre um espaço', 'url': '#'},
            {'name': 'Artigos do Blog', 'url': '#'},
            {'name': 'Qual terapia escolher?', 'url': '#'},
        ],
        'empresa': [
            {'name': 'Sobre', 'url': '#'},
            {'name': 'Contatos', 'url': '#'},
            {'name': 'Parceria & Publicidade', 'url': '#'},
            {'name': 'Política de cookies', 'url': '#'},
            {'name': 'Aviso de privacidade', 'url': '#'},
            {'name': 'Termos & Denúncias', 'url': '#'},
        ]
    }
    
    # Redes sociais
    social_media = [
        {
            'name': 'Instagram',
            'url': 'https://instagram.com/espacovital',
            'icon': 'instagram',
            'color': 'text-pink-500'
        },
        {
            'name': 'Facebook',
            'url': 'https://facebook.com/espacovital',
            'icon': 'facebook',
            'color': 'text-blue-600'
        },
        {
            'name': 'Twitter/X',
            'url': 'https://twitter.com/espacovital',
            'icon': 'twitter',
            'color': 'text-gray-900'
        },
        {
            'name': 'LinkedIn',
            'url': 'https://linkedin.com/company/espacovital',
            'icon': 'linkedin',
            'color': 'text-blue-700'
        }
    ]
    
    # ============================================
    # DADOS PARA O MODAL DE BUSCA (EM TODAS AS PÁGINAS)
    # ============================================
    
    # TODAS as especialidades/terapias
    especialidades_modal = Especialidade.objects.filter(
        is_active=True
    ).order_by('nome')
    
    # Todos os países cadastrados
    paises_modal = Pais.objects.filter(
        ativo=True
    ).order_by('nome')
    
    # Todos os estados cadastrados
    estados_modal = Estado.objects.filter(
        ativo=True
    ).select_related('pais').order_by('nome')
    
    # Todas as cidades cadastradas
    cidades_modal = Cidade.objects.filter(
        ativo=True
    ).select_related('estado', 'estado__pais').order_by('nome')
    
    return {
        'SITE_NAME': 'Espaço Vital',
        'main_navigation': main_navigation,
        'footer_links': footer_links,
        'social_media': social_media,
        'especialidades_modal': especialidades_modal,
        'paises_modal': paises_modal,
        'estados_modal': estados_modal,
        'cidades_modal': cidades_modal,
    }