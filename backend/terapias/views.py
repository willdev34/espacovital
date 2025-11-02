# ===============================================================
# Título: Views do App Terapias
# Descrição: Views para listagem e detalhes de terapias/especialidades
# Autor: Will
# Data: Novembro 2025
# ===============================================================

from django.shortcuts import render
from django.views.generic import ListView, DetailView
from core.models import Especialidade
from terapeutas.models import Terapeuta
from espacos.models import Espaco


class TerapiasDestaquesView(ListView):
    """
    View: Terapias em Destaque
    Descrição: Exibe as 10 terapias marcadas como destaque
    Template: terapias/destaques.html
    URL: /terapias/
    """
    model = Especialidade
    template_name = 'terapias/destaques.html'
    context_object_name = 'terapias_destaque'
    
    def get_queryset(self):
        """
        Retorna apenas especialidades marcadas como destaque
        Ordenadas por: destaque, ordem e nome
        Limite: 10 terapias
        """
        return Especialidade.objects.filter(
            destaque=True,
            is_active=True
        ).order_by('-destaque', 'ordem', 'nome')[:10]
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações relacionadas à terapia
        """
        context = super().get_context_data(**kwargs)
        terapia = self.get_object()
        
        # Terapeutas que atendem esta especialidade
        context['terapeutas'] = Terapeuta.objects.filter(
            especialidades=terapia,
            is_active=True
        ).select_related('user').prefetch_related('especialidades')[:6]
        
        # Espaços que oferecem esta terapia
        context['espacos'] = Espaco.objects.filter(
            especialidades=terapia,
            is_active=True
        ).prefetch_related('especialidades', 'comodidades')[:6]
        
        # Contadores
        context['total_terapeutas'] = Terapeuta.objects.filter(
            especialidades=terapia,
            is_active=True
        ).count()
        
        context['total_espacos'] = Espaco.objects.filter(
            especialidades=terapia,
            is_active=True
        ).count()
        
        # ===============================================================
        # NOVO: Cidades que oferecem a terapia
        # ===============================================================
        from django.db.models import Q
        
        # Buscar cidades únicas de terapeutas
        cidades_terapeutas = Terapeuta.objects.filter(
            especialidades=terapia,
            is_active=True
        ).values_list('cidade', flat=True).distinct()
        
        # Buscar cidades únicas de espaços
        cidades_espacos = Espaco.objects.filter(
            especialidades=terapia,
            is_active=True
        ).values_list('cidade', flat=True).distinct()
        
        # Combinar e remover duplicatas
        from core.models import Cidade
        ids_cidades = set(list(cidades_terapeutas) + list(cidades_espacos))
        context['cidades'] = Cidade.objects.filter(id__in=ids_cidades).order_by('nome')
        
        return context


class TerapiasListagemView(ListView):
    """
    View: Listagem Alfabética de Terapias (A-Z)
    Descrição: Exibe todas as terapias ativas ordenadas alfabeticamente
              Com filtro por letra via HTMX
    Template: terapias/listagem_alfabetica.html
    URL: /terapias/todas/
    """
    model = Especialidade
    template_name = 'terapias/listagem_alfabetica.html'
    context_object_name = 'terapias'
    paginate_by = 30  # Paginação de 30 terapias por página
    
    def get_queryset(self):
        """
        Retorna todas as especialidades ativas
        Filtra por letra se parâmetro 'letra' estiver presente
        """
        queryset = Especialidade.objects.filter(is_active=True)
        
        # Filtro por letra (A-Z) via query parameter
        letra = self.request.GET.get('letra', None)
        
        if letra and letra != 'todas':
            queryset = queryset.filter(nome__istartswith=letra)
        
        return queryset.order_by('nome')
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações extras ao contexto
        """
        context = super().get_context_data(**kwargs)
        
        # Letra selecionada (para destacar no menu A-Z)
        context['letra_selecionada'] = self.request.GET.get('letra', 'todas')
        
        # Alfabeto para o filtro
        context['alfabeto'] = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        # Total de resultados
        context['total_resultados'] = self.get_queryset().count()
        
        return context


class TerapiaDetalheView(DetailView):
    """
    View: Página Individual da Terapia
    Descrição: Exibe detalhes completos de uma terapia específica
              Incluindo: terapeutas que atendem e espaços que oferecem
    Template: terapias/detalhe.html
    URL: /terapias/<slug>/
    """
    model = Especialidade
    template_name = 'terapias/detalhe.html'
    context_object_name = 'terapia'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Retorna apenas especialidades ativas
        """
        return Especialidade.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações relacionadas à terapia
        """
        context = super().get_context_data(**kwargs)
        terapia = self.get_object()
        
        # Terapeutas que atendem esta especialidade
        # Filtra terapeutas ativos e com especialidade relacionada
        context['terapeutas'] = Terapeuta.objects.filter(
            especialidades=terapia,
            is_active=True
        ).select_related('user').prefetch_related('especialidades')[:6]
        
        # Espaços que oferecem esta terapia
        # Filtra espaços ativos e com especialidade relacionada
        context['espacos'] = Espaco.objects.filter(
            especialidades=terapia,
            is_active=True
        ).prefetch_related('especialidades', 'comodidades')[:6]
        
        # Contadores
        context['total_terapeutas'] = Terapeuta.objects.filter(
            especialidades=terapia,
            is_active=True
        ).count()
        
        context['total_espacos'] = Espaco.objects.filter(
            especialidades=terapia,
            is_active=True
        ).count()
        
        return context
