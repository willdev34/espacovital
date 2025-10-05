# ===============================================================
# Título: Views do App Core - Carrossel com Todos Destaques
# Descrição: Views que mostram todos terapeutas destaque com ordem rotativa
# Autor: Will | Empresa: Espaço Vital
# Data: 17/09/2025
# ===============================================================

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.cache import cache
import hashlib
import time
from datetime import datetime


class HomeView(TemplateView):
    """
    View da página inicial do Espaço Vital
    Carrossel com todos terapeutas em destaque, ordem rotativa a cada 5h
    """
    template_name = 'core/home.html'
    
    def get_carousel_seed(self):
        """
        Gera uma seed que muda a cada 5 horas e a cada reinício do servidor
        """
        # Horário atual em blocos de 5 horas
        now = datetime.now()
        hours_block = now.hour // 5  # 0, 1, 2, 3, 4 (blocos de 5h)
        date_hour_key = f"{now.date()}-{hours_block}"
        
        # Adicionar timestamp de início do servidor (muda a cada reinício)
        server_start_time = cache.get('server_start_time')
        if not server_start_time:
            server_start_time = time.time()
            cache.set('server_start_time', server_start_time, timeout=None)
        
        # Combinar data+hora+início_servidor para criar seed única
        seed_string = f"{date_hour_key}-{int(server_start_time)}"
        
        # Converter para número usando hash
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
    
    def get_context_data(self, **kwargs):
        """
        Contexto com TODOS os terapeutas em destaque, ordem rotativa
        """
        context = super().get_context_data(**kwargs)
        
        # Meta dados da página
        context['page_title'] = 'Espaço Vital - Conectando você ao cuidado terapêutico'
        context['meta_description'] = 'Encontre terapeutas e espaços terapêuticos verificados. Conectamos você ao cuidado que transforma sua vida.'
        
        # ===== BUSCAR TODOS OS TERAPEUTAS EM DESTAQUE =====
        try:
            from terapeutas.models import Terapeuta
            
            # Buscar TODOS os terapeutas em destaque (não limitar quantidade)
            terapeutas_destaque = Terapeuta.objects.filter(
                is_active=True,
                destaque=True  # APENAS os marcados como destaque
            ).select_related('cidade_principal', 'cidade_principal__estado').prefetch_related('especialidades')
            
            print(f"=== CARROSSEL DESTAQUE ===")
            print(f"Terapeutas em destaque encontrados: {terapeutas_destaque.count()}")
            
            # Se não há terapeutas em destaque, buscar premium
            if not terapeutas_destaque.exists():
                print("Nenhum destaque encontrado, buscando premium...")
                terapeutas_destaque = Terapeuta.objects.filter(
                    is_active=True,
                    premium=True
                ).select_related('cidade_principal', 'cidade_principal__estado').prefetch_related('especialidades')
                print(f"Terapeutas premium encontrados: {terapeutas_destaque.count()}")
            
            # Se ainda não há, buscar verificados
            if not terapeutas_destaque.exists():
                print("Nenhum premium encontrado, buscando verificados...")
                terapeutas_destaque = Terapeuta.objects.filter(
                    is_active=True,
                    verificado=True
                ).select_related('cidade_principal', 'cidade_principal__estado').prefetch_related('especialidades')
                print(f"Terapeutas verificados encontrados: {terapeutas_destaque.count()}")
            
            # Aplicar ordem aleatória baseada na seed rotativa
            seed = self.get_carousel_seed()
            print(f"Seed atual para ordem: {seed}")
            
            # Converter para lista e embaralhar de forma determinística
            terapeutas_list = list(terapeutas_destaque)
            
            # Embaralhar usando a seed (sempre a mesma ordem durante 5h)
            import random
            random.seed(seed)
            random.shuffle(terapeutas_list)
            
            # Converter para formato do template
            context['featured_therapists'] = []
            for terapeuta in terapeutas_list:
                # Buscar especialidades do terapeuta
                especialidades = list(terapeuta.especialidades.all()[:2])
                especialidades_str = ' • '.join([esp.nome for esp in especialidades]) if especialidades else 'Terapeuta Holístico'
                
                context['featured_therapists'].append({
                    'id': terapeuta.id,
                    'name': terapeuta.nome_exibicao or terapeuta.nome_completo,
                    'specialties': especialidades_str,
                    'location': terapeuta.get_cidade_principal_display(),
                    'verified': terapeuta.verificado,
                    'premium': terapeuta.premium,
                    'destaque': terapeuta.destaque,
                    'photo': terapeuta.foto_perfil.url if terapeuta.foto_perfil else None,
                    'rating': 4.8,
                    'total_reviews': 85,
                    'url': f'/terapeutas/perfil/{terapeuta.slug}/' if terapeuta.slug else '#'
                })
            
            print(f"Terapeutas no carrossel: {len(context['featured_therapists'])}")
            for i, t in enumerate(context['featured_therapists']):
                status = []
                if t['destaque']: status.append('DESTAQUE')
                if t['premium']: status.append('PREMIUM')
                if t['verified']: status.append('VERIFICADO')
                print(f"{i+1}. {t['name']} ({' | '.join(status)})")
            print("=== FIM DEBUG ===")
                
        except Exception as e:
            print(f"ERRO na busca de terapeutas: {str(e)}")
            context['featured_therapists'] = [
                {
                    'id': 1,
                    'name': 'ERRO - Verifique os terapeutas',
                    'specialties': f'Erro: {str(e)[:50]}',
                    'location': 'Debug Mode',
                    'verified': False,
                    'premium': False,
                    'destaque': False,
                    'photo': None,
                    'rating': 0,
                    'total_reviews': 0,
                    'url': '/admin/terapeutas/terapeuta/'
                }
            ]
        
        # ===== DADOS ESTÁTICOS (resto da página) =====
        
        # Dados de espaços (estático por enquanto)
        context['featured_spaces'] = [
            {
                'id': 1,
                'name': 'Centro de Bem-Estar',
                'location': 'Centro / RJ',
                'therapists_count': 3,
                'color_class': 'from-yellow-200 via-orange-300 to-amber-400',
                'available_therapies': ['Massoterapia', 'Reiki', 'Yoga'],
                'url': '#'
            },
            {
                'id': 2,
                'name': 'Espaço Harmonia',
                'location': 'Santa da Tijuca / RJ',
                'therapists_count': 5,
                'color_class': 'from-amber-400 via-orange-500 to-red-500',
                'available_therapies': ['Shiatsu', 'Aromaterapia', 'Cristaloterapia'],
                'url': '#'
            },
            {
                'id': 3,
                'name': 'Vila Zen',
                'location': 'Vila Madalena / SP',
                'therapists_count': 8,
                'color_class': 'from-red-400 via-red-600 to-red-800',
                'available_therapies': ['Tantra', 'Yoga', 'Meditação'],
                'url': '#'
            },
            {
                'id': 4,
                'name': 'Santuário Natural',
                'location': 'Santo Inácio / RJ',
                'therapists_count': 2,
                'color_class': 'from-gray-300 via-gray-500 to-gray-700',
                'available_therapies': ['Reflexologia', 'Massoterapia'],
                'url': '#'
            },
            {
                'id': 5,
                'name': 'Espaço Vital',
                'location': 'Vilinha / ES',
                'therapists_count': 4,
                'color_class': 'from-amber-300 via-yellow-400 to-orange-500',
                'available_therapies': ['Reiki', 'Cristaloterapia', 'Aromaterapia'],
                'url': '#'
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
                'featured_image': None,
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
        
        # ===== ESTATÍSTICAS DINÂMICAS =====
        try:
            from terapeutas.models import Terapeuta
            context['stats'] = {
                'total_therapists': Terapeuta.objects.filter(is_active=True).count(),
                'total_spaces': 89,
                'total_therapies': 15,
                'total_cities': 12
            }
        except:
            context['stats'] = {
                'total_therapists': 247,
                'total_spaces': 89,
                'total_therapies': 15,
                'total_cities': 12
            }
        
        return context
    
# ===============================================================
# APIs DE LOCALIZAÇÃO (AJAX)
# ===============================================================

from django.http import JsonResponse
from .models import Estado, Cidade

def api_estados(request):
    """
    API para buscar estados por país
    Uso: /api/estados/?pais=1
    """
    pais_id = request.GET.get('pais')
    
    if not pais_id:
        return JsonResponse({'error': 'País não informado'}, status=400)
    
    estados = Estado.objects.filter(
        pais_id=pais_id,
        ativo=True
    ).values('id', 'nome', 'sigla').order_by('nome')
    
    return JsonResponse(list(estados), safe=False)


def api_cidades(request):
    """
    API para buscar cidades por estado OU por país
    Uso: /api/cidades/?estado=1  OU  /api/cidades/?pais=1
    """
    estado_id = request.GET.get('estado')
    pais_id = request.GET.get('pais')
    
    if estado_id:
        # Buscar cidades por estado (Brasil e países com estados)
        cidades = Cidade.objects.filter(
            estado_id=estado_id,
            ativo=True
        ).values('id', 'nome').order_by('nome')
    elif pais_id:
        # Buscar cidades diretas do país (países sem estados)
        cidades = Cidade.objects.filter(
            pais_id=pais_id,
            estado__isnull=True,
            ativo=True
        ).values('id', 'nome').order_by('nome')
    else:
        return JsonResponse({'error': 'Estado ou País não informado'}, status=400)
    
    return JsonResponse(list(cidades), safe=False)