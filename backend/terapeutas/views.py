# ===============================================================
# Título: Views do App Terapeutas - Espaço Vital
# Descrição: Views para busca, listagem e perfil de terapeutas
# Autor: Will | Empresa: Espaço VItal
# Data: 13/09/2025
# ===============================================================

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from .models import (
    Terapeuta, Especialidade, Estado, Cidade, 
    Avaliacao, Contato, SessionType, ProfileType, ClientType
)
import json


# ===============================================================
# VIEWS DE BUSCA E LISTAGEM
# ===============================================================

class TerapeutaListView(ListView):
    """
    View principal para listagem de terapeutas com filtros
    Baseada no layout da busca avançada compartilhado
    """
    model = Terapeuta
    template_name = 'terapeutas/busca_avancada.html'
    context_object_name = 'terapeutas'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Aplica todos os filtros baseados nos parâmetros GET
        Exatamente como no layout da busca avançada
        """
        queryset = Terapeuta.objects.filter(is_active=True).select_related(
            'cidade', 'cidade__estado'
        ).prefetch_related(
            'especialidades', 'avaliacoes'
        ).annotate(
            media_avaliacoes=Avg('avaliacoes__nota'),
            total_avaliacoes=Count('avaliacoes', filter=Q(avaliacoes__is_active=True))
        )
        
        # ===== FILTROS DO LAYOUT =====
        
        # Filtro: Que tipo de sessão está buscando?
        tipos_sessao = self.request.GET.getlist('tipos_sessao')
        if tipos_sessao:
            # Filtra terapeutas que oferecem pelo menos um dos tipos selecionados
            for tipo in tipos_sessao:
                if tipo in [choice[0] for choice in SessionType.choices]:
                    queryset = queryset.filter(
                        tipos_sessao__contains=[tipo]
                    )
        
        # Filtro: Localização
        cidade_id = self.request.GET.get('cidade')
        if cidade_id:
            try:
                queryset = queryset.filter(cidade_id=cidade_id)
            except ValueError:
                pass
        
        estado_id = self.request.GET.get('estado')
        if estado_id:
            try:
                queryset = queryset.filter(cidade__estado_id=estado_id)
            except ValueError:
                pass
        
        # Filtro: Terapias/Especialidades
        especialidades = self.request.GET.getlist('especialidades')
        if especialidades:
            try:
                especialidades_ids = [int(esp_id) for esp_id in especialidades]
                queryset = queryset.filter(
                    especialidades__id__in=especialidades_ids
                ).distinct()
            except ValueError:
                pass
        
        # Filtro: Acessibilidade
        acessibilidade = self.request.GET.get('acessibilidade')
        if acessibilidade == 'sim':
            queryset = queryset.filter(acessibilidade=True)
        
        # Filtro: Perfil de profissional
        perfil_profissional = self.request.GET.get('perfil_profissional')
        if perfil_profissional:
            if perfil_profissional in [choice[0] for choice in ProfileType.choices]:
                queryset = queryset.filter(tipo_perfil=perfil_profissional)
        
        # Filtro: Para quem é a terapia
        para_quem = self.request.GET.get('para_quem')
        if para_quem:
            if para_quem in [choice[0] for choice in ClientType.choices]:
                queryset = queryset.filter(para_quem=para_quem)
        
        # Filtro: Busca por texto (nome, bio, especialidades)
        busca = self.request.GET.get('q')
        if busca:
            queryset = queryset.filter(
                Q(nome_completo__icontains=busca) |
                Q(nome_exibicao__icontains=busca) |
                Q(bio_curta__icontains=busca) |
                Q(bio_completa__icontains=busca) |
                Q(especialidades__nome__icontains=busca)
            ).distinct()
        
        # ===== ORDENAÇÃO =====
        # Ordem de prioridade: Destaque > Premium > Verificado > Melhor avaliado
        ordering = self.request.GET.get('ordenacao', 'relevancia')
        
        if ordering == 'melhor_avaliado':
            queryset = queryset.order_by('-media_avaliacoes', '-total_avaliacoes')
        elif ordering == 'mais_experiente':
            queryset = queryset.order_by('-experiencia_anos')
        elif ordering == 'nome':
            queryset = queryset.order_by('nome_exibicao')
        else:  # relevancia (padrão)
            queryset = queryset.order_by(
                '-destaque', '-premium', '-verificado', 
                '-media_avaliacoes', '-created_at'
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Adiciona dados para os filtros no template
        """
        context = super().get_context_data(**kwargs)
        
        # Dados para os filtros
        context['estados'] = Estado.objects.all().order_by('nome')
        context['cidades'] = Cidade.objects.all().order_by('nome')
        context['especialidades'] = Especialidade.objects.filter(
            is_active=True
        ).order_by('nome')
        
        # Choices para os selects
        context['tipos_sessao_choices'] = SessionType.choices
        context['perfil_profissional_choices'] = ProfileType.choices
        context['para_quem_choices'] = ClientType.choices
        
        # Valores atuais dos filtros (para manter selecionado)
        context['filtros_atuais'] = {
            'tipos_sessao': self.request.GET.getlist('tipos_sessao'),
            'cidade': self.request.GET.get('cidade', ''),
            'estado': self.request.GET.get('estado', ''),
            'especialidades': self.request.GET.getlist('especialidades'),
            'acessibilidade': self.request.GET.get('acessibilidade', ''),
            'perfil_profissional': self.request.GET.get('perfil_profissional', ''),
            'para_quem': self.request.GET.get('para_quem', ''),
            'q': self.request.GET.get('q', ''),
            'ordenacao': self.request.GET.get('ordenacao', 'relevancia'),
        }
        
        # Contar resultados
        context['total_resultados'] = self.get_queryset().count()
        
        # Informações da busca atual
        if context['filtros_atuais']['cidade']:
            try:
                cidade = Cidade.objects.get(id=context['filtros_atuais']['cidade'])
                context['localizacao_atual'] = f"{cidade.nome} - {cidade.estado.sigla}"
            except Cidade.DoesNotExist:
                pass
        
        # Meta dados da página
        context['page_title'] = 'Buscar Terapeuta - Espaço Vital'
        context['meta_description'] = 'Encontre terapeutas verificados usando nossa busca avançada. Filtre por localização, especialidade, tipo de sessão e muito mais.'
        
        return context


