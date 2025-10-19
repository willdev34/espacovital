# ===============================================================
# Título: Views do App Espacos - Espaço Vital
# Descrição: Views para busca, listagem e perfil de espaços terapêuticos
# Autor: Will | Empresa: Espaço Vital
# Data: 14/09/2025
# ===============================================================

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.db.models import Q, Avg, Count, Prefetch
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    Espaco, Comodidade, AvaliacaoEspaco, ContatoEspaco, TipoEspaco, DisponibilidadePeriodo
)
from core.models import Estado, Cidade, Especialidade
from .forms import ContatoEspacoForm, AvaliacaoEspacoForm
import json


# ===============================================================
# VIEWS DE BUSCA E LISTAGEM
# ===============================================================

class EspacoListView(ListView):
    """
    View principal para busca avançada de espaços
    Baseada no layout espacoComFiltro.pdf
    """
    model = Espaco
    template_name = 'espacos/busca_avancada.html'
    context_object_name = 'espacos'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Aplica todos os filtros baseados nos parâmetros GET
        Exatamente como no layout espacoComFiltro.pdf
        """
        queryset = Espaco.objects.filter(is_active=True).select_related(
            'cidade', 'cidade__estado', 'estado', 'pais'
        ).prefetch_related('comodidades', 'especialidades'
        ).annotate(
            avg_avaliacoes=Avg('avaliacoes__nota'),
            count_avaliacoes=Count('avaliacoes', filter=Q(avaliacoes__is_active=True))
        )
        
        # ===== FILTROS DO LAYOUT =====
        
        # Filtro: Que tipo de espaço está buscando?
        tipo_espaco = self.request.GET.get('tipo_espaco')
        if tipo_espaco and tipo_espaco != 'todos':
            queryset = queryset.filter(tipo_espaco=tipo_espaco)
        
        # Filtro: Localização (País, Estado e Cidade)
        # Filtro por País
        pais_id = self.request.GET.get('pais')
        if pais_id:
            try:
                # Filtra pelo campo 'pais' direto do espaço
                queryset = queryset.filter(pais_id=pais_id)
            except ValueError:
                pass

        # Filtro por Estado
        estado = self.request.GET.get('estado')
        if estado and estado != '':
            queryset = queryset.filter(cidade__estado_id=estado)

        # Filtro por Cidade
        cidade = self.request.GET.get('cidade')
        if cidade and cidade != '':
            queryset = queryset.filter(cidade_id=cidade)
        
        # Filtro: Terapias disponíveis (multi-select)
        terapias = self.request.GET.getlist('terapias')
        if terapias and 'todas' not in terapias:
            queryset = queryset.filter(especialidades__id__in=terapias).distinct()
        
        # Filtro: Espaço com acessibilidade? (Sim/Não)
        acessibilidade = self.request.GET.get('acessibilidade')
        if acessibilidade == 'sim':
            queryset = queryset.filter(tem_acessibilidade=True)
        elif acessibilidade == 'nao':
            queryset = queryset.filter(tem_acessibilidade=False)
        
        # Filtro: Aceita locação? (Sim/Não)  
        locacao = self.request.GET.get('locacao')
        if locacao == 'sim':
            queryset = queryset.filter(aceita_locacao=True)
        elif locacao == 'nao':
            queryset = queryset.filter(aceita_locacao=False)
        
        # Filtro: Disponibilidade por período
        disponibilidade = self.request.GET.getlist('disponibilidade')
        if disponibilidade:
            # Filtra espaços que têm pelo menos um dos períodos selecionados
            q_objects = Q()
            for periodo in disponibilidade:
                q_objects |= Q(disponibilidade__contains=periodo)
            queryset = queryset.filter(q_objects)
        
        # Filtro: Comodidades desejadas (checkboxes múltiplos)
        comodidades = self.request.GET.getlist('comodidades')
        if comodidades:
            # Filtra espaços que têm TODAS as comodidades selecionadas
            for comodidade_id in comodidades:
                queryset = queryset.filter(comodidades__id=comodidade_id)
        
        # Filtro: Busca por texto (nome, descrição, localização)
        busca = self.request.GET.get('busca', '').strip()
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(descricao_breve__icontains=busca) |
                Q(bairro__icontains=busca) |
                Q(cidade__nome__icontains=busca) |
                Q(especialidades__nome__icontains=busca)
            ).distinct()
        
        # Ordenação
        ordem = self.request.GET.get('ordem', 'destaque')
        if ordem == 'nome':
            queryset = queryset.order_by('nome')
        elif ordem == 'avaliacao':
            queryset = queryset.order_by('-media_avaliacoes', '-total_avaliacoes')
        elif ordem == 'recente':
            queryset = queryset.order_by('-created_at')
        else:  # destaque (padrão)
            queryset = queryset.order_by('-is_destaque', '-is_premium', '-is_verificado', 'nome')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Adiciona dados para os filtros no template
        """
        context = super().get_context_data(**kwargs)
        
        # Importar Pais
        from core.models import Pais
        
        # Dados para dropdowns e filtros
        context['paises'] = Pais.objects.filter(ativo=True).order_by('nome')
        context['estados'] = Estado.objects.filter(ativo=True).order_by('nome')
        context['tipos_espaco'] = TipoEspaco.choices
        context['periodos_disponibilidade'] = DisponibilidadePeriodo.choices
        context['todas_especialidades'] = Especialidade.objects.filter(is_active=True).order_by('nome')  # Todas as 29
        context['todas_comodidades'] = Comodidade.objects.filter(is_active=True).order_by('-is_destaque', 'nome')
        
        # Manter valores dos filtros aplicados
        context['filtros_aplicados'] = {
            'tipo_espaco': self.request.GET.get('tipo_espaco', ''),
            'pais': self.request.GET.get('pais', ''),
            'estado': self.request.GET.get('estado', ''),
            'cidade': self.request.GET.get('cidade', ''),
            'terapias': self.request.GET.getlist('terapias'),
            'acessibilidade': self.request.GET.get('acessibilidade', ''),
            'locacao': self.request.GET.get('locacao', ''),
            'disponibilidade': self.request.GET.getlist('disponibilidade'),
            'comodidades': self.request.GET.getlist('comodidades'),
            'busca': self.request.GET.get('busca', ''),
            'ordem': self.request.GET.get('ordem', 'destaque'),
        }
        
        # Estatísticas dos resultados
        context['total_espacos'] = self.get_queryset().count()
        context['espacos_verificados'] = self.get_queryset().filter(is_verificado=True).count()
        
        return context


