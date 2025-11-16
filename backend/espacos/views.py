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
    
# ===============================================================
# VIEWS DO DASHBOARD PRIVADO DO ESPAÇO
# ===============================================================

from datetime import timedelta


class EspacoRequiredMixin(LoginRequiredMixin):
    """
    Título: Mixin de Verificação de Proprietário de Espaço
    Descrição: Garante que apenas proprietários de espaços acessem o dashboard
    Autor: Will
    Data: 16/11/2025
    
    Verificações:
    - Usuário está autenticado
    - Usuário possui pelo menos um espaço cadastrado
    - Redireciona para home caso não atenda os requisitos
    """
    login_url = '/accounts/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Intercepta a requisição antes de processar
        Verifica autenticação e propriedade de espaço
        """
        # Verificar se está autenticado
        if not request.user.is_authenticated:
            messages.warning(
                request,
                'Você precisa estar logado para acessar o painel do espaço.'
            )
            return self.handle_no_permission()
        
        # Verificar se tem pelo menos um espaço
        if not Espaco.objects.filter(responsavel=request.user).exists():
            messages.error(
                request,
                'Você precisa ter um espaço terapêutico cadastrado para acessar esta área. '
                'Entre em contato conosco para cadastrar seu espaço.'
            )
            return redirect('core:home')
        
        return super().dispatch(request, *args, **kwargs)


class DashboardEspacoView(EspacoRequiredMixin, TemplateView):
    """
    Título: Dashboard Principal do Espaço
    Descrição: Visão geral do espaço com estatísticas e ações rápidas
    Autor: Will
    Data: 16/11/2025
    """
    template_name = 'espacos/dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        Carrega todas as estatísticas e informações do espaço
        """
        context = super().get_context_data(**kwargs)
        
        # Pegar o espaço do usuário (primeiro se tiver vários)
        espaco = Espaco.objects.filter(
            responsavel=self.request.user
        ).select_related('cidade', 'estado').first()
        
        context['espaco'] = espaco
        
        # Verificar se tem espaço
        if not espaco:
            return context
        
        # ===== ESTATÍSTICAS PRINCIPAIS =====
        
        # Total de visualizações (verificar se campo existe)
        if hasattr(espaco, 'visualizacoes'):
            context['total_visualizacoes'] = espaco.visualizacoes
            context['visualizacoes_7_dias'] = int(espaco.visualizacoes * 0.15)
        else:
            context['total_visualizacoes'] = 0
            context['visualizacoes_7_dias'] = 0
        
        # Total de contatos recebidos
        context['total_contatos'] = espaco.contatos.count()
        
        # Contatos nos últimos 30 dias
        data_30_dias = timezone.now() - timedelta(days=30)
        context['contatos_30_dias'] = espaco.contatos.filter(
            created_at__gte=data_30_dias
        ).count()
        
        # ===== AVALIAÇÕES =====
        
        # Média de avaliações
        media_avaliacoes = espaco.avaliacoes.filter(
            is_active=True
        ).aggregate(Avg('nota'))['nota__avg']
        context['media_avaliacoes'] = round(media_avaliacoes, 1) if media_avaliacoes else 0
        
        # Total de avaliações
        context['total_avaliacoes'] = espaco.avaliacoes.filter(is_active=True).count()
        
        # ===== TERAPEUTAS VINCULADOS =====
        
        # Verificar se o model tem campo para terapeutas vinculados
        if hasattr(espaco, 'terapeutas_vinculados'):
            context['total_terapeutas'] = espaco.terapeutas_vinculados.count()
        else:
            context['total_terapeutas'] = 0
        
        # ===== PERCENTUAL DE COMPLETUDE DO PERFIL =====
        
        completude = 0
        total_campos = 6
        
        # Verificar cada campo importante (com hasattr para segurança)
        if espaco.nome:
            completude += 1
        if hasattr(espaco, 'descricao_completa') and espaco.descricao_completa:
            completude += 1
        if hasattr(espaco, 'descricao_breve') and espaco.descricao_breve:
            completude += 1
        if espaco.cidade:
            completude += 1
        if espaco.comodidades.exists():
            completude += 1
        if espaco.especialidades.exists():
            completude += 1
        
        context['percentual_completude'] = int((completude / total_campos) * 100)
        
        # ===== CONTATOS RECENTES =====
        
        context['contatos_recentes'] = espaco.contatos.select_related(
        ).order_by('-created_at')[:5]
        
        # ===== AVALIAÇÕES RECENTES =====
        
        context['avaliacoes_recentes'] = espaco.avaliacoes.filter(
            is_active=True
        ).order_by('-created_at')[:3]
        
        # ===== PLANO ATUAL =====
        
        # Determinar plano baseado nos campos do model
        if espaco.is_premium:
            context['plano_atual'] = 'Premium S'
            context['plano_badge_color'] = 'bg-gradient-to-r from-amber-500 to-orange-500'
        elif espaco.is_destaque:
            context['plano_atual'] = 'Premium A'
            context['plano_badge_color'] = 'bg-gradient-to-r from-blue-500 to-indigo-500'
        else:
            context['plano_atual'] = 'Basic'
            context['plano_badge_color'] = 'bg-gray-500'
        
        # ===== COMPARATIVO COM MÉDIA DA PLATAFORMA =====
        
        context['media_plataforma_visualizacoes'] = 0
        context['diferenca_visualizacoes'] = 0
        
        return context


