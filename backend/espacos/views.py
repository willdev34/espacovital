# ===============================================================
# Título: Views do App Espacos - Espaço Vital
# Descrição: Views para busca, listagem e perfil de espaços terapêuticos
# ===============================================================

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, View
from django.db.models import Q, Avg, Count, Prefetch
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    Espaco, Comodidade, AvaliacaoEspaco, ContatoEspaco, TipoEspaco, DisponibilidadePeriodo
)
from core.models import Estado, Cidade, Especialidade, Assinatura
from .forms import ContatoEspacoForm, AvaliacaoEspacoForm
from django.forms import inlineformset_factory
from agendamentos.models import Sala
from core.models import Assinatura
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
    Descrição: Formulário completo para edição de dados do espaço + galeria
    Autor: Will
    Data: 26/12/2025
    """
    template_name = 'espacos/dashboard/editar_espaco.html'
    
    def get_context_data(self, **kwargs):
        """
        Carrega o formulário unificado e formset de galeria
        """
        from .forms import EspacoForm
        from .models import FotoGaleriaEspaco
        
        context = super().get_context_data(**kwargs)
        
        # Pegar o espaço do usuário
        espaco = Espaco.objects.filter(
            responsavel=self.request.user
        ).select_related('cidade', 'estado', 'pais').first()
        
        # Criar formset para galeria (até 7 fotos) - CAMPOS OPCIONAIS
        FotoGaleriaFormSet = inlineformset_factory(
            Espaco,
            FotoGaleriaEspaco,
            fields=('imagem', 'descricao', 'ordem'),
            extra=0,  # ✅ Mudou de 1 para 0 (não criar formulários vazios)
            max_num=7,
            can_delete=True,
            can_order=False
        )
        
        # Criar formulário principal e formset
        context['form'] = EspacoForm(instance=espaco)
        context['galeria_formset'] = FotoGaleriaFormSet(instance=espaco)
        context['espaco'] = espaco
        
        # Carregar dados auxiliares
        context['especialidades'] = Especialidade.objects.filter(is_active=True)
        context['estados'] = Estado.objects.filter(pais__nome='Brasil', ativo=True)
        context['comodidades'] = Comodidade.objects.filter(is_active=True)
        
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Processa o formulário de edição + galeria
        """
        from .forms import EspacoForm
        from .models import FotoGaleriaEspaco
        
        espaco = Espaco.objects.filter(
            responsavel=request.user
        ).first()
        
        if not espaco:
            messages.error(request, '❌ Espaço não encontrado.')
            return redirect('core:home')
        
        # Criar formset para galeria - OPCIONAL (extra=0)
        FotoGaleriaFormSet = inlineformset_factory(
            Espaco,
            FotoGaleriaEspaco,
            fields=('imagem', 'descricao', 'ordem'),
            extra=0,  # ✅ NÃO criar formulários vazios obrigatórios
            max_num=7,
            can_delete=True
        )
        
        form = EspacoForm(request.POST, request.FILES, instance=espaco)
        galeria_formset = FotoGaleriaFormSet(request.POST, request.FILES, instance=espaco)
        
        if form.is_valid() and galeria_formset.is_valid():
            # Salvar formulário principal
            espaco_atualizado = form.save(commit=False)
            espaco_atualizado.responsavel = request.user
            espaco_atualizado.save()
            form.save_m2m()
            
            # Salvar galeria
            galeria_formset.save()
            
            messages.success(request, '✅ Perfil do espaço atualizado com sucesso!')
            return redirect('espacos:dashboard_editar')
        else:
            # ===== MENSAGENS DE ERRO DETALHADAS =====
            
            # Erros do formulário principal
            if form.errors:
                for field, errors in form.errors.items():
                    field_name = form.fields[field].label if field in form.fields else field
                    for error in errors:
                        messages.error(request, f'❌ {field_name}: {error}')
            
            # Erros do formset de galeria
            if galeria_formset.errors:
                for i, form_errors in enumerate(galeria_formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(request, f'❌ Foto {i+1} - {field}: {error}')
            
            # Erros não relacionados a campos específicos
            if galeria_formset.non_form_errors():
                for error in galeria_formset.non_form_errors():
                    messages.error(request, f'❌ Galeria: {error}')
            
            # Mensagem geral se não houver erros específicos
            if not form.errors and not galeria_formset.errors:
                messages.error(request, '❌ Erro desconhecido ao salvar. Tente novamente.')
        
        # Se houver erros, renderizar novamente
        context = self.get_context_data()
        context['form'] = form
        context['galeria_formset'] = galeria_formset
        return self.render_to_response(context)

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
        from agendamentos.models import VinculoTerapeutaEspaco
        
        context = super().get_context_data(**kwargs)
        
        espaco = Espaco.objects.filter(
            responsavel=self.request.user
        ).first()
        
        context['espaco'] = espaco
        
        # Terapeutas com vínculo APROVADO
        # Retorna objetos Terapeuta para manter compatibilidade com o template
        vinculos_aprovados = VinculoTerapeutaEspaco.objects.filter(
            espaco=espaco,
            status='APROVADO',
            is_active=True
        )

        from terapeutas.models import Terapeuta
        context['terapeutas_vinculados'] = Terapeuta.objects.filter(
            vinculos_espacos__espaco=espaco,
            vinculos_espacos__status='APROVADO',
            vinculos_espacos__is_active=True
        )
        context['total_vinculados'] = vinculos_aprovados.count()
        
        # Solicitações PENDENTES aguardando aprovação do espaço
        context['solicitacoes_pendentes'] = VinculoTerapeutaEspaco.objects.filter(
            espaco=espaco,
            status='PENDENTE',
            is_active=True
        ).select_related('terapeuta')
        
        context['total_pendentes'] = context['solicitacoes_pendentes'].count()
        
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

# ===============================================================
# VIEW: DASHBOARD - GERENCIAR SALAS (AGENDAMENTO)
# ===============================================================
class DashboardSalasView(EspacoRequiredMixin, ListView):
    """
    View para listar e gerenciar salas do espaço.
    Disponível apenas para espaços Premium S+.
    """
    model = Sala
    template_name = 'espacos/dashboard/salas_lista.html'
    context_object_name = 'salas'
    
    def get_queryset(self):
        """Retorna apenas salas do espaço do usuário logado"""
        # Busca o espaço do usuário logado
        espaco = Espaco.objects.filter(responsavel=self.request.user).first()
        
        if not espaco:
            return Sala.objects.none()
        
        return Sala.objects.filter(
            espaco=espaco
        ).prefetch_related('comodidades').order_by('-is_active', 'nome')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Busca o espaço do usuário logado
        espaco = Espaco.objects.filter(responsavel=self.request.user).first()
        
        # Adiciona o espaço ao contexto
        context['espaco'] = espaco
        
        # Verifica se tem permissão (Premium S+ ou Combo)
        # Buscar assinatura ativa do usuário
        if espaco:
            from core.models import Assinatura
            
            assinatura = Assinatura.objects.filter(
                usuario=self.request.user,  # ✅ self.request.user
                status='active'
            ).select_related('plano').first()
            
            # Verificar se o plano permite gerenciamento de salas
            if assinatura and assinatura.plano:
                context['tem_permissao'] = assinatura.plano.nome in [
                    'premium_s_plus', 
                    'combo_a_s_plus'
                ]
            else:
                context['tem_permissao'] = False
        else:
            context['tem_permissao'] = False
        
        # Estatísticas básicas
        context['total_salas'] = self.get_queryset().count()
        context['salas_ativas'] = self.get_queryset().filter(is_active=True).count()
        context['salas_inativas'] = self.get_queryset().filter(is_active=False).count()
        
        return context


class DashboardSalaCriarView(EspacoRequiredMixin, CreateView):
    """
    Título: Criar Nova Sala
    Descrição: Formulário para cadastrar nova sala no espaço.
               Sincronizado com o Django Admin.
    Autor: Will
    Data: 30/12/2024
    """
    model = Sala
    template_name = 'espacos/dashboard/sala_form.html'
    fields = [
        'nome', 'capacidade', 'valor_sessao', 'duracao_sessao',
        'horario_abertura', 'horario_fechamento', 'foto', 'comodidades'
    ]
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o espaço tem permissão (Premium S+)
        """

        espaco = Espaco.objects.filter(responsavel=request.user).first()

        if not espaco:
            messages.error(request, 'Espaço não encontrado.')
            return redirect('espacos:dashboard')

        # Verificar se tem assinatura ativa com plano adequado
        assinatura = Assinatura.objects.filter(
            usuario=request.user,  # ✅ request.user (sem self)
            status='active'
        ).select_related('plano').first()

        tem_permissao = False
        if assinatura and assinatura.plano:
            tem_permissao = assinatura.plano.nome in ['premium_s_plus', 'combo_a_s_plus']

        if not tem_permissao:
            messages.error(
                request,
                'O sistema de agendamento de salas está disponível apenas para planos Premium S+ ou Combo Premium.'
            )
            return redirect('espacos:dashboard_salas')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        """
        Customiza o formulário para filtrar comodidades do espaço
        """
        form = super().get_form(form_class)
        espaco = Espaco.objects.filter(responsavel=self.request.user).first()
        
        # Filtra apenas comodidades do espaço
        if espaco:
            form.fields['comodidades'].queryset = espaco.comodidades.all()
        
        # Adiciona classes CSS e configurações
        form.fields['comodidades'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'size': '6'
        })
        
        # Adiciona classes para os outros campos
        for field_name, field in form.fields.items():
            if field_name != 'comodidades':
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
                })
        
        return form
    
    def form_valid(self, form):
        """
        Associa a sala ao espaço do usuário logado
        """
        from django.db import IntegrityError
        
        espaco = Espaco.objects.filter(responsavel=self.request.user).first()
        form.instance.espaco = espaco
        
        try:
            # Tentar salvar a sala
            response = super().form_valid(form)
            
            messages.success(
                self.request,
                f'✅ Sala "{form.instance.nome}" criada com sucesso!'
            )
            
            return response
            
        except IntegrityError:
            # Erro de sala duplicada
            messages.error(
                self.request,
                f'❌ Erro: Já existe uma sala chamada "{form.cleaned_data["nome"]}" neste espaço. '
                f'Por favor, escolha outro nome.'
            )
            
            # Retornar ao formulário com os dados preenchidos
            return self.form_invalid(form)
    
    def get_success_url(self):
        """
        Redireciona para a lista de salas após criar
        """
        return reverse('espacos:dashboard_salas')
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações ao contexto
        """
        context = super().get_context_data(**kwargs)
        espaco = Espaco.objects.filter(responsavel=self.request.user).first()
        context['espaco'] = espaco
        context['titulo'] = 'Criar Nova Sala'
        context['botao_texto'] = 'Criar Sala'
        return context


class DashboardSalaEditarView(EspacoRequiredMixin, UpdateView):
    """
    Título: Editar Sala Existente
    Descrição: Formulário para editar dados de uma sala.
               Sincronizado com o Django Admin.
    Autor: Will
    Data: 30/12/2024
    """
    model = Sala
    template_name = 'espacos/dashboard/sala_form.html'
    fields = [
        'nome', 'capacidade', 'valor_sessao', 'duracao_sessao',
        'horario_abertura', 'horario_fechamento', 'foto', 'comodidades', 'is_active'
    ]
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o espaço tem permissão e se a sala pertence a ele
        """

        espaco = Espaco.objects.filter(responsavel=request.user).first()

        if not espaco:
            messages.error(request, 'Espaço não encontrado.')
            return redirect('espacos:dashboard')

        # Verificar se tem assinatura ativa com plano adequado
        assinatura = Assinatura.objects.filter(
            usuario=request.user,  # ✅ request.user (sem self)
            status='active'
        ).select_related('plano').first()

        tem_permissao = False
        if assinatura and assinatura.plano:
            tem_permissao = assinatura.plano.nome in ['premium_s_plus', 'combo_a_s_plus']

        if not tem_permissao:
            messages.error(
                request,
                'O sistema de agendamento de salas está disponível apenas para planos Premium S+ ou Combo Premium.'
            )
            return redirect('espacos:dashboard_salas')
        
        # Verifica se a sala pertence ao espaço
        sala = self.get_object()
        if sala.espaco != espaco:
            messages.error(request, 'Você não tem permissão para editar esta sala.')
            return redirect('espacos:dashboard_salas')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Retorna apenas salas do espaço do usuário
        """
        espaco = Espaco.objects.filter(responsavel=self.request.user).first()
        
        if not espaco:
            return Sala.objects.none()
        
        return Sala.objects.filter(espaco=espaco)
    
    def get_form(self, form_class=None):
        """
        Customiza o formulário para filtrar comodidades do espaço
        """
        form = super().get_form(form_class)
        espaco = Espaco.objects.filter(responsavel=self.request.user).first()
        
        # Filtra apenas comodidades do espaço
        if espaco:
            form.fields['comodidades'].queryset = espaco.comodidades.all()
        
        # Adiciona classes CSS
        form.fields['comodidades'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'size': '6'
        })
        
        # Adiciona classes para os outros campos
        for field_name, field in form.fields.items():
            if field_name != 'comodidades' and field_name != 'is_active':
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
                })
        
        return form
    
    def form_valid(self, form):
        """
        Salva as alterações
        """
        from django.db import IntegrityError
        
        try:
            # Tentar salvar as alterações
            response = super().form_valid(form)
            
            messages.success(
                self.request,
                f'✅ Sala "{form.instance.nome}" atualizada com sucesso!'
            )
            
            return response
            
        except IntegrityError:
            # Erro de sala duplicada
            messages.error(
                self.request,
                f'❌ Erro: Já existe outra sala chamada "{form.cleaned_data["nome"]}" neste espaço. '
                f'Por favor, escolha outro nome.'
            )
            
            # Retornar ao formulário com os dados preenchidos
            return self.form_invalid(form)
    
    def get_success_url(self):
        """
        Redireciona para a lista de salas após editar
        """
        return reverse('espacos:dashboard_salas')
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações ao contexto
        """
        context = super().get_context_data(**kwargs)
        espaco = Espaco.objects.filter(responsavel=self.request.user).first()
        context['espaco'] = espaco
        context['titulo'] = f'Editar Sala: {self.object.nome}'
        context['botao_texto'] = 'Salvar Alterações'
        return context


class DashboardSalaToggleView(EspacoRequiredMixin, View):
    """
    Título: Ativar/Desativar Sala
    Descrição: View para alternar status is_active da sala via AJAX ou redirect
    Autor: Will
    Data: 30/12/2024
    """
    
    def get(self, request, pk):
        """
        Alterna o status is_active da sala
        """

        espaco = Espaco.objects.filter(responsavel=request.user).first()

        if not espaco:
            messages.error(request, 'Espaço não encontrado.')
            return redirect('espacos:dashboard')

        # Verificar se tem assinatura ativa com plano adequado
        assinatura = Assinatura.objects.filter(
            usuario=request.user,  # ✅ request.user (sem self)
            status='active'
        ).select_related('plano').first()

        tem_permissao = False
        if assinatura and assinatura.plano:
            tem_permissao = assinatura.plano.nome in ['premium_s_plus', 'combo_a_s_plus']

        if not tem_permissao:
            messages.error(
                request,
                'Você não tem permissão para esta ação.'
            )
            return redirect('espacos:dashboard_salas')
        
        # Busca a sala
        try:
            sala = Sala.objects.get(pk=pk, espaco=espaco)
        except Sala.DoesNotExist:
            messages.error(request, 'Sala não encontrada.')
            return redirect('espacos:dashboard_salas')
        
        # Alterna o status
        sala.is_active = not sala.is_active
        sala.save()
        
        # Mensagem de sucesso
        status = 'ativada' if sala.is_active else 'desativada'
        messages.success(
            request,
            f'Sala "{sala.nome}" {status} com sucesso!'
        )
        
        return redirect('espacos:dashboard_salas')

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

class AprovarVinculoTerapeutaView(EspacoRequiredMixin, View):
    """
    Título: Aprovar Vínculo com Terapeuta
    Descrição: Espaço aprova solicitação de vínculo de um terapeuta.
               Muda status para APROVADO e registra data de aprovação.
    URL: /espacos/dashboard/vinculos/<id>/aprovar/
    """

    def post(self, request, vinculo_id):
        from agendamentos.models import VinculoTerapeutaEspaco
        from django.utils import timezone

        # Busca o vínculo garantindo que é do espaço logado
        espaco = Espaco.objects.filter(responsavel=request.user).first()

        vinculo = get_object_or_404(
            VinculoTerapeutaEspaco,
            pk=vinculo_id,
            espaco=espaco,
            status='PENDENTE'
        )

        # Aprova o vínculo
        vinculo.status = 'APROVADO'
        vinculo.data_aprovacao = timezone.now()
        vinculo.save()

        messages.success(
            request,
            f'✅ Vínculo com {vinculo.terapeuta} aprovado com sucesso!'
        )

        return redirect('espacos:dashboard_terapeutas')


class RecusarVinculoTerapeutaView(EspacoRequiredMixin, View):
    """
    Título: Recusar Vínculo com Terapeuta
    Descrição: Espaço recusa solicitação de vínculo de um terapeuta.
               Muda status para RECUSADO.
    URL: /espacos/dashboard/vinculos/<id>/recusar/
    """

    def post(self, request, vinculo_id):
        from agendamentos.models import VinculoTerapeutaEspaco

        # Busca o vínculo garantindo que é do espaço logado
        espaco = Espaco.objects.filter(responsavel=request.user).first()

        vinculo = get_object_or_404(
            VinculoTerapeutaEspaco,
            pk=vinculo_id,
            espaco=espaco,
            status='PENDENTE'
        )

        # Recusa o vínculo
        vinculo.status = 'RECUSADO'
        vinculo.is_active = False
        vinculo.save()

        messages.warning(
            request,
            f'Solicitação de {vinculo.terapeuta} recusada.'
        )

        return redirect('espacos:dashboard_terapeutas')
    
class ConvidarTerapeutaView(EspacoRequiredMixin, View):
    """
    Título: Convidar Terapeuta
    Descrição: Espaço convida um terapeuta pelo email para se vincular.
               Cria VinculoTerapeutaEspaco com status PENDENTE e tipo CONVITE.
    URL: /espacos/dashboard/vinculos/convidar/
    """

    def post(self, request):
        from agendamentos.models import VinculoTerapeutaEspaco, ConviteExterno
        from terapeutas.models import Terapeuta
        from django.utils import timezone
        from datetime import timedelta
        from django.core.mail import send_mail
        from django.template.loader import render_to_string

        espaco = Espaco.objects.filter(responsavel=request.user).first()
        email = request.POST.get('email_terapeuta', '').strip()
        mensagem = request.POST.get('mensagem', '').strip()

        if not email:
            messages.error(request, '❌ Informe o email do terapeuta.')
            return redirect('espacos:dashboard_terapeutas')

        # ===== FLUXO 1: Terapeuta já cadastrado =====
        try:
            from django.contrib.auth.models import User
            usuario = User.objects.get(email=email)
            terapeuta = Terapeuta.objects.get(user=usuario)

            # Verifica se já existe vínculo
            vinculo_existente = VinculoTerapeutaEspaco.objects.filter(
                terapeuta=terapeuta,
                espaco=espaco
            ).first()

            if vinculo_existente:
                if vinculo_existente.status == 'APROVADO':
                    messages.warning(request, '⚠️ Este terapeuta já está vinculado ao seu espaço.')
                elif vinculo_existente.status == 'PENDENTE':
                    messages.warning(request, '⚠️ Já existe um convite pendente para este terapeuta.')
                else:
                    vinculo_existente.status = 'PENDENTE'
                    vinculo_existente.tipo = 'CONVITE'
                    vinculo_existente.is_active = True
                    vinculo_existente.save()
                    messages.success(request, f'✅ Convite reenviado para {terapeuta}!')
            else:
                VinculoTerapeutaEspaco.objects.create(
                    terapeuta=terapeuta,
                    espaco=espaco,
                    status='PENDENTE',
                    tipo='CONVITE',
                )
                messages.success(
                    request,
                    f'✅ Convite enviado para {terapeuta}! Aguarde a confirmação.'
                )

        except (User.DoesNotExist, Terapeuta.DoesNotExist):

            # ===== FLUXO 2: Terapeuta não cadastrado =====
            # Verifica se já existe convite pendente para esse email
            convite_existente = ConviteExterno.objects.filter(
                espaco=espaco,
                email=email,
                usado=False,
                expira_em__gt=timezone.now()
            ).first()

            if convite_existente:
                messages.warning(
                    request,
                    f'⚠️ Já existe um convite pendente para {email}.'
                )
                return redirect('espacos:dashboard_terapeutas')

            # Cria convite externo com validade de 30 dias
            convite = ConviteExterno.objects.create(
                espaco=espaco,
                email=email,
                mensagem=mensagem,
                expira_em=timezone.now() + timedelta(days=30)
            )

            # Monta links para o email
            base_url = request.build_absolute_uri('/')[:-1]
            link_cadastro = f"{base_url}/parceiro/?convite={convite.token}"
            link_login = f"{base_url}/accounts/login/?convite={convite.token}"

            # Renderiza o template do email
            html_email = render_to_string('emails/convite_terapeuta.html', {
                'espaco': espaco,
                'mensagem': mensagem,
                'link_cadastro': link_cadastro,
                'link_login': link_login,
                'expira_em': convite.expira_em.strftime('%d/%m/%Y'),
            })

            # Envia o email
            try:
                send_mail(
                    subject=f'Convite do {espaco.nome} - Espaço Vital',
                    message=f'Você recebeu um convite do {espaco.nome} para usar a plataforma Espaço Vital.',
                    from_email='noreply@espacovital.com.br',
                    recipient_list=[email],
                    html_message=html_email,
                    fail_silently=False,
                )
                messages.success(
                    request,
                    f'✅ Convite enviado para {email}! O terapeuta receberá um email com instruções.'
                )
            except Exception as e:
                convite.delete()
                messages.error(
                    request,
                    f'❌ Erro ao enviar email. Tente novamente.'
                )

        return redirect('espacos:dashboard_terapeutas')