class EspacoListagemSimplesView(ListView):
    """
    View para listagem simples de espaços (sem filtros avançados)
    Baseada no layout espacoSemFiltro.pdf
    """
    model = Espaco
    template_name = 'espacos/listagem_simples.html'
    context_object_name = 'espacos'
    paginate_by = 18
    
    def get_queryset(self):
        """
        Queryset básico com ordenação por destaque
        """
        return Espaco.objects.filter(is_active=True).select_related(
            'cidade', 'cidade__estado'
        ).prefetch_related(
            'especialidades', 'avaliacoes'
        ).annotate(
            avg_avaliacoes=Avg('avaliacoes__nota'),
            count_avaliacoes=Count('avaliacoes', filter=Q(avaliacoes__is_active=True))
        ).order_by('-is_destaque', '-is_premium', '-is_verificado', 'nome')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agrupar espaços por região para tabs
        context['espacos_por_regiao'] = {}
        regioes = ['Rio de Janeiro', 'São Paulo', 'Belo Horizonte', 'Outras']
        
        for regiao in regioes:
            if regiao == 'Outras':
                espacos = self.get_queryset().exclude(
                    cidade__nome__in=['Rio de Janeiro', 'São Paulo', 'Belo Horizonte']
                )[:6]
            else:
                espacos = self.get_queryset().filter(cidade__nome=regiao)[:6]
            context['espacos_por_regiao'][regiao] = espacos
        
        return context