class DashboardEditarEspacoView(EspacoRequiredMixin, TemplateView):
    """
    Título: Editar Perfil do Espaço
    Descrição: Formulário completo para edição de dados do espaço
    Autor: Will
    Data: 16/11/2025
    """
    template_name = 'espacos/dashboard/editar_espaco.html'
    
    def get_context_data(self, **kwargs):
        """
        Carrega todas as estatísticas e informações do espaço
        Versão simplificada e segura
        """
        context = super().get_context_data(**kwargs)
        
        # Pegar o espaço do usuário (primeiro se tiver vários)
        espaco = Espaco.objects.filter(
            responsavel=self.request.user
        ).first()
        
        context['espaco'] = espaco
        
        # Verificar se tem espaço
        if not espaco:
            context['total_visualizacoes'] = 0
            context['visualizacoes_7_dias'] = 0
            context['total_contatos'] = 0
            context['contatos_30_dias'] = 0
            context['media_avaliacoes'] = 0
            context['total_avaliacoes'] = 0
            context['total_terapeutas'] = 0
            context['percentual_completude'] = 0
            context['contatos_recentes'] = []
            context['avaliacoes_recentes'] = []
            context['plano_atual'] = 'Basic'
            context['plano_badge_color'] = 'bg-gray-500'
            context['media_plataforma_visualizacoes'] = 0
            context['diferenca_visualizacoes'] = 0
            return context
        
        # ===== ESTATÍSTICAS PRINCIPAIS (valores padrão) =====
        context['total_visualizacoes'] = 0
        context['visualizacoes_7_dias'] = 0
        context['total_contatos'] = espaco.contatos.count() if hasattr(espaco, 'contatos') else 0
        context['contatos_30_dias'] = 0
        context['media_avaliacoes'] = 0
        context['total_avaliacoes'] = 0
        context['total_terapeutas'] = 0
        
        # Contatos nos últimos 30 dias
        if hasattr(espaco, 'contatos'):
            data_30_dias = timezone.now() - timedelta(days=30)
            context['contatos_30_dias'] = espaco.contatos.filter(
                created_at__gte=data_30_dias
            ).count()
        
        # ===== AVALIAÇÕES =====
        if hasattr(espaco, 'avaliacoes'):
            media_avaliacoes = espaco.avaliacoes.filter(
                is_active=True
            ).aggregate(Avg('nota'))['nota__avg']
            context['media_avaliacoes'] = round(media_avaliacoes, 1) if media_avaliacoes else 0
            context['total_avaliacoes'] = espaco.avaliacoes.filter(is_active=True).count()
        
        # ===== PERCENTUAL DE COMPLETUDE DO PERFIL =====
        completude = 0
        if espaco.nome:
            completude += 1
        if hasattr(espaco, 'descricao_completa') and espaco.descricao_completa:
            completude += 1
        if hasattr(espaco, 'descricao_breve') and espaco.descricao_breve:
            completude += 1
        if espaco.cidade:
            completude += 1
        if hasattr(espaco, 'comodidades') and espaco.comodidades.exists():
            completude += 1
        if hasattr(espaco, 'especialidades') and espaco.especialidades.exists():
            completude += 1
        
        context['percentual_completude'] = int((completude / 6) * 100)
        
        # ===== CONTATOS RECENTES =====
        if hasattr(espaco, 'contatos'):
            context['contatos_recentes'] = espaco.contatos.order_by('-created_at')[:5]
        else:
            context['contatos_recentes'] = []
        
        # ===== AVALIAÇÕES RECENTES =====
        if hasattr(espaco, 'avaliacoes'):
            context['avaliacoes_recentes'] = espaco.avaliacoes.filter(
                is_active=True
            ).order_by('-created_at')[:3]
        else:
            context['avaliacoes_recentes'] = []
        
        # ===== PLANO ATUAL =====
        if hasattr(espaco, 'is_premium') and espaco.is_premium:
            context['plano_atual'] = 'Premium S'
            context['plano_badge_color'] = 'bg-gradient-to-r from-amber-500 to-orange-500'
        elif hasattr(espaco, 'is_destaque') and espaco.is_destaque:
            context['plano_atual'] = 'Premium A'
            context['plano_badge_color'] = 'bg-gradient-to-r from-blue-500 to-indigo-500'
        else:
            context['plano_atual'] = 'Basic'
            context['plano_badge_color'] = 'bg-gray-500'
        
        # ===== COMPARATIVO =====
        context['media_plataforma_visualizacoes'] = 0
        context['diferenca_visualizacoes'] = 0
        
        return context


