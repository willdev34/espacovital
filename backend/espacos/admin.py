# ===============================================================
# Título: Admin do App Espacos - Espaço Vital
# Descrição: Interface administrativa para gerenciar espaços terapêuticos e comodidades
# Autor: Will | Empresa: Espaço Vital
# Data: 14/09/2025
# ===============================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg
from django.contrib.admin import SimpleListFilter
from .models import (
    Estado, Cidade, Comodidade, Especialidade, Espaco,
    EspacoEspecialidade, AvaliacaoEspaco, ContatoEspaco
)


# ===============================================================
# FILTROS PERSONALIZADOS
# ===============================================================

class VerificadoEspacoFilter(SimpleListFilter):
    """
    Filtro personalizado para status de verificação de espaços
    """
    title = 'Status de Verificação'
    parameter_name = 'verificacao_status'
    
    def lookups(self, request, model_admin):
        return [
            ('verificado', 'Verificados'),
            ('nao_verificado', 'Não Verificados'),
            ('pendente', 'Pendente Verificação'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'verificado':
            return queryset.filter(is_verificado=True)
        elif self.value() == 'nao_verificado':
            return queryset.filter(is_verificado=False, data_verificacao__isnull=True)
        elif self.value() == 'pendente':
            return queryset.filter(is_verificado=False, data_verificacao__isnull=False)
        return queryset


class AvaliacaoEspacoFilter(SimpleListFilter):
    """
    Filtro por média de avaliações dos espaços
    """
    title = 'Média de Avaliações'
    parameter_name = 'media_avaliacoes'
    
    def lookups(self, request, model_admin):
        return [
            ('5', '5 estrelas'),
            ('4+', '4+ estrelas'),
            ('3+', '3+ estrelas'),
            ('sem_avaliacao', 'Sem avaliações'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == '5':
            return queryset.filter(avaliacoes__nota=5)
        elif self.value() == '4+':
            return queryset.filter(avaliacoes__nota__gte=4)
        elif self.value() == '3+':
            return queryset.filter(avaliacoes__nota__gte=3)
        elif self.value() == 'sem_avaliacao':
            return queryset.filter(avaliacoes__isnull=True)
        return queryset


class TipoEspacoFilter(SimpleListFilter):
    """
    Filtro por tipo de espaço
    """
    title = 'Tipo de Espaço'
    parameter_name = 'tipo_espaco'
    
    def lookups(self, request, model_admin):
        return [
            ('clinica', 'Clínica'),
            ('centro_holistico', 'Centro Holístico'),
            ('estudio', 'Estúdio'),
            ('spa', 'Spa'),
            ('consultorio', 'Consultório'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tipo_espaco=self.value())
        return queryset


# ===============================================================
# INLINES PARA RELACIONAMENTOS
# ===============================================================

class EspacoEspecialidadeInline(admin.TabularInline):
    """
    Inline para especialidades do espaço
    """
    model = EspacoEspecialidade
    extra = 1
    min_num = 1
    max_num = 10
    fields = ['especialidade', 'preco_sessao', 'duracao_sessao', 'is_destaque', 'observacoes']
    verbose_name = 'Especialidade'
    verbose_name_plural = 'Especialidades Oferecidas'


class AvaliacaoEspacoInline(admin.TabularInline):
    """
    Inline para avaliações do espaço
    """
    model = AvaliacaoEspaco
    extra = 0
    max_num = 5
    fields = ['usuario', 'nota', 'comentario', 'is_active']
    readonly_fields = ['created_at']
    verbose_name = 'Avaliação'
    verbose_name_plural = 'Últimas Avaliações'
    
    def get_queryset(self, request):
        """
        Mostra apenas as 5 avaliações mais recentes
        """
        return super().get_queryset(request).order_by('-created_at')[:5]


# ===============================================================
# ADMINS PARA MODELS AUXILIARES
# ===============================================================

@admin.register(Estado)
class EstadoEspacoAdmin(admin.ModelAdmin):
    """
    Admin para Estados (espaços)
    """
    list_display = ['nome', 'sigla', 'total_espacos', 'total_cidades']
    search_fields = ['nome', 'sigla']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    def total_espacos(self, obj):
        """
        Total de espaços no estado
        """
        return obj.cidades_espacos.aggregate(
            total=Count('espacos')
        )['total'] or 0
    total_espacos.short_description = 'Espaços'
    
    def total_cidades(self, obj):
        """
        Total de cidades no estado
        """
        return obj.cidades_espacos.count()
    total_cidades.short_description = 'Cidades'


@admin.register(Cidade)
class CidadeEspacoAdmin(admin.ModelAdmin):
    """
    Admin para Cidades (espaços)
    """
    list_display = ['nome', 'estado', 'total_espacos']
    list_filter = ['estado']
    search_fields = ['nome', 'estado__nome']
    ordering = ['estado__nome', 'nome']
    
    def total_espacos(self, obj):
        return obj.espacos.filter(is_active=True).count()
    total_espacos.short_description = 'Espaços'


@admin.register(Comodidade)
class ComodidadeAdmin(admin.ModelAdmin):
    """
    Admin para Comodidades
    """
    list_display = [
        'nome', 'icone_display', 'destaque_display', 
        'total_espacos', 'is_destaque', 'is_active'
    ]
    list_filter = ['is_destaque', 'is_active']
    search_fields = ['nome', 'descricao']
    list_editable = ['is_destaque', 'is_active']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao')
        }),
        ('Personalização', {
            'fields': ('icone', 'is_destaque')
        }),
        ('Sistema', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def icone_display(self, obj):
        """
        Exibe o ícone da comodidade
        """
        if obj.icone:
            return format_html(
                '<span style="font-size: 16px;" title="{}">{}</span>',
                obj.nome, obj.icone
            )
        return format_html(
            '<span style="color: gray;">-</span>'
        )
    icone_display.short_description = 'Ícone'
    
    def destaque_display(self, obj):
        """
        Exibe status de destaque com ícone
        """
        if obj.is_destaque:
            return format_html(
                '<span style="color: gold;">⭐ Destaque</span>'
            )
        return format_html(
            '<span style="color: gray;">-</span>'
        )
    destaque_display.short_description = 'Status'
    
    def total_espacos(self, obj):
        """
        Total de espaços com esta comodidade
        """
        return obj.espacos.filter(is_active=True).count()
    total_espacos.short_description = 'Espaços'


@admin.register(Especialidade)
class EspecialidadeEspacoAdmin(admin.ModelAdmin):
    """
    Admin para Especialidades (espaços)
    """
    list_display = [
        'nome', 'categoria_display', 'total_espacos', 'is_active'
    ]
    list_filter = ['categoria', 'is_active']
    search_fields = ['nome', 'descricao', 'categoria']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao')
        }),
        ('Categorização', {
            'fields': ('categoria',)
        }),
        ('Sistema', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def categoria_display(self, obj):
        """
        Exibe categoria com cor
        """
        cores_categoria = {
            'Massagem': '#10b981',    # verde
            'Energética': '#8b5cf6',  # roxo
            'Mental': '#3b82f6',      # azul
            'Corporal': '#f59e0b',    # amarelo
        }
        cor = cores_categoria.get(obj.categoria, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            cor, obj.categoria or 'Sem categoria'
        )
    categoria_display.short_description = 'Categoria'
    
    def total_espacos(self, obj):
        """
        Total de espaços com esta especialidade
        """
        return obj.espacos.filter(is_active=True).count()
    total_espacos.short_description = 'Espaços'


# ===============================================================
# ADMIN PRINCIPAL - ESPACOS
# ===============================================================

@admin.register(Espaco)
class EspacoAdmin(admin.ModelAdmin):
    """
    Admin principal para Espaços Terapêuticos
    """
    list_display = [
        'nome_display', 'cidade', 'tipo_espaco_display', 'status_display', 
        'rating_display', 'total_avaliacoes', 'comodidades_count', 'created_at'
    ]
    list_filter = [
        VerificadoEspacoFilter, AvaliacaoEspacoFilter, TipoEspacoFilter,
        'is_destaque', 'is_premium', 'aceita_locacao', 'tem_acessibilidade',
        'is_active', 'cidade__estado'
    ]
    search_fields = [
        'nome', 'descricao_breve', 'email', 'telefone',
        'especialidades__nome', 'cidade__nome', 'bairro'
    ]
    readonly_fields = [
        'slug', 'media_avaliacoes', 'total_avaliacoes', 'created_at', 'updated_at'
    ]
    
    # Inlines
    inlines = [EspacoEspecialidadeInline, AvaliacaoEspacoInline]
    
    # Configurações da lista
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Ações personalizadas
    actions = ['verificar_espacos', 'remover_verificacao', 'marcar_destaque', 'marcar_premium']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': (
                'nome', 'slug', 'responsavel'
            )
        }),
        ('Descrições', {
            'fields': (
                'descricao_breve', 'descricao_completa'
            )
        }),
        ('Localização', {
            'fields': (
                'cidade', 'bairro', 'endereco', 'cep'
            )
        }),
        ('Características', {
            'fields': (
                'tipo_espaco', 'aceita_locacao', 'tem_acessibilidade', 'disponibilidade'
            )
        }),
        ('Comodidades e Especialidades', {
            'fields': (
                'comodidades', 'especialidades'
            )
        }),
        ('Contato', {
            'fields': (
                'telefone', 'email', 'whatsapp', 'website', 'instagram'
            )
        }),
        ('Mídia', {
            'fields': (
                'foto_principal', 'foto_galeria'
            )
        }),
        ('Status e Verificação', {
            'fields': (
                'is_verificado', 'data_verificacao', 'is_destaque', 'is_premium'
            )
        }),
        ('Sistema', {
            'fields': (
                'is_active', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    ]
    
    # Configurações de campos Many-to-Many
    filter_horizontal = ['comodidades', 'especialidades']
    
    def nome_display(self, obj):
        """
        Nome do espaço com link para página
        """
        return format_html(
            '<strong><a href="{}" target="_blank" title="Ver página do espaço">{}</a></strong>',
            obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else '#',
            obj.nome
        )
    nome_display.short_description = 'Espaço'
    
    def tipo_espaco_display(self, obj):
        """
        Tipo de espaço com cores
        """
        cores_tipo = {
            'clinica': '#10b981',           # verde
            'centro_holistico': '#8b5cf6',  # roxo
            'estudio': '#f59e0b',           # amarelo
            'spa': '#06b6d4',               # cyan
            'consultorio': '#3b82f6',       # azul
            'espaco_compartilhado': '#ef4444', # vermelho
            'outros': '#6b7280',            # cinza
        }
        cor = cores_tipo.get(obj.tipo_espaco, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            cor, obj.get_tipo_espaco_display()
        )
    tipo_espaco_display.short_description = 'Tipo'
    
    def status_display(self, obj):
        """
        Exibe status do espaço com cores e ícones
        """
        status = []
        
        if obj.is_verificado:
            status.append('<span style="color: green; font-weight: bold;">✓ Verificado</span>')
        else:
            status.append('<span style="color: red;">✗ Não Verificado</span>')
        
        if obj.is_premium:
            status.append('<span style="color: gold;">👑 Premium</span>')
        
        if obj.is_destaque:
            status.append('<span style="color: purple;">⭐ Destaque</span>')
        
        if obj.aceita_locacao:
            status.append('<span style="color: blue;">🏢 Locação</span>')
        
        if obj.tem_acessibilidade:
            status.append('<span style="color: green;">♿ Acessível</span>')
        
        return format_html(' | '.join(status))
    status_display.short_description = 'Status'
    
    def rating_display(self, obj):
        """
        Exibe rating com estrelas
        """
        rating = obj.media_avaliacoes
        if rating and rating > 0:
            stars = '⭐' * int(rating)
            return format_html(
                '<span title="{:.1f} estrelas">{} ({:.1f})</span>',
                rating, stars, rating
            )
        return format_html('<span style="color: gray;">Sem avaliações</span>')
    rating_display.short_description = 'Avaliação'
    
    def comodidades_count(self, obj):
        """
        Total de comodidades
        """
        count = obj.comodidades.count()
        destaque_count = obj.comodidades.filter(is_destaque=True).count()
        
        if destaque_count > 0:
            return format_html(
                '<span title="{} comodidades, {} em destaque">{} <small>({} ⭐)</small></span>',
                count, destaque_count, count, destaque_count
            )
        return count
    comodidades_count.short_description = 'Comodidades'
    
    # Ações personalizadas
    def verificar_espacos(self, request, queryset):
        """
        Ação para verificar espaços selecionados
        """
        updated = queryset.update(
            is_verificado=True,
            data_verificacao=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} espaço(s) verificado(s) com sucesso.'
        )
    verificar_espacos.short_description = 'Verificar espaços selecionados'
    
    def remover_verificacao(self, request, queryset):
        """
        Ação para remover verificação
        """
        updated = queryset.update(
            is_verificado=False,
            data_verificacao=None
        )
        self.message_user(
            request,
            f'Verificação removida de {updated} espaço(s).'
        )
    remover_verificacao.short_description = 'Remover verificação'
    
    def marcar_destaque(self, request, queryset):
        """
        Ação para marcar como destaque
        """
        updated = queryset.update(is_destaque=True)
        self.message_user(
            request,
            f'{updated} espaço(s) marcado(s) como destaque.'
        )
    marcar_destaque.short_description = 'Marcar como destaque'
    
    def marcar_premium(self, request, queryset):
        """
        Ação para marcar como premium
        """
        updated = queryset.update(is_premium=True)
        self.message_user(
            request,
            f'{updated} espaço(s) marcado(s) como premium.'
        )
    marcar_premium.short_description = 'Marcar como premium'


# ===============================================================
# ADMINS PARA AVALIAÇÕES E CONTATOS
# ===============================================================

@admin.register(AvaliacaoEspaco)
class AvaliacaoEspacoAdmin(admin.ModelAdmin):
    """
    Admin para Avaliações de Espaços
    """
    list_display = [
        'espaco', 'usuario', 'nota_display', 'comentario_truncado', 
        'is_active', 'created_at'
    ]
    list_filter = ['nota', 'is_active', 'created_at']
    search_fields = ['espaco__nome', 'usuario__username', 'comentario']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def nota_display(self, obj):
        """
        Exibe nota com estrelas
        """
        stars = '⭐' * obj.nota
        return format_html(
            '<span title="{} estrelas">{}</span>',
            obj.nota, stars
        )
    nota_display.short_description = 'Nota'
    
    def comentario_truncado(self, obj):
        """
        Comentário truncado
        """
        if len(obj.comentario) > 50:
            return f'{obj.comentario[:50]}...'
        return obj.comentario
    comentario_truncado.short_description = 'Comentário'


@admin.register(ContatoEspaco)
class ContatoEspacoAdmin(admin.ModelAdmin):
    """
    Admin para Contatos de Espaços
    """
    list_display = [
        'espaco', 'nome', 'email', 'assunto_truncado', 
        'status_display', 'created_at'
    ]
    list_filter = ['is_respondido', 'created_at']
    search_fields = ['espaco__nome', 'nome', 'email', 'assunto']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('Informações do Contato', {
            'fields': ('espaco', 'nome', 'email', 'telefone')
        }),
        ('Mensagem', {
            'fields': ('assunto', 'mensagem')
        }),
        ('Status', {
            'fields': ('is_respondido',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def assunto_truncado(self, obj):
        """
        Assunto truncado
        """
        if len(obj.assunto) > 50:
            return f'{obj.assunto[:50]}...'
        return obj.assunto
    assunto_truncado.short_description = 'Assunto'
    
    def status_display(self, obj):
        """
        Status com cores
        """
        if obj.is_respondido:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">Respondido</span>'
            )
        return format_html(
            '<span style="background-color: #f59e0b; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">Pendente</span>'
        )
    status_display.short_description = 'Status'


# ===============================================================
# CONFIGURAÇÕES EXTRAS DO ADMIN
# ===============================================================

# Personalizar título do admin para espaços
admin.site.site_header = "Espaço Vital - Administração"
admin.site.site_title = "Espaço Vital Admin"
admin.site.index_title = "Painel de Controle - Espaços Terapêuticos"