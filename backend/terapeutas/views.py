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
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from .models import (
    Terapeuta, Especialidade, 
    Avaliacao, Contato, SessionType, ProfileType, ClientType
)
from core.models import Estado, Cidade
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
import json


def processar_multiplas_cidades(request, terapeuta_instance):
    """
    Processa e salva as múltiplas cidades do formulário
    """
    from .models import Cidade
    
    # Cidade principal (obrigatória)
    cidade_principal_id = request.POST.get('cidade_principal')
    if cidade_principal_id:
        try:
            cidade_principal = Cidade.objects.get(id=cidade_principal_id)
            terapeuta_instance.cidade_principal = cidade_principal
        except Cidade.DoesNotExist:
            return False, "Cidade principal inválida"
    else:
        return False, "Cidade principal é obrigatória"
    
    # Salvar terapeuta com cidade principal
    terapeuta_instance.save()
    
    # Processar cidades adicionais
    cidades_adicionais = []
    
    # Buscar todas as cidades adicionais do POST
    for key, value in request.POST.items():
        if key.startswith('cidade_adicional_') and value:
            try:
                cidade_adicional = Cidade.objects.get(id=value)
                # Evitar duplicatas (não adicionar a cidade principal)
                if cidade_adicional.id != cidade_principal.id:
                    cidades_adicionais.append(cidade_adicional)
            except Cidade.DoesNotExist:
                continue  # Ignora cidades inválidas
    
    # Limpar cidades antigas e adicionar as novas
    terapeuta_instance.cidades_atendimento.clear()
    if cidades_adicionais:
        terapeuta_instance.cidades_atendimento.add(*cidades_adicionais)
    
    return True, "Cidades processadas com sucesso"

# ===============================================================
# VIEWS DE BUSCA E LISTAGEM
# ===============================================================