class DashboardTerapeutasVinculadosView(EspacoRequiredMixin, TemplateView):
    """
    Título: Terapeutas Vinculados ao Espaço
    Descrição: Gerenciar terapeutas que utilizam o espaço
    Autor: Will
    Data: 16/11/2025
    """
    template_name = 'espacos/dashboard/terapeutas_vinculados.html'
    
    def get_context_data(self, **kwargs):
        """
        Lista terapeutas vinculados e solicitações pendentes
        """
        context = super().get_context_data(**kwargs)
        
        espaco = Espaco.objects.filter(
            responsavel=self.request.user
        ).first()
        
        context['espaco'] = espaco
        
        # Terapeutas vinculados (se o relacionamento existir)
        if hasattr(espaco, 'terapeutas_vinculados'):
            context['terapeutas_vinculados'] = espaco.terapeutas_vinculados.all()
        else:
            context['terapeutas_vinculados'] = []
        
        # Solicitações pendentes (estrutura para futuro)
        context['solicitacoes_pendentes'] = []
        
        # Estatísticas de uso
        context['total_vinculados'] = len(context['terapeutas_vinculados'])
        
        return context


class DashboardDisponibilidadeView(EspacoRequiredMixin, TemplateView):
    """
    Título: Disponibilidade do Espaço
    Descrição: Gerenciar calendário e horários disponíveis para locação
    Autor: Will
    Data: 16/11/2025
    """
    template_name = 'espacos/dashboard/disponibilidade.html'
    
    def get_context_data(self, **kwargs):
        """
        Carrega informações de disponibilidade e reservas
        """
        context = super().get_context_data(**kwargs)
        
        espaco = Espaco.objects.filter(
            responsavel=self.request.user
        ).first()
        
        context['espaco'] = espaco
        
        # Períodos de disponibilidade configurados
        context['periodos_disponiveis'] = []
        if espaco:
            # Verificar quais períodos estão marcados
            if hasattr(espaco, 'disponibilidade_manha') and espaco.disponibilidade_manha:
                context['periodos_disponiveis'].append('Manhã')
            if hasattr(espaco, 'disponibilidade_tarde') and espaco.disponibilidade_tarde:
                context['periodos_disponiveis'].append('Tarde')
            if hasattr(espaco, 'disponibilidade_noite') and espaco.disponibilidade_noite:
                context['periodos_disponiveis'].append('Noite')
            if hasattr(espaco, 'disponibilidade_fds') and espaco.disponibilidade_fds:
                context['periodos_disponiveis'].append('Finais de Semana')
        
        # Reservas futuras (estrutura para futuro)
        context['reservas_futuras'] = []
        
        # Horários disponíveis
        context['horarios_semana'] = [
            {'dia': 'Segunda-feira', 'horarios': '08:00 - 20:00'},
            {'dia': 'Terça-feira', 'horarios': '08:00 - 20:00'},
            {'dia': 'Quarta-feira', 'horarios': '08:00 - 20:00'},
            {'dia': 'Quinta-feira', 'horarios': '08:00 - 20:00'},
            {'dia': 'Sexta-feira', 'horarios': '08:00 - 20:00'},
            {'dia': 'Sábado', 'horarios': '09:00 - 14:00'},
            {'dia': 'Domingo', 'horarios': 'Fechado'},
        ]
        
        return context