def terapeutas_sem_filtro(request, especialidade_slug=None):
    """
    View para listagem simples sem filtros (baseado no layout sem filtro)
    Usado quando vem de links diretos ou categorias
    """
    terapeutas = Terapeuta.objects.filter(is_active=True).select_related(
        'cidade', 'cidade__estado'
    ).prefetch_related(
        'especialidades', 'avaliacoes'
    ).annotate(
        media_avaliacoes=Avg('avaliacoes__nota'),
        total_avaliacoes=Count('avaliacoes', filter=Q(avaliacoes__is_active=True))
    )
    
    especialidade = None
    if especialidade_slug:
        especialidade = get_object_or_404(
            Especialidade, 
            slug=especialidade_slug, 
            is_active=True
        )
        terapeutas = terapeutas.filter(especialidades=especialidade)
    
    # Ordenação padrão: destaque > premium > verificado
    terapeutas = terapeutas.order_by(
        '-destaque', '-premium', '-verificado', '-created_at'
    )
    
    # Paginação
    paginator = Paginator(terapeutas, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Busca por região/cidade (para o filtro lateral)
    estados = Estado.objects.all().order_by('nome')
    especialidades = Especialidade.objects.filter(is_active=True).order_by('nome')
    
    context = {
        'terapeutas': page_obj,
        'especialidade_atual': especialidade,
        'estados': estados,
        'especialidades': especialidades,
        'total_resultados': terapeutas.count(),
        'page_title': f'Terapeutas{" - " + especialidade.nome if especialidade else ""} - Espaço Vital',
        'meta_description': f'Encontre os melhores terapeutas{" de " + especialidade.nome if especialidade else ""} verificados pela plataforma.',
    }
    
    return render(request, 'terapeutas/listagem_simples.html', context)


# ===============================================================
# VIEW DE PERFIL DO TERAPEUTA
# ===============================================================

class TerapeutaDetailView(DetailView):
    """
    View para exibir perfil completo do terapeuta
    """
    model = Terapeuta
    template_name = 'terapeutas/perfil.html'
    context_object_name = 'terapeuta'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Terapeuta.objects.filter(is_active=True).select_related(
            'cidade', 'cidade__estado', 'user'
        ).prefetch_related(
            'especialidades',
            'terapeutaespecialidade_set',
            'avaliacoes__cliente'
        )
    
    def get_object(self):
        obj = super().get_object()
        # Incrementar visualizações
        obj.incrementar_visualizacoes()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        terapeuta = self.object
        
        # Especialidades com detalhes
        context['especialidades_detalhadas'] = terapeuta.terapeutaespecialidade_set.filter(
            is_active=True
        ).order_by('-principal', 'especialidade__nome')
        
        # Avaliações recentes
        context['avaliacoes_recentes'] = terapeuta.avaliacoes.filter(
            is_active=True
        ).select_related('cliente').order_by('-created_at')[:5]
        
        # Estatísticas
        context['stats'] = {
            'total_avaliacoes': terapeuta.total_avaliacoes,
            'media_avaliacoes': terapeuta.rating_medio,
            'anos_experiencia': terapeuta.experiencia_anos,
            'visualizacoes': terapeuta.visualizacoes,
        }
        
        # Terapeutas relacionados (mesma cidade, especialidades similares)
        context['terapeutas_relacionados'] = Terapeuta.objects.filter(
            cidade=terapeuta.cidade,
            especialidades__in=terapeuta.especialidades.all(),
            is_active=True
        ).exclude(
            id=terapeuta.id
        ).annotate(
            media_avaliacoes=Avg('avaliacoes__nota')
        ).order_by('-verificado', '-media_avaliacoes')[:3]
        
        # Meta dados
        context['page_title'] = f'{terapeuta.nome_exibicao} - Terapeuta - Espaço Vital'
        context['meta_description'] = f'{terapeuta.bio_curta[:150]}...'
        
        return context


# ===============================================================
# VIEWS AJAX PARA FILTROS DINÂMICOS
# ===============================================================

def cidades_por_estado_ajax(request):
    """
    Retorna cidades de um estado via AJAX
    Para o filtro de localização
    """
    estado_id = request.GET.get('estado_id')
    
    if not estado_id:
        return JsonResponse({'cidades': []})
    
    try:
        cidades = Cidade.objects.filter(
            estado_id=estado_id
        ).order_by('nome').values('id', 'nome')
        
        return JsonResponse({
            'cidades': list(cidades)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def busca_terapeutas_ajax(request):
    """
    Busca terapeutas via AJAX para autocomplete
    Para o campo de busca do hero section
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'terapeutas': []})
    
    terapeutas = Terapeuta.objects.filter(
        Q(nome_exibicao__icontains=query) |
        Q(especialidades__nome__icontains=query),
        is_active=True,
        verificado=True
    ).select_related('cidade').prefetch_related(
        'especialidades'
    ).annotate(
        media_avaliacoes=Avg('avaliacoes__nota')
    ).order_by('-destaque', '-premium', '-media_avaliacoes')[:8]
    
    resultados = []
    for terapeuta in terapeutas:
        resultados.append({
            'id': terapeuta.id,
            'nome': terapeuta.nome_exibicao,
            'slug': terapeuta.slug,
            'cidade': f"{terapeuta.cidade.nome} - {terapeuta.cidade.estado.sigla}" if terapeuta.cidade else '',
            'especialidades': [esp.nome for esp in terapeuta.especialidades.filter(is_active=True)[:2]],
            'rating': float(terapeuta.media_avaliacoes) if terapeuta.media_avaliacoes else 0.0,
            'verificado': terapeuta.verificado,
            'premium': terapeuta.premium,
            'foto_url': terapeuta.foto_perfil.url if terapeuta.foto_perfil else None,
        })
    
    return JsonResponse({'terapeutas': resultados})


# ===============================================================
# VIEW PARA CONTATO COM TERAPEUTA
# ===============================================================

def contatar_terapeuta(request, terapeuta_slug):
    """
    View para enviar mensagem para um terapeuta
    """
    terapeuta = get_object_or_404(Terapeuta, slug=terapeuta_slug, is_active=True)
    
    if request.method == 'POST':
        try:
            # Validar dados básicos
            nome = request.POST.get('nome', '').strip()
            email = request.POST.get('email', '').strip()
            assunto = request.POST.get('assunto', '').strip()
            mensagem = request.POST.get('mensagem', '').strip()
            telefone = request.POST.get('telefone', '').strip()
            
            if not all([nome, email, assunto, mensagem]):
                messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
                return render(request, 'terapeutas/contato_form.html', {
                    'terapeuta': terapeuta
                })
            
            # Obter especialidade de interesse (opcional)
            especialidade_id = request.POST.get('especialidade_interesse')
            especialidade_interesse = None
            if especialidade_id:
                try:
                    especialidade_interesse = Especialidade.objects.get(
                        id=especialidade_id, is_active=True
                    )
                except Especialidade.DoesNotExist:
                    pass
            
            # Criar contato
            contato = Contato.objects.create(
                terapeuta=terapeuta,
                nome=nome,
                email=email,
                telefone=telefone,
                assunto=assunto,
                mensagem=mensagem,
                especialidade_interesse=especialidade_interesse,
                ip_origem=request.META.get('REMOTE_ADDR'),
            )
            
            # Incrementar contador do terapeuta
            terapeuta.total_contatos += 1
            terapeuta.save(update_fields=['total_contatos'])
            
            # TODO: Enviar email de notificação para o terapeuta
            
            messages.success(
                request, 
                f'Sua mensagem foi enviada com sucesso para {terapeuta.nome_exibicao}! '
                'Eles entrarão em contato em breve.'
            )
            
            # Retornar JSON se for requisição AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Mensagem enviada com sucesso!'
                })
            
            return render(request, 'terapeutas/contato_sucesso.html', {
                'terapeuta': terapeuta,
                'contato': contato
            })
            
        except Exception as e:
            messages.error(request, 'Ocorreu um erro ao enviar sua mensagem. Tente novamente.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Erro ao enviar mensagem.'
                })
    
    # GET - Exibir formulário
    context = {
        'terapeuta': terapeuta,
        'especialidades': terapeuta.especialidades.filter(is_active=True),
        'page_title': f'Contatar {terapeuta.nome_exibicao} - Espaço Vital',
    }
    
    return render(request, 'terapeutas/contato_form.html', context)