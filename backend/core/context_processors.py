# ===============================================================
# Título: Context Processors - Espaço Vital
# Descrição: Dados globais disponíveis em todos os templates
# Autor: Will
# Data: 07/09/2025
# ===============================================================

from django.conf import settings


def global_context(request):
    """
    Context processor que adiciona dados globais a todos os templates
    Inclui informações do site, navegação, etc.
    """
    
    # Menu principal de navegação
    main_navigation = [
        {
            'name': 'Buscar Terapeuta',
            'url': '#',  # Futuramente: reverse('terapeutas:search')
            'icon': 'user',
            'active': False
        },
        {
            'name': 'Terapias',
            'url': '#',  # Futuramente: reverse('terapias:list')
            'icon': 'heart',
            'active': False
        },
        {
            'name': 'Espaços',
            'url': '#',  # Futuramente: reverse('espacos:list')
            'icon': 'map-pin',
            'active': False
        },
        {
            'name': 'Blog',
            'url': '#',  # Futuramente: reverse('blog:list')
            'icon': 'book-open',
            'active': False
        },
        {
            'name': 'Sobre',
            'url': '#',  # Futuramente: reverse('core:about')
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
    
    # Informações gerais do site
    site_info = {
        'name': 'Espaço Vital',
        'tagline': 'Conectando você ao cuidado terapêutico que transforma',
        'description': 'Plataforma que conecta pessoas a terapeutas e espaços terapêuticos verificados',
        'email': 'contato@espacovital.com.br',
        'phone': '+55 (21) 99999-9999',
        'address': 'Rio de Janeiro, RJ',
        'founded_year': 2025,
        'current_year': 2025
    }
    
    # Estatísticas gerais (placeholder - futuramente vir do banco)
    site_stats = {
        'total_therapists': 247,
        'total_spaces': 89,
        'total_therapies': 15,
        'total_cities': 12,
        'total_articles': 156,
        'total_reviews': 1840
    }
    
    # Configurações de SEO padrão
    default_seo = {
        'meta_description': getattr(settings, 'DEFAULT_META_DESCRIPTION', ''),
        'meta_keywords': getattr(settings, 'DEFAULT_META_KEYWORDS', ''),
        'og_image': '/static/images/og-image.jpg',  # Imagem padrão para compartilhamento
        'twitter_card': 'summary_large_image'
    }
    
    # Verificar se usuário está logado e suas informações
    user_context = {}
    if request.user.is_authenticated:
        user_context = {
            'is_therapist': False,  # Verificar se user tem perfil de terapeuta
            'is_space_owner': False,  # Verificar se user é dono de espaço
            'has_notifications': False,  # Verificar notificações pendentes
            'favorite_therapists_count': 0,  # Terapeutas favoritados
            'favorite_spaces_count': 0,  # Espaços favoritados
        }
    
    # Detectar se é mobile baseado no user agent
    is_mobile = False
    if request.META.get('HTTP_USER_AGENT'):
        user_agent = request.META['HTTP_USER_AGENT'].lower()
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
        is_mobile = any(indicator in user_agent for indicator in mobile_indicators)
    
    return {
        'MAIN_NAVIGATION': main_navigation,
        'FOOTER_LINKS': footer_links,
        'SOCIAL_MEDIA': social_media,
        'SITE_INFO': site_info,
        'SITE_STATS': site_stats,
        'DEFAULT_SEO': default_seo,
        'USER_CONTEXT': user_context,
        'IS_MOBILE': is_mobile,
        'DEBUG': settings.DEBUG,
    }