class DashboardPagamentosEspacoView(EspacoRequiredMixin, TemplateView):
    """
    Título: Pagamentos Recebidos
    Descrição: Gerenciar pagamentos de terapeutas pelo uso do espaço
    Autor: Will
    Data: 16/11/2025
    """
    template_name = 'espacos/dashboard/pagamentos.html'
    
    def get_context_data(self, **kwargs):
        """
        Carrega histórico e resumo de pagamentos
        """
        context = super().get_context_data(**kwargs)
        
        espaco = Espaco.objects.filter(
            responsavel=self.request.user
        ).first()
        
        context['espaco'] = espaco
        
        # Valores simulados (estrutura para futuro sistema de pagamentos)
        context['receita_total'] = 0.00
        context['receita_mes_atual'] = 0.00
        context['pagamentos_pendentes'] = 0.00
        
        # Histórico de transações (futuro)
        context['transacoes'] = []
        
        # Estatísticas
        context['total_transacoes'] = 0
        context['media_por_transacao'] = 0.00
        
        return context


class DashboardAssinaturaEspacoView(EspacoRequiredMixin, TemplateView):
    """
    Título: Assinatura do Espaço
    Descrição: Gerenciar plano de assinatura do espaço
    Autor: Will
    Data: 16/11/2025
    """
    template_name = 'espacos/dashboard/assinatura.html'
    
    def get_context_data(self, **kwargs):
        """
        Carrega informações do plano atual e opções de upgrade
        """
        context = super().get_context_data(**kwargs)
        
        espaco = Espaco.objects.filter(
            responsavel=self.request.user
        ).first()
        
        context['espaco'] = espaco
        
        # Determinar plano atual
        if espaco.is_premium:
            context['plano_atual'] = 'Premium S'
            context['preco_atual'] = 99.90
            context['plano_badge_color'] = 'bg-gradient-to-r from-amber-500 to-orange-500'
        elif espaco.is_destaque:
            context['plano_atual'] = 'Premium A'
            context['preco_atual'] = 49.90
            context['plano_badge_color'] = 'bg-gradient-to-r from-blue-500 to-indigo-500'
        else:
            context['plano_atual'] = 'Basic'
            context['preco_atual'] = 9.99
            context['plano_badge_color'] = 'bg-gray-500'
        
        # Definição dos planos disponíveis
        context['planos'] = [
            {
                'nome': 'Basic',
                'preco': 9.99,
                'cor': 'gray',
                'icone': '🏠',
                'beneficios': [
                    'Perfil básico na plataforma',
                    'Até 3 fotos do espaço',
                    'Listagem na busca',
                    'Contato por formulário',
                ],
                'limitacoes': [
                    'Sem destaque na busca',
                    'Sem selo de verificado',
                    'Suporte básico',
                ]
            },
            {
                'nome': 'Premium A',
                'preco': 49.90,
                'cor': 'blue',
                'icone': '⭐',
                'beneficios': [
                    'Tudo do Basic',
                    'Até 7 fotos do espaço',
                    'Destaque na busca',
                    'Selo de espaço verificado',
                    'Link direto para WhatsApp',
                    'Suporte prioritário',
                ],
                'limitacoes': [
                    'Sem posição premium no topo',
                ]
            },
            {
                'nome': 'Premium S',
                'preco': 99.90,
                'cor': 'amber',
                'icone': '👑',
                'beneficios': [
                    'Tudo do Premium A',
                    'Posição premium no topo',
                    'Badge VIP exclusivo',
                    'Destaque na home',
                    'Estatísticas avançadas',
                    'Suporte VIP 24h',
                    'Relatórios mensais',
                ],
                'limitacoes': []
            }
        ]
        
        # Data de renovação (simulada)
        context['data_renovacao'] = timezone.now() + timedelta(days=30)
        
        return context