class TerapeutaListView(ListView):
    """
    View principal para listagem de terapeutas com filtros
    Baseada no layout da busca avançada compartilhado
    """
    model = Terapeuta
    template_name = 'terapeutas/listagem_resultados.html'
    context_object_name = 'terapeutas'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Aplica todos os filtros baseados nos parâmetros GET
        Exatamente como no layout da busca avançada
        """
        queryset = Terapeuta.objects.filter(is_active=True).select_related(
            'cidade_principal', 'cidade_principal__estado'
        ).prefetch_related(
            'cidades_atendimento', 'especialidades', 'avaliacoes'
        ).annotate(
            avg_avaliacoes=Avg('avaliacoes__nota'),
            count_avaliacoes=Count('avaliacoes', filter=Q(avaliacoes__is_active=True))
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
        pais_id = self.request.GET.get('pais')
        if pais_id:
            try:
                # Filtra pelo campo 'pais' direto do terapeuta
                queryset = queryset.filter(pais_id=pais_id)
            except ValueError:
                pass

        # Filtro por Cidade
        cidade_id = self.request.GET.get('cidade')
        if cidade_id:
            try:
                queryset = queryset.filter(
                    Q(cidade_principal_id=cidade_id) |
                    Q(cidades_atendimento__id=cidade_id)
                ).distinct()
            except ValueError:
                pass

        # Filtro por Estado
        estado_id = self.request.GET.get('estado')
        if estado_id:
            try:
                queryset = queryset.filter(
                    Q(cidade_principal__estado_id=estado_id) |
                    Q(cidades_atendimento__estado_id=estado_id)
                ).distinct()
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
            queryset = queryset.order_by('-avg_avaliacoes', '-count_avaliacoes')
        elif ordering == 'mais_experiente':
            queryset = queryset.order_by('-experiencia_anos')
        elif ordering == 'nome':
            queryset = queryset.order_by('nome_exibicao')
        else:  # relevancia (padrão)
            # Ordenação com prioridade de plano: Categoria S > Premium A > Basic
            from django.db.models import Case, When, IntegerField
            
            queryset = queryset.annotate(
                prioridade_plano=Case(
                    When(plano='premium_s', then=3),
                    When(plano='premium_a', then=2),
                    When(plano='basic', then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ).order_by(
                '-prioridade_plano',  # Categoria S primeiro
                '-verificado',         # Depois verificados
                '-avg_avaliacoes',     # Depois por avaliação
                'nome_exibicao'        # Por fim alfabético
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
            'pais': self.request.GET.get('pais', ''),
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
    View para listagem de terapeutas que processa filtros vindos do modal
    Usado para /terapeutas/lista/ com parâmetros da busca
    """
    # DEBUG: Ver parâmetros recebidos
    print(f"=== DEBUG FILTROS ===")
    print(f"GET params: {dict(request.GET)}")
    
    terapeutas = Terapeuta.objects.filter(is_active=True).select_related(
        'cidade_principal', 'cidade_principal__estado'
    ).prefetch_related(
        'cidades_atendimento',
        'especialidades', 'avaliacoes'
    )
    
    print(f"Terapeutas antes dos filtros: {terapeutas.count()}")
    
    # ===== PROCESSAR FILTROS DO MODAL =====
    
    # Filtro: Tipo de sessão
    tipos_sessao = request.GET.getlist('tipo_sessao')
    if tipos_sessao:
        print(f"Filtrando por tipos_sessao: {tipos_sessao}")
        # O campo no modelo é 'tipos_sessao' (JSONField ou CharField)
        # Filtrar terapeutas que atendem pelo menos um dos tipos
        filtro_sessao = Q()
        for tipo in tipos_sessao:
            if tipo in ['presencial', 'online', 'domicilio']:
                # Se for JSONField, usar contains
                filtro_sessao |= Q(tipos_sessao__icontains=tipo)
        
        if filtro_sessao:
            terapeutas = terapeutas.filter(filtro_sessao)
            print(f"Terapeutas após filtro tipo_sessao: {terapeutas.count()}")
    
    # Filtro: Localização (Estado e Cidade)
    estado = request.GET.get('estado')
    cidade = request.GET.get('cidade')
    
    if estado:
        print(f"Filtrando por estado: {estado}")
        # Filtrar por estado usando nome ou sigla
        terapeutas = terapeutas.filter(
            Q(cidade_principal__estado__nome__icontains=estado) | 
            Q(cidade_principal__estado__sigla__iexact=estado) |
            Q(cidades_atendimento__estado__nome__icontains=estado) |
            Q(cidades_atendimento__estado__sigla__iexact=estado)
        ).distinct()
        print(f"Terapeutas após filtro estado: {terapeutas.count()}")
    
    if cidade:
        print(f"Filtrando por cidade: {cidade}")
        # Filtrar por cidade usando apenas nome
        terapeutas = terapeutas.filter(
            Q(cidade_principal__nome__icontains=cidade) |
            Q(cidades_atendimento__nome__icontains=cidade)
        ).distinct()
        print(f"Terapeutas após filtro cidade: {terapeutas.count()}")
        
        # DEBUG: Ver quais cidades existem no banco
        cidades_existentes = Cidade.objects.values_list('nome', flat=True)
        print(f"Cidades no banco: {list(cidades_existentes)}")
    
    # Filtro: Terapias/Especialidades
    terapias = request.GET.getlist('terapias')
    if terapias:
        print(f"Filtrando por terapias: {terapias}")
        # Buscar especialidades pelos nomes
        especialidades_ids = []
        for terapia in terapias:
            # Converter nomes do modal para especialidades do banco
            try:
                if terapia == 'aromaterapia':
                    especialidade = Especialidade.objects.get(nome__icontains='Aromaterapia')
                elif terapia == 'cristaloterapia':
                    especialidade = Especialidade.objects.get(nome__icontains='Cristaloterapia')
                elif terapia == 'massoterapia':
                    especialidade = Especialidade.objects.get(nome__icontains='Massoterapia')
                elif terapia == 'reiki':
                    especialidade = Especialidade.objects.get(nome__icontains='Reiki')
                elif terapia == 'terapia-tantrica':
                    especialidade = Especialidade.objects.get(nome__icontains='Tântrica')
                elif terapia == 'ThetaHealing':
                    especialidade = Especialidade.objects.get(nome__icontains='ThetaHealing')
                elif terapia == 'psicoterapia':
                    especialidade = Especialidade.objects.get(nome__icontains='Psicoterapia')
                elif terapia == 'acupuntura':
                    especialidade = Especialidade.objects.get(nome__icontains='Acupuntura')
                else:
                    # Busca genérica
                    especialidade = Especialidade.objects.filter(nome__icontains=terapia).first()
                
                if especialidade:
                    especialidades_ids.append(especialidade.id)
            except Especialidade.DoesNotExist:
                continue
        
        if especialidades_ids:
            terapeutas = terapeutas.filter(especialidades__id__in=especialidades_ids).distinct()
            print(f"Terapeutas após filtro terapias: {terapeutas.count()}")
    
    # Filtro: Acessibilidade
    acessibilidade = request.GET.get('acessibilidade')
    if acessibilidade == 'sim':
        terapeutas = terapeutas.filter(acessibilidade=True)
        print(f"Terapeutas após filtro acessibilidade=True: {terapeutas.count()}")
    elif acessibilidade == 'nao':
        terapeutas = terapeutas.filter(acessibilidade=False)
        print(f"Terapeutas após filtro acessibilidade=False: {terapeutas.count()}")
    
    print(f"=== FIM DEBUG ===")
    
    # ===== FILTRO POR ESPECIALIDADE (PARA URLs DIRETAS) =====
    especialidade = None
    if especialidade_slug:
        especialidade = get_object_or_404(
            Especialidade, 
            slug=especialidade_slug, 
            is_active=True
        )
        terapeutas = terapeutas.filter(especialidades=especialidade)
    
    # ===== ORDENAÇÃO =====
    # Ordenação padrão: destaque > premium > verificado > nome
    terapeutas = terapeutas.order_by(
        '-destaque', '-premium', '-verificado', 'nome_exibicao'
    )
    
    # ===== PAGINAÇÃO =====
    paginator = Paginator(terapeutas, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # ===== DADOS PARA O TEMPLATE =====
    estados = Estado.objects.all().order_by('nome')
    especialidades = Especialidade.objects.filter(is_active=True).order_by('nome')
    
    # Construir título baseado nos filtros
    titulo_pagina = "Terapeutas"
    if especialidade:
        titulo_pagina = f"{especialidade.nome}"
    elif cidade:
        # Usar o nome da cidade diretamente, não buscar por ID
        titulo_pagina = f"Terapeutas em {cidade}"
    elif estado:
        # Usar o nome do estado diretamente
        titulo_pagina = f"Terapeutas no {estado}"
    
    # Informações sobre filtros aplicados
    filtros_aplicados = []
    if tipos_sessao:
        filtros_aplicados.append(f"Tipos: {', '.join(tipos_sessao)}")
    if terapias:
        filtros_aplicados.append(f"Terapias: {', '.join(terapias)}")
    if acessibilidade:
        filtros_aplicados.append(f"Acessibilidade: {acessibilidade}")
    
    context = {
        'terapeutas': page_obj,
        'especialidade_atual': especialidade,
        'estados': estados,
        'especialidades': especialidades,
        'total_resultados': terapeutas.count(),
        'titulo_pagina': titulo_pagina,
        'filtros_aplicados': filtros_aplicados,
        'page_title': f'{titulo_pagina} - Espaço Vital',
        'meta_description': f'Encontre os melhores {titulo_pagina.lower()} verificados pela plataforma.'
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
            'cidade_principal', 'cidade_principal__estado', 'user'
        ).prefetch_related(
            'cidades_atendimento',
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
            Q(cidade_principal=terapeuta.cidade_principal) |
            Q(cidades_atendimento__in=terapeuta.get_todas_cidades()),
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
    ).select_related('cidade_principal').prefetch_related(
        'cidades_atendimento',
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
            'cidade': f"{terapeuta.cidade_principal.nome} - {terapeuta.cidade_principal.estado.sigla}" if terapeuta.cidade_principal else '',
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

class TerapeutaCreateView(LoginRequiredMixin, CreateView):
    """
    View para cadastro de novo terapeuta
    Com suporte a múltiplas cidades
    """
    model = Terapeuta
    template_name = 'terapeutas/cadastro.html'
    fields = [
        'nome_exibicao', 'bio_curta', 'bio_completa', 'telefone', 
        'whatsapp', 'email', 'foto_perfil', 'especialidades',
        'tipos_sessao', 'tipo_perfil', 'para_quem', 'acessibilidade'
    ]
    
    def get_context_data(self, **kwargs):
        """
        Adiciona países, estados e cidades ao contexto
        """
        from core.models import Pais
        
        context = super().get_context_data(**kwargs)
        context['paises'] = Pais.objects.filter(ativo=True).order_by('nome')
        context['estados'] = Estado.objects.filter(ativo=True).order_by('nome')
        context['cidades'] = Cidade.objects.filter(ativo=True).order_by('nome')
        context['page_title'] = 'Cadastrar Terapeuta - Espaço Vital'
        return context

    
    def form_valid(self, form):
        """
        Processa formulário e múltiplas cidades
        """
        # Associar usuário logado
        form.instance.user = self.request.user
        
        # Salvar formulário básico
        response = super().form_valid(form)
        
        # Processar múltiplas cidades
        sucesso, mensagem = processar_multiplas_cidades(self.request, self.object)
        
        if not sucesso:
            messages.error(self.request, f"Erro: {mensagem}")
            return self.form_invalid(form)
        
        messages.success(
            self.request, 
            "Perfil de terapeuta cadastrado com sucesso! "
            "Suas informações serão verificadas em até 24h."
        )
        
        return response
    
    def get_success_url(self):
        return reverse('terapeutas:profile', kwargs={'slug': self.object.slug})


class TerapeutaUpdateView(LoginRequiredMixin, UpdateView):
    """
    View para edição de terapeuta existente
    Com suporte a múltiplas cidades
    """
    model = Terapeuta
    template_name = 'terapeutas/editar.html'
    fields = [
        'nome_exibicao', 'bio_curta', 'bio_completa', 'telefone', 
        'whatsapp', 'email', 'foto_perfil', 'especialidades',
        'tipos_sessao', 'tipo_perfil', 'para_quem', 'acessibilidade'
    ]
    
    def get_object(self):
        """
        Garante que usuário só edita próprio perfil
        """
        return get_object_or_404(
            Terapeuta, 
            user=self.request.user,
            slug=self.kwargs['slug']
        )
    
    def get_context_data(self, **kwargs):
        """
        Adiciona países, estados e cidades ao contexto
        """
        from core.models import Pais
        
        context = super().get_context_data(**kwargs)
        context['paises'] = Pais.objects.filter(ativo=True).order_by('nome')
        context['estados'] = Estado.objects.filter(ativo=True).order_by('nome')
        context['cidades'] = Cidade.objects.filter(ativo=True).order_by('nome')
        context['page_title'] = f'Editar Perfil - {self.object.nome_exibicao}'
        return context

    
    def form_valid(self, form):
        """
        Processa formulário e múltiplas cidades
        """
        # Salvar formulário básico
        response = super().form_valid(form)
        
        # Processar múltiplas cidades
        sucesso, mensagem = processar_multiplas_cidades(self.request, self.object)
        
        if not sucesso:
            messages.error(self.request, f"Erro: {mensagem}")
            return self.form_invalid(form)
        
        messages.success(
            self.request, 
            "Perfil atualizado com sucesso!"
        )
        
        return response
    
    def get_success_url(self):
        return reverse('terapeutas:profile', kwargs={'slug': self.object.slug})
    
class TerapeutaRequiredMixin(LoginRequiredMixin):
    """
    Mixin: Verificar se usuário é terapeuta
    Descrição: Garante que apenas terapeutas autenticados acessem o dashboard
               Redireciona para home caso não tenha perfil de terapeuta
    Uso: Todas as views do dashboard herdam este mixin
    """
    login_url = '/accounts/login/'  # URL de login do django-allauth
    
    def dispatch(self, request, *args, **kwargs):
        """
        Intercepta a requisição antes de processar
        Verifica autenticação e perfil de terapeuta
        """
        # Verificar se está autenticado
        if not request.user.is_authenticated:
            messages.warning(
                request, 
                'Você precisa estar logado para acessar o dashboard.'
            )
            return self.handle_no_permission()
        
        # Verificar se tem perfil de terapeuta
        if not hasattr(request.user, 'terapeuta'):
            messages.error(
                request, 
                'Você precisa ter um perfil de terapeuta para acessar esta área. '
                'Entre em contato conosco para criar seu perfil.'
            )
            return redirect('core:home')
        
        return super().dispatch(request, *args, **kwargs)


class DashboardView(TerapeutaRequiredMixin, TemplateView):
    """
    View: Dashboard Principal do Terapeuta
    Descrição: Página inicial do painel privado com visão geral
               Exibe estatísticas, completude do perfil e resumos
    Template: terapeutas/dashboard/dashboard.html
    URL: /terapeutas/dashboard/
    """
    template_name = 'terapeutas/dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        Adiciona dados do dashboard ao contexto
        """
        context = super().get_context_data(**kwargs)
        
        # Buscar o terapeuta logado
        terapeuta = self.request.user.terapeuta
        
        # ===== ESTATÍSTICAS BÁSICAS =====
        context['terapeuta'] = terapeuta
        context['total_visualizacoes'] = terapeuta.visualizacoes
        context['total_contatos'] = terapeuta.total_contatos
        context['rating_medio'] = terapeuta.rating_medio
        context['total_avaliacoes'] = terapeuta.total_avaliacoes
        
        # ===== COMPLETUDE DO PERFIL =====
        completude = self._calcular_completude_perfil(terapeuta)
        context['completude_perfil'] = completude['percentual']
        context['perfil_completo'] = completude['completo']
        context['campos_faltantes'] = completude['campos_faltantes']
        
        # ===== ÚLTIMAS AVALIAÇÕES =====
        context['ultimas_avaliacoes'] = terapeuta.avaliacoes.filter(
            is_active=True
        ).select_related('cliente').order_by('-created_at')[:5]
        
        # ===== ESPAÇOS VINCULADOS =====
        # TODO: Implementar relacionamento com espaços quando o modelo estiver pronto
        context['espacos_vinculados'] = []
        context['total_espacos'] = 0
        
        # ===== ESTATÍSTICAS DO MÊS =====
        data_limite = timezone.now() - timedelta(days=30)
        
        # Avaliações dos últimos 30 dias
        avaliacoes_mes = terapeuta.avaliacoes.filter(
            created_at__gte=data_limite,
            is_active=True
        ).count()
        context['avaliacoes_mes'] = avaliacoes_mes
        
        # Contatos dos últimos 30 dias
        contatos_mes = terapeuta.contatos_recebidos.filter(
            created_at__gte=data_limite
        ).count()
        context['contatos_mes'] = contatos_mes
        
        return context
    
    def _calcular_completude_perfil(self, terapeuta):
        """
        Calcula percentual de completude do perfil
        """
        campos_obrigatorios = [
            bool(terapeuta.foto_perfil),
            bool(terapeuta.foto_capa),
            bool(terapeuta.bio_completa),
            bool(terapeuta.whatsapp),
            bool(terapeuta.especialidades.exists()),
            bool(terapeuta.formacao),
            terapeuta.experiencia_anos > 0,
            bool(terapeuta.cidade_principal or terapeuta.cidade_texto),
        ]
        
        campos_opcionais = [
            bool(terapeuta.instagram),
            bool(terapeuta.facebook),
            bool(terapeuta.registro_profissional),
            bool(terapeuta.metodologia),
            terapeuta.fotos_galeria.count() > 0,
        ]
        
        # Peso: obrigatórios valem 70%, opcionais 30%
        total_obrigatorios = len(campos_obrigatorios)
        preenchidos_obrigatorios = sum(campos_obrigatorios)
        
        total_opcionais = len(campos_opcionais)
        preenchidos_opcionais = sum(campos_opcionais)
        
        percentual_obrigatorios = (preenchidos_obrigatorios / total_obrigatorios) * 70
        percentual_opcionais = (preenchidos_opcionais / total_opcionais) * 30
        
        percentual_total = int(percentual_obrigatorios + percentual_opcionais)
        
        return {
            'percentual': percentual_total,
            'campos_faltantes': total_obrigatorios - preenchidos_obrigatorios,
            'completo': percentual_total >= 80
        }


class DashboardEditarPerfilView(TerapeutaRequiredMixin, TemplateView):
    """
    View: Editar Perfil do Terapeuta
    Descrição: Formulário completo para edição de dados profissionais
               Upload de foto, bio, especialidades, cidades, etc.
    Template: terapeutas/dashboard/editar_perfil.html
    URL: /terapeutas/dashboard/perfil/
    """
    template_name = 'terapeutas/dashboard/editar_perfil.html'
    
    def get_context_data(self, **kwargs):
        """
        Adiciona dados necessários para o formulário
        """
        context = super().get_context_data(**kwargs)
        
        # Terapeuta logado
        terapeuta = self.request.user.terapeuta
        context['terapeuta'] = terapeuta
        
        # ===== OPÇÕES PARA OS SELECTS =====
        
        # Buscar todas as especialidades disponíveis
        from core.models import Especialidade
        context['todas_especialidades'] = Especialidade.objects.filter(
            is_active=True
        ).order_by('nome')
        
        # Especialidades já selecionadas pelo terapeuta
        context['especialidades_selecionadas'] = terapeuta.especialidades.values_list(
            'id', flat=True
        )
        
        # Buscar todos os estados do Brasil
        from core.models import Estado
        context['estados_brasil'] = Estado.objects.filter(
            pais__nome='Brasil',
            ativo=True
        ).order_by('nome')
        
        # Cidades já selecionadas pelo terapeuta
        context['cidades_selecionadas'] = terapeuta.cidades_atendimento.values_list(
            'id', flat=True
        )
        
        # ===== TIPOS DE SESSÃO =====
        context['tipos_sessao_disponiveis'] = [
            {'value': 'presencial', 'label': 'Presencial'},
            {'value': 'online', 'label': 'On-line'},
            {'value': 'domicilio', 'label': 'Domicílio'},
        ]
        
        # ===== PARA QUEM =====
        context['para_quem_opcoes'] = [
            {'value': 'adultos', 'label': 'Adultos'},
            {'value': 'criancas', 'label': 'Crianças'},
            {'value': 'idosos', 'label': 'Idosos'},
            {'value': 'casais', 'label': 'Casais'},
            {'value': 'grupos', 'label': 'Grupos'},
        ]
        
        return context


class DashboardEstatisticasView(TerapeutaRequiredMixin, TemplateView):
    """
    View: Estatísticas Detalhadas do Terapeuta
    Descrição: Métricas detalhadas de performance
               Visualizações, contatos, avaliações ao longo do tempo
    Template: terapeutas/dashboard/estatisticas.html
    URL: /terapeutas/dashboard/estatisticas/
    """
    template_name = 'terapeutas/dashboard/estatisticas.html'
    
    def get_context_data(self, **kwargs):
        """
        Adiciona estatísticas detalhadas ao contexto
        """
        context = super().get_context_data(**kwargs)
        
        # Terapeuta logado
        terapeuta = self.request.user.terapeuta
        context['terapeuta'] = terapeuta
        
        # ===== ESTATÍSTICAS GERAIS =====
        context['total_visualizacoes'] = terapeuta.visualizacoes
        context['total_contatos'] = terapeuta.total_contatos
        context['rating_medio'] = terapeuta.rating_medio
        context['total_avaliacoes'] = terapeuta.total_avaliacoes
        
        # ===== ESTATÍSTICAS DOS ÚLTIMOS 30 DIAS =====
        data_limite_30d = timezone.now() - timedelta(days=30)
        
        # Avaliações dos últimos 30 dias
        avaliacoes_recentes = terapeuta.avaliacoes.filter(
            created_at__gte=data_limite_30d,
            is_active=True
        )
        context['avaliacoes_mes'] = avaliacoes_recentes.count()
        
        # Média das avaliações recentes
        media_recente = avaliacoes_recentes.aggregate(
            media=Avg('nota')
        )['media']
        context['media_avaliacoes_mes'] = round(media_recente, 1) if media_recente else 0
        
        # Contatos dos últimos 30 dias
        contatos_recentes = terapeuta.contatos_recebidos.filter(
            created_at__gte=data_limite_30d
        )
        context['contatos_mes'] = contatos_recentes.count()
        
        # ===== ESTATÍSTICAS DOS ÚLTIMOS 7 DIAS =====
        data_limite_7d = timezone.now() - timedelta(days=7)
        
        context['avaliacoes_semana'] = terapeuta.avaliacoes.filter(
            created_at__gte=data_limite_7d,
            is_active=True
        ).count()
        
        context['contatos_semana'] = terapeuta.contatos_recebidos.filter(
            created_at__gte=data_limite_7d
        ).count()
        
        # ===== DISTRIBUIÇÃO DE AVALIAÇÕES POR NOTA =====
        distribuicao_notas = {}
        for nota in range(1, 6):  # 1 a 5 estrelas
            distribuicao_notas[nota] = terapeuta.avaliacoes.filter(
                nota=nota,
                is_active=True
            ).count()
        context['distribuicao_notas'] = distribuicao_notas
        
        # ===== ÚLTIMAS AVALIAÇÕES =====
        context['ultimas_avaliacoes'] = terapeuta.avaliacoes.filter(
            is_active=True
        ).select_related('cliente').order_by('-created_at')[:10]
        
        # ===== COMPARAÇÃO COM MÉDIA DA PLATAFORMA =====
        # Buscar média geral de todos os terapeutas
        from terapeutas.models import Terapeuta
        from django.db.models import Count

        # Buscar terapeutas com pelo menos 1 avaliação
        terapeutas_com_avaliacoes = Terapeuta.objects.filter(
            is_active=True
        ).annotate(
            num_avaliacoes=Count('avaliacoes', filter=Q(avaliacoes__is_active=True))
        ).filter(
            num_avaliacoes__gt=0
        )

        # Calcular média geral da plataforma
        media_plataforma = terapeutas_com_avaliacoes.aggregate(
            media=Avg('avaliacoes__nota', filter=Q(avaliacoes__is_active=True))
        )['media']
        
        context['media_plataforma'] = round(media_plataforma, 1) if media_plataforma else 0
        context['acima_da_media'] = terapeuta.rating_medio > (media_plataforma or 0)
        
        return context


class DashboardEspacosVinculadosView(TerapeutaRequiredMixin, TemplateView):
    """
    View: Gerenciar Espaços Vinculados
    Descrição: Listar espaços já vinculados e sugerir novos
               Permite adicionar/remover vínculos com espaços terapêuticos
    Template: terapeutas/dashboard/espacos_vinculados.html
    URL: /terapeutas/dashboard/espacos/
    """
    template_name = 'terapeutas/dashboard/espacos_vinculados.html'
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações sobre espaços ao contexto
        """
        context = super().get_context_data(**kwargs)
        
        # Terapeuta logado
        terapeuta = self.request.user.terapeuta
        context['terapeuta'] = terapeuta
        
        # ===== ESPAÇOS JÁ VINCULADOS =====
        # TODO: Implementar relacionamento ManyToMany entre Terapeuta e Espaco
        context['espacos_vinculados'] = []
        context['total_espacos_vinculados'] = 0
        
        # ===== SUGERIR ESPAÇOS DISPONÍVEIS =====
        from espacos.models import Espaco
        
        # Pegar IDs das cidades onde o terapeuta atende
        cidades_terapeuta_ids = list(terapeuta.cidades_atendimento.values_list('id', flat=True))
        
        # Adicionar cidade principal se existir
        if terapeuta.cidade_principal:
            cidades_terapeuta_ids.append(terapeuta.cidade_principal.id)
        
        # Buscar espaços nas mesmas cidades
        if cidades_terapeuta_ids:
            espacos_disponiveis = Espaco.objects.filter(
                is_active=True,
                cidade_id__in=cidades_terapeuta_ids
            ).select_related('cidade', 'cidade__estado').prefetch_related(
                'comodidades'
            ).order_by('nome')[:10]  # Limitar a 10 sugestões
        else:
            espacos_disponiveis = []
        
        context['espacos_disponiveis'] = espacos_disponiveis
        context['total_sugestoes'] = len(espacos_disponiveis) if espacos_disponiveis else 0
        
        # ===== VERIFICAR SE TEM CIDADES CADASTRADAS =====
        context['tem_cidades'] = terapeuta.cidades_atendimento.exists() or bool(terapeuta.cidade_principal)
        
        return context


class DashboardAssinaturaView(TerapeutaRequiredMixin, TemplateView):
    """
    View: Gerenciar Plano de Assinatura
    Descrição: Exibe plano atual e opções de upgrade
               4 planos: Basic, Premium A, Premium S
    Template: terapeutas/dashboard/assinatura.html
    URL: /terapeutas/dashboard/assinatura/
    """
    template_name = 'terapeutas/dashboard/assinatura.html'
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações sobre planos ao contexto
        """
        context = super().get_context_data(**kwargs)
        
        # Terapeuta logado
        terapeuta = self.request.user.terapeuta
        context['terapeuta'] = terapeuta
        
        # ===== PLANO ATUAL =====
        context['plano_atual'] = terapeuta.nome_plano
        context['is_basic'] = terapeuta.is_basic
        context['is_premium_a'] = terapeuta.is_premium_a
        context['is_premium_s'] = terapeuta.is_premium_s
        
        # ===== LIMITE DE CATEGORIA S =====
        from terapeutas.models import Terapeuta, PlanoChoices
        
        total_categoria_s = Terapeuta.objects.filter(
            plano=PlanoChoices.PREMIUM_S,
            is_active=True
        ).count()
        
        MAX_CATEGORIA_S = 50
        vagas_restantes_s = MAX_CATEGORIA_S - total_categoria_s
        categoria_s_disponivel = vagas_restantes_s > 0
        
        context['vagas_restantes_s'] = vagas_restantes_s
        context['categoria_s_disponivel'] = categoria_s_disponivel
        context['max_categoria_s'] = MAX_CATEGORIA_S
        
        # ===== DEFINIÇÃO DOS PLANOS =====
        context['planos'] = [
            {
                'id': 'basic',
                'nome': 'Basic',
                'emoji': '🌱',
                'preco': 'R$ 9,99',
                'periodo': 'por mês',
                'descricao': 'Ideal para começar e ter presença online',
                'beneficios': [
                    'Perfil básico permanente',
                    'Listagem nos resultados de busca',
                    'Até 3 especialidades cadastradas',
                    'Até 5 fotos no perfil',
                    'Receber e responder avaliações',
                    'Formulário de contato',
                    'Suporte por email',
                ],
                'limitacoes': [
                    'Não aparece em destaque',
                    'Estatísticas limitadas',
                    'Sem badge premium',
                    'Sem prioridade nas buscas',
                ],
                'atual': terapeuta.is_basic,
                'destaque': False,
                'cor': 'gray',
            },
            {
                'id': 'premium_a',
                'nome': 'Premium A',
                'emoji': '⭐',
                'preco': 'R$ 49,90',
                'periodo': 'por mês',
                'descricao': 'Para profissionais que querem crescer',
                'beneficios': [
                    '✨ Tudo do plano Basic',
                    '🌟 Destaque moderado nas buscas',
                    '✅ Badge "Verificado Premium"',
                    '∞ Especialidades ilimitadas',
                    '📸 Galeria ilimitada de fotos',
                    '📊 Estatísticas básicas',
                    '🔗 Links para redes sociais',
                    '🏢 Até 3 espaços vinculados',
                    '🎯 Suporte prioritário',
                ],
                'destaque': True,
                'atual': terapeuta.is_premium_a,
                'cor': 'blue',
            },
            {
                'id': 'premium_s',
                'nome': 'Premium S',
                'subtitulo': 'Categoria S',
                'emoji': '💎',
                'preco': 'R$ 99,90',
                'periodo': 'por mês',
                'descricao': 'Elite dos profissionais - Recursos avançados',
                'beneficios': [
                    '✨ Tudo do Premium A',
                    '🥇 PRIORIDADE MÁXIMA nas buscas',
                    '💎 Badge dourado "Categoria S"',
                    '🏠 Aparece na home em destaque rotativo',
                    '📊 Estatísticas avançadas com gráficos',
                    '🏢 Espaços vinculados ilimitados',
                    '📱 Suporte via WhatsApp prioritário',
                    '📅 Sistema de agendamento online (em breve)',
                    '💳 Sistema de pagamento integrado (em breve)',
                    '🏆 Selo "Top Profissional"',
                    '📈 Análise de concorrência',
                ],
                'destaque': True,
                'atual': terapeuta.is_premium_s,
                'cor': 'gold',
                'limitado': True,
                'vagas_restantes': vagas_restantes_s,
                'disponivel': categoria_s_disponivel,
            },
        ]
        
        # ===== BENEFÍCIOS EXCLUSIVOS PREMIUM =====
        context['beneficios_premium_exclusivos'] = [
            {
                'icone': '🌟',
                'titulo': 'Destaque nas Buscas',
                'descricao': 'Seu perfil aparece primeiro nos resultados',
            },
            {
                'icone': '📊',
                'titulo': 'Estatísticas Avançadas',
                'descricao': 'Acompanhe visualizações, contatos e performance',
            },
            {
                'icone': '✅',
                'titulo': 'Badge Verificado',
                'descricao': 'Mostre profissionalismo com selo premium',
            },
            {
                'icone': '🎯',
                'titulo': 'Suporte Prioritário',
                'descricao': 'Atendimento rápido e personalizado',
            },
        ]
        
        return context