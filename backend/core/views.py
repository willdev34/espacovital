# ===============================================================
# Título: Views do App Core - Espaço Vital (Versão Atualizada)
# Descrição: Views principais da aplicação com contexto otimizado
# Autor: Will
# Data: 07/09/2025
# ===============================================================

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator


class HomeView(TemplateView):
    """
    View da página inicial do Espaço Vital
    Exibe hero section, terapeutas em destaque, espaços e benefícios
    """
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        """
        Adiciona contexto específico para a home
        Incluindo terapeutas em destaque, espaços e dados dinâmicos
        """
        context = super().get_context_data(**kwargs)
        
        # Meta dados da página
        context['page_title'] = 'Espaço Vital - Conectando você ao cuidado terapêutico'
        context['meta_description'] = 'Encontre terapeutas e espaços terapêuticos verificados. Conectamos você ao cuidado que transforma sua vida.'
        
        # Dados para seção de terapeutas em destaque
        # Quando tiver o model Terapeuta, buscar os destacados aqui
        context['featured_therapists'] = [
            {
                'id': 1,
                'name': 'Ana Silva',
                'specialties': 'Massoterapia • Reiki',
                'location': 'Rio de Janeiro, RJ',
                'verified': True,
                'photo': None,  # Quando tiver upload de fotos
                'rating': 4.9,
                'total_reviews': 127
            },
            {
                'id': 2,
                'name': 'Carlos Mendes',
                'specialties': 'Yoga • Meditação',
                'location': 'São Paulo, SP',
                'verified': True,
                'photo': None,
                'rating': 4.8,
                'total_reviews': 89
            },
            {
                'id': 3,
                'name': 'Marina Costa',
                'specialties': 'Aromaterapia • Cristaloterapia',
                'location': 'Belo Horizonte, MG',
                'verified': True,
                'photo': None,
                'rating': 4.9,
                'total_reviews': 156
            },
            {
                'id': 4,
                'name': 'Roberto Lima',
                'specialties': 'Shiatsu • Reflexologia',
                'location': 'Porto Alegre, RS',
                'verified': True,
                'photo': None,
                'rating': 4.7,
                'total_reviews': 94
            }
        ]
        
        # Dados para seção de espaços terapêuticos
        context['featured_spaces'] = [
            {
                'id': 1,
                'name': 'Centro de Bem-Estar',
                'location': 'Centro / RJ',
                'therapists_count': 3,
                'color_class': 'from-yellow-200 via-orange-300 to-amber-400',
                'available_therapies': ['Massoterapia', 'Reiki', 'Yoga']
            },
            {
                'id': 2,
                'name': 'Espaço Harmonia',
                'location': 'Santa da Tijuca / RJ',
                'therapists_count': 5,
                'color_class': 'from-amber-400 via-orange-500 to-red-500',
                'available_therapies': ['Shiatsu', 'Aromaterapia', 'Cristaloterapia']
            },
            {
                'id': 3,
                'name': 'Vila Zen',
                'location': 'Vila Madalena / SP',
                'therapists_count': 8,
                'color_class': 'from-red-400 via-red-600 to-red-800',
                'available_therapies': ['Tantra', 'Yoga', 'Meditação']
            },
            {
                'id': 4,
                'name': 'Santuário Natural',
                'location': 'Santo Inácio / RJ',
                'therapists_count': 2,
                'color_class': 'from-gray-300 via-gray-500 to-gray-700',
                'available_therapies': ['Reflexologia', 'Massoterapia']
            },
            {
                'id': 5,
                'name': 'Espaço Vital',
                'location': 'Vilinha / ES',
                'therapists_count': 4,
                'color_class': 'from-amber-300 via-yellow-400 to-orange-500',
                'available_therapies': ['Reiki', 'Cristaloterapia', 'Aromaterapia']
            }
        ]
        
        # Dados para benefícios da terapia
        context['therapy_benefits'] = [
            {
                'title': 'Autoconhecimento',
                'description': 'Descubra suas próprias competências e desperte vitalidade e felicidade. A terapia ajuda você a descobrir potenciais antes desconhecidos sobre quem você realmente é.',
                'icon': 'star'
            },
            {
                'title': 'Resgate da autoestima',
                'description': 'Reconecte-se com seu corpo e valor pessoal. Valorize suas competências e desenvolva sua autoestima de forma genuína e duradoura.',
                'icon': 'heart'
            },
            {
                'title': 'Liberação de traumas',
                'description': 'Transforme traumas em cura através de um ambiente seguro e cuidadoso, com técnicas terapêuticas especializadas em uma atmosfera única e acolhedora.',
                'icon': 'check-circle'
            },
            {
                'title': 'Expansão da consciência',
                'description': 'Amplie sua percepção e consciência sobre a vida. Desenvolva uma visão mais clara sobre seus processos internos e externos.',
                'icon': 'search'
            },
            {
                'title': 'Melhoria nos relacionamentos',
                'description': 'Desenvolva empatia, clareza na comunicação e construa relacionamentos mais saudáveis com maior velocidade e afeto genuíno.',
                'icon': 'users'
            },
            {
                'title': 'Redução do estresse',
                'description': 'Aprenda técnicas que promovem relaxamento físico e mental. Trabalhe a ansiedade e encontre paz em uma atmosfera acolhedora e transformadora.',
                'icon': 'check-circle'
            }
        ]
        
        # Dados para "Por que utilizar o Espaço Vital"
        context['platform_benefits'] = [
            {
                'title': 'Profissionais verificados',
                'description': 'Garantia de segurança e credibilidade com todos os terapeutas aprovados.',
                'icon': 'shield'
            },
            {
                'title': 'Espaços selecionados',
                'description': 'Locais cuidadosamente escolhidos que representam a ética terapêutica.',
                'icon': 'tag'
            },
            {
                'title': 'Filtro por especialidade',
                'description': 'Encontre exatamente o que procura de forma rápida e precisa.',
                'icon': 'search'
            },
            {
                'title': 'Conteúdo educativo',
                'description': 'Aprenda sobre autocuidado através de nossa base científica.',
                'icon': 'book'
            }
        ]
        
        # Dados para blog (últimos artigos)
        context['latest_articles'] = [
            {
                'id': 1,
                'title': 'A importância do toque consciente na terapia',
                'excerpt': 'Descubra como o toque terapêutico pode ser uma ferramenta poderosa de cura e conexão, promovendo bem-estar físico e emocional através de técnicas conscientes.',
                'author': {
                    'name': 'Luiza Marques',
                    'specialty': 'Massoterapeuta'
                },
                'featured_image': None,  # Quando tiver upload de imagens
                'color_class': 'from-gray-400 via-gray-600 to-gray-800',
                'published_date': '2025-09-05',
                'reading_time': 5
            },
            {
                'id': 2,
                'title': 'Como a respiração pode transformar seu estado mental',
                'excerpt': 'Explore técnicas de respiração consciente que podem revolucionar sua saúde mental, reduzir ansiedade e promover um estado de calma e clareza mental duradouro.',
                'author': {
                    'name': 'Marcelo Araujo',
                    'specialty': 'Yoga'
                },
                'featured_image': None,
                'color_class': 'from-amber-300 via-orange-400 to-red-400',
                'published_date': '2025-09-03',
                'reading_time': 7
            },
            {
                'id': 3,
                'title': 'Tantra além do prazer: uma jornada de cura',
                'excerpt': 'Entenda como o Tantra vai muito além do aspecto sexual, oferecendo um caminho profundo de autoconhecimento, cura emocional e expansão da consciência.',
                'author': {
                    'name': 'Beatriz Silva',
                    'specialty': 'Tantra'
                },
                'featured_image': None,
                'color_class': 'from-purple-400 via-pink-400 to-red-400',
                'published_date': '2025-09-01',
                'reading_time': 8
            }
        ]
        
        # Estatísticas gerais (placeholder)
        context['stats'] = {
            'total_therapists': 247,
            'total_spaces': 89,
            'total_therapies': 15,
            'total_cities': 12
        }
        
        return context


def home_view(request):
    """
    View função simples para a home (alternativa à classe)
    Mantida para compatibilidade, mas recomenda-se usar HomeView
    """
    context = {
        'page_title': 'Espaço Vital - Conectando você ao cuidado terapêutico',
        'meta_description': 'Encontre terapeutas e espaços terapêuticos verificados'
    }
    return render(request, 'core/home.html', context)


def search_therapists_ajax(request):
    """
    View AJAX para busca de terapeutas em tempo real
    Para uso futuro com HTMX na busca do hero section
    """
    if request.method == 'GET':
        query = request.GET.get('q', '')
        
        if len(query) >= 3:  # Buscar apenas se tiver 3+ caracteres
            # Aqui seria a busca no model Terapeuta quando estiver criado
            # therapists = Terapeuta.objects.filter(
            #     Q(name__icontains=query) | 
            #     Q(specialties__name__icontains=query)
            # ).distinct()[:5]
            
            # Por enquanto, resultados fake para demonstração
            results = [
                {'id': 1, 'name': 'Ana Silva', 'specialty': 'Massoterapia'},
                {'id': 2, 'name': 'Carlos Mendes', 'specialty': 'Yoga'},
            ]
            
            return JsonResponse({
                'success': True,
                'results': results
            })
    
    return JsonResponse({'success': False, 'results': []})


def search_spaces_ajax(request):
    """
    View AJAX para busca de espaços em tempo real
    Para uso futuro com HTMX
    """
    if request.method == 'GET':
        query = request.GET.get('q', '')
        
        if len(query) >= 3:
            # Busca futura no model Espaco
            results = [
                {'id': 1, 'name': 'Centro de Bem-Estar', 'location': 'Centro / RJ'},
                {'id': 2, 'name': 'Espaço Harmonia', 'location': 'Tijuca / RJ'},
            ]
            
            return JsonResponse({
                'success': True,
                'results': results
            })
    
    return JsonResponse({'success': False, 'results': []})


class AboutView(TemplateView):
    """
    View para página Sobre (para implementação futura)
    """
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Sobre - Espaço Vital'
        context['meta_description'] = 'Conheça nossa missão de conectar pessoas ao cuidado terapêutico que transforma vidas'
        return context


class ContactView(TemplateView):
    """
    View para página de Contato (para implementação futura)
    """
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Contato - Espaço Vital'
        context['meta_description'] = 'Entre em contato conosco para dúvidas, sugestões ou parcerias'
        return context