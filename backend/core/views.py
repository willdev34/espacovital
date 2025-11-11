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

# Temporário
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
import io

from django.views.generic import CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Contact, SugestaoTerapia


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
    
    def get_location_display(self, terapeuta):
        """
        Retorna localização formatada do terapeuta
        Funciona para Brasil (cidade + estado) e Internacional (cidade_texto + país)
        """
        # Brasil - cidade do banco com estado
        if terapeuta.cidade_principal:
            if hasattr(terapeuta.cidade_principal, 'estado') and terapeuta.cidade_principal.estado:
                return f"{terapeuta.cidade_principal.nome} - {terapeuta.cidade_principal.estado.sigla}"
            else:
                return terapeuta.cidade_principal.nome
        
        # Outros países - cidade texto com país
        if terapeuta.cidade_texto:
            if terapeuta.pais:
                return f"{terapeuta.cidade_texto}/{terapeuta.pais.codigo}"
            return terapeuta.cidade_texto
        
        # Se tem estado mas não tem cidade
        if terapeuta.estado:
            return terapeuta.estado.sigla if hasattr(terapeuta.estado, 'sigla') else terapeuta.estado.nome
        
        # Última opção: retornar vazio (o template pode mostrar mensagem padrão se quiser)
        return ""

    def get_context_data(self, **kwargs):
        """
        Contexto com TODOS os terapeutas em destaque, ordem rotativa
        """
        context = super().get_context_data(**kwargs)
        
        # Importar models necessários
        from terapeutas.models import Terapeuta, Especialidade
        from espacos.models import Espaco
        from core.models import Pais, Estado, Cidade
        
        # Terapeutas em destaque com ordem rotativa
        seed = self.get_carousel_seed()
        terapeutas_qs = Terapeuta.objects.filter(
            is_active=True,
            destaque=True,
            verificado=True
        ).select_related(
            'cidade_principal', 
            'cidade_principal__estado',
            'pais'
        ).prefetch_related('especialidades')

        # Converter para lista e embaralhar
        terapeutas_list = list(terapeutas_qs)
        import random
        random.seed(seed)
        random.shuffle(terapeutas_list)

        # Converter para formato do template (igual ao que o template espera)
        context['featured_therapists'] = []
        for terapeuta in terapeutas_list:
            # DEBUG - APAGAR DEPOIS
            print(f"\n=== TERAPEUTA: {terapeuta.nome_completo} ===")
            print(f"cidade_principal: {terapeuta.cidade_principal}")
            print(f"cidade_texto: {terapeuta.cidade_texto}")
            print(f"pais: {terapeuta.pais}")
            if terapeuta.cidade_principal:
                print(f"cidade_principal.nome: {terapeuta.cidade_principal.nome}")
                print(f"cidade_principal.estado: {terapeuta.cidade_principal.estado}")
            print(f"Location gerado: {self.get_location_display(terapeuta)}")
            print("=" * 50)
            # Buscar especialidades
            especialidades = list(terapeuta.especialidades.all()[:2])
            especialidades_str = ' • '.join([esp.nome for esp in especialidades]) if especialidades else 'Terapeuta Holístico'
            
            # Montar objeto no formato esperado pelo template
            context['featured_therapists'].append({
                'id': terapeuta.id,
                'name': terapeuta.nome_exibicao or terapeuta.nome_completo,
                'specialties': especialidades_str,
                'location': self.get_location_display(terapeuta),
                'verified': terapeuta.verificado,
                'premium': terapeuta.premium,
                'destaque': terapeuta.destaque,
                'photo': terapeuta.foto_perfil.url if terapeuta.foto_perfil else None,
                'rating': 4.8,
                'total_reviews': 85,
                'url': f'/terapeutas/perfil/{terapeuta.slug}/' if terapeuta.slug else '#'
            })
        
        # Espaços em destaque
        context['espacos_destaque'] = Espaco.objects.filter(
            is_active=True,
            is_destaque=True
        ).select_related('cidade')[:6]
        
        # ============================================
        # DADOS PARA O MODAL DE BUSCA
        # ============================================
        
        # TODAS as especialidades/terapias (29 cadastradas)
        context['especialidades_modal'] = Especialidade.objects.filter(
            is_active=True
        ).order_by('nome')

        # Todos os países cadastrados
        context['paises_modal'] = Pais.objects.filter(
            ativo=True
        ).order_by('nome')

        # Todos os estados cadastrados
        context['estados_modal'] = Estado.objects.filter(
            ativo=True
        ).order_by('nome')

        # Todas as cidades cadastradas (para popular dinamicamente)
        context['cidades_modal'] = Cidade.objects.filter(
            ativo=True
        ).select_related('estado').order_by('nome')
        
        # Meta dados da página
        context['page_title'] = 'Espaço Vital - Conectando você ao cuidado terapêutico'
        context['meta_description'] = 'Encontre terapeutas e espaços terapêuticos verificados. Conectamos você ao cuidado que transforma sua vida.'
        
        return context
        
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