class EspacoPorRegiaoView(ListView):
    """
    View para listagem de espaços por região específica
    """
    model = Espaco
    template_name = 'espacos/por_regiao.html'
    context_object_name = 'espacos'
    paginate_by = 15
    
    def get_queryset(self):
        cidade_slug = self.kwargs.get('cidade_slug')
        self.cidade = get_object_or_404(Cidade, slug=cidade_slug)
        
        return Espaco.objects.filter(
            is_active=True, cidade=self.cidade
        ).select_related(
            'cidade', 'cidade__estado'
        ).prefetch_related(
            'especialidades', 'avaliacoes'
        ).annotate(
            avg_avaliacoes=Avg('avaliacoes__nota'),
            count_avaliacoes=Count('avaliacoes', filter=Q(avaliacoes__is_active=True))
        ).order_by('-is_destaque', '-is_premium', 'nome')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cidade'] = self.cidade
        context['total_espacos'] = self.get_queryset().count()
        return context


# ===============================================================
# VIEWS DE DETALHES E PERFIL
# ===============================================================

class EspacoDetailView(DetailView):
    """
    View para exibir perfil completo do espaço
    """
    model = Espaco
    template_name = 'espacos/perfil_espaco.html'
    context_object_name = 'espaco'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Espaco.objects.filter(is_active=True).select_related(
            'cidade', 'cidade__estado', 'responsavel'
        ).prefetch_related(
            'comodidades', 'especialidades',
            Prefetch('avaliacoes', queryset=AvaliacaoEspaco.objects.filter(
                is_active=True
            ).select_related('usuario').order_by('-created_at'))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        espaco = self.object
        
        # Estatísticas do espaço
        context['media_avaliacoes'] = espaco.media_avaliacoes
        context['total_avaliacoes'] = espaco.total_avaliacoes
        
        # Avaliações recentes (5 últimas)
        context['avaliacoes_recentes'] = espaco.avaliacoes.filter(
            is_active=True
        ).order_by('-created_at')[:5]
        
        # Distribuição de notas
        context['distribuicao_notas'] = {}
        for nota in range(1, 6):
            count = espaco.avaliacoes.filter(is_active=True, nota=nota).count()
            context['distribuicao_notas'][nota] = count
        
        # Comodidades em destaque
        context['comodidades_destaque'] = espaco.comodidades_destaque
        context['outras_comodidades'] = espaco.comodidades.exclude(
            id__in=espaco.comodidades_destaque.values_list('id', flat=True)
        )
        
        # Especialidades com detalhes
        context['especialidades_detalhadas'] = espaco.especialidades_detalhadas.select_related(
            'especialidade'
        ).order_by('-is_destaque', 'especialidade__nome')
        
        # Espaços relacionados (mesma cidade)
        context['espacos_relacionados'] = Espaco.objects.filter(
            is_active=True, cidade=espaco.cidade
        ).exclude(id=espaco.id).order_by('-is_destaque')[:4]
        
        return context


class EspacoGaleriaView(DetailView):
    """
    View para galeria de fotos do espaço
    """
    model = Espaco
    template_name = 'espacos/galeria.html'
    context_object_name = 'espaco'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


# ===============================================================
# VIEWS DE CONTATO E INTERAÇÃO
# ===============================================================

class ContatoEspacoView(CreateView):
    """
    View para formulário de contato com o espaço
    """
    model = ContatoEspaco
    form_class = ContatoEspacoForm
    template_name = 'espacos/contato.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.espaco = get_object_or_404(Espaco, slug=self.kwargs['slug'], is_active=True)
        context['espaco'] = self.espaco
        return context
    
    def form_valid(self, form):
        self.espaco = get_object_or_404(Espaco, slug=self.kwargs['slug'], is_active=True)
        form.instance.espaco = self.espaco
        messages.success(
            self.request,
            f'Mensagem enviada com sucesso para {self.espaco.nome}! '
            'Entrarão em contato em breve.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('espacos:detalhe', kwargs={'slug': self.espaco.slug})


class AvaliarEspacoView(LoginRequiredMixin, CreateView):
    """
    View para avaliar um espaço (somente usuários logados)
    """
    model = AvaliacaoEspaco
    form_class = AvaliacaoEspacoForm
    template_name = 'espacos/avaliar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.espaco = get_object_or_404(Espaco, slug=self.kwargs['slug'], is_active=True)
        context['espaco'] = self.espaco
        
        # Verificar se usuário já avaliou
        avaliacao_existente = AvaliacaoEspaco.objects.filter(
            espaco=self.espaco, usuario=self.request.user
        ).first()
        context['avaliacao_existente'] = avaliacao_existente
        
        return context
    
    def form_valid(self, form):
        self.espaco = get_object_or_404(Espaco, slug=self.kwargs['slug'], is_active=True)
        
        # Verificar se já avaliou
        if AvaliacaoEspaco.objects.filter(espaco=self.espaco, usuario=self.request.user).exists():
            messages.error(self.request, 'Você já avaliou este espaço.')
            return redirect('espacos:detalhe', slug=self.espaco.slug)
        
        form.instance.espaco = self.espaco
        form.instance.usuario = self.request.user
        
        messages.success(self.request, 'Avaliação enviada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('espacos:detalhe', kwargs={'slug': self.espaco.slug})


# ===============================================================
# VIEWS DE APIS AJAX
# ===============================================================

class CidadesPorEstadoAPIView(TemplateView):
    """
    API para carregar cidades por estado (filtro cascata)
    """
    def get(self, request, *args, **kwargs):
        estado_id = kwargs.get('estado_id')
        cidades = Cidade.objects.filter(estado_id=estado_id).order_by('nome')
        
        data = {
            'cidades': [
                {'id': cidade.id, 'nome': cidade.nome}
                for cidade in cidades
            ]
        }
        return JsonResponse(data)


class ComodidadesAPIView(TemplateView):
    """
    API para listar todas as comodidades
    """
    def get(self, request, *args, **kwargs):
        comodidades = Comodidade.objects.filter(is_active=True).order_by('-is_destaque', 'nome')
        
        data = {
            'comodidades': [
                {
                    'id': com.id,
                    'nome': com.nome,
                    'icone': com.icone,
                    'is_destaque': com.is_destaque
                }
                for com in comodidades
            ]
        }
        return JsonResponse(data)


class EspecialidadesAPIView(TemplateView):
    """
    API para listar especialidades por categoria
    """
    def get(self, request, *args, **kwargs):
        especialidades = Especialidade.objects.filter(is_active=True).order_by('categoria', 'nome')
        
        # Agrupar por categoria
        por_categoria = {}
        for esp in especialidades:
            categoria = esp.categoria or 'Outras'
            if categoria not in por_categoria:
                por_categoria[categoria] = []
            por_categoria[categoria].append({
                'id': esp.id,
                'nome': esp.nome
            })
        
        return JsonResponse({'especialidades': por_categoria})


class EspacoBuscaHTMXView(ListView):
    """
    View HTMX para busca de espaços sem reload da página
    """
    model = Espaco
    template_name = 'espacos/partials/lista_espacos.html'
    context_object_name = 'espacos'
    paginate_by = 12
    
    def get_queryset(self):
        # Reutilizar a mesma lógica de filtros da EspacoListView
        view = EspacoListView()
        view.request = self.request
        return view.get_queryset()


# ===============================================================
# VIEWS AUXILIARES
# ===============================================================

class EspacoHomeView(TemplateView):
    """
    View para página inicial de espaços (redirecionamento)
    """
    template_name = 'espacos/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Espaços em destaque
        context['espacos_destaque'] = Espaco.objects.filter(
            is_active=True, is_destaque=True
        ).order_by('-is_premium')[:6]
        
        # Estatísticas gerais
        context['total_espacos'] = Espaco.objects.filter(is_active=True).count()
        context['total_cidades'] = Cidade.objects.filter(espacos__is_active=True).distinct().count()
        context['total_comodidades'] = Comodidade.objects.filter(is_active=True).count()
        
        return context


class EspacoEstatisticasView(LoginRequiredMixin, DetailView):
    """
    View para estatísticas do espaço (apenas para proprietários)
    """
    model = Espaco
    template_name = 'espacos/estatisticas.html'
    context_object_name = 'espaco'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        # Apenas espaços do usuário logado
        return Espaco.objects.filter(responsavel=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        espaco = self.object
        
        # Estatísticas de contatos
        context['total_contatos'] = espaco.contatos.count()
        context['contatos_mes'] = espaco.contatos.filter(
            created_at__month=timezone.now().month
        ).count()
        
        # Estatísticas de avaliações
        context['media_avaliacoes'] = espaco.media_avaliacoes
        context['total_avaliacoes'] = espaco.total_avaliacoes
        
        return context