@staff_member_required
@require_http_methods(["GET"])
def fix_sequences_view(request):
    """View temporária para corrigir sequences do PostgreSQL"""
    try:
        # Captura a saída do comando
        output = io.StringIO()
        call_command('fix_sequences', stdout=output)
        result = output.getvalue()
        
        return HttpResponse(
            f"<pre>{result}</pre>",
            content_type="text/html"
        )
    except Exception as e:
        return HttpResponse(
            f"<h2>❌ Erro ao corrigir sequences:</h2><pre>{str(e)}</pre>",
            content_type="text/html"
        )
    
# ===============================================================
# PÁGINAS INSTITUCIONAIS
# ===============================================================

class SobreView(TemplateView):
    """
    Página Sobre o Projeto
    Descreve a missão, visão e valores do Espaço Vital
    Autor: Will
    Data: 08/11/2025
    """
    template_name = 'core/sobre.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Sobre o Espaço Vital - Nossa História e Missão'
        return context


class TermosView(TemplateView):
    """
    Página Termos de Uso
    Apresenta os termos e condições de uso da plataforma
    Autor: Will
    Data: 08/11/2025
    """
    template_name = 'core/termos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Termos de Uso - Espaço Vital'
        return context


class PrivacidadeView(TemplateView):
    """
    Página Política de Privacidade
    Apresenta como os dados dos usuários são coletados e utilizados
    Autor: Will
    Data: 08/11/2025
    """
    template_name = 'core/privacidade.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Política de Privacidade - Espaço Vital'
        return context


class CookiesView(TemplateView):
    """
    Página Política de Cookies
    Explica o uso de cookies e tecnologias similares
    Autor: Will
    Data: 08/11/2025
    """
    template_name = 'core/cookies.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Política de Cookies - Espaço Vital'
        return context


class ParceiroView(TemplateView):
    """
    Página Seja um Parceiro
    Informações para terapeutas e espaços se cadastrarem
    Autor: Will
    Data: 08/11/2025
    """
    template_name = 'core/parceiro.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Seja um Parceiro - Espaço Vital'
        return context


class FaqView(TemplateView):
    """
    Página de Perguntas Frequentes (FAQ)
    Responde dúvidas comuns dos usuários
    Autor: Will
    Data: 08/11/2025
    """
    template_name = 'core/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Perguntas Frequentes (FAQ) - Espaço Vital'
        return context


class ContatoView(CreateView):
    """
    Página de Contato com Formulário
    Permite usuários enviarem mensagens para o Espaço Vital
    Autor: Will
    Data: 08/11/2025
    """
    model = Contact
    template_name = 'core/contato.html'
    fields = ['name', 'email', 'phone', 'subject', 'message']
    success_url = reverse_lazy('core:contato')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Fale Conosco - Espaço Vital'
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Mensagem enviada com sucesso! Entraremos em contato em breve.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Erro ao enviar mensagem. Verifique os campos e tente novamente.'
        )
        return super().form_invalid(form)
    
class IndiqueTerapiaView(CreateView):
    """
    Formulário para usuários indicarem terapias
    Permite sugestões de novas terapias para o catálogo
    Autor: Will
    Data: 08/11/2025
    """
    model = SugestaoTerapia
    template_name = 'core/indique_terapia.html'
    fields = ['nome', 'email', 'nome_terapia', 'descricao']
    success_url = reverse_lazy('core:indique_terapia')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Indique uma Terapia - Espaço Vital'
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Obrigado pela sugestão! Avaliaremos e entraremos em contato.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Erro ao enviar sugestão. Verifique os campos e tente novamente.'
        )
        return super().form_invalid(form)