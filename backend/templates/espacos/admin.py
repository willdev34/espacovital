# ===============================================================
# Título: Admin do App Espaços - Espaço Vital
# Descrição: Configuração do painel administrativo para espaços
# Autor: Will
# Data: 04/10/2025
# ===============================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import (
    Espaco, TipoEspaco, Comodidade, Especialidade, 
    Estado, Cidade, AvaliacaoEspaco, ContatoEspaco,
    DisponibilidadePeriodo, GaleriaEspaco, EspecialidadeDetalhada
)


# ===============================================================
# INLINE ADMINS
# ===============================================================

class GaleriaEspacoInline(admin.TabularInline):
    """
    Inline para adicionar múltiplas fotos ao espaço
    """
    model = GaleriaEspaco
    extra = 1
    fields = ['imagem', 'descricao', 'ordem', 'is_active']
    ordering = ['ordem']


class EspecialidadeDetalhadaInline(admin.TabularInline):
    """
    Inline para vincular especialidades com detalhes específicos
    """
    model = EspecialidadeDetalhada
    extra = 1
    fields = ['especialidade', 'descricao_no_espaco', 'preco_medio', 'duracao_media', 'is_destaque']
    autocomplete_fields = ['especialidade']


class AvaliacaoEspacoInline(admin.TabularInline):
    """
    Inline para visualizar avaliações do espaço
    """
    model = AvaliacaoEspaco
    extra = 0
    readonly_fields = ['nome', 'email', 'nota', 'comentario', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# ===============================================================
# ADMIN PRINCIPAL - ESPAÇO
# ===============================================================

@admin.register(Espaco)
class EspacoAdmin(admin.ModelAdmin):
    """
    Admin completo para gerenciamento de espaços terapêuticos
    """
    
    # Configuração da listagem
    list_display = [
        'foto_miniatura', 'nome', 'tipo_espaco_badge', 'cidade_estado',
        'tem_acessibilidade_icon', 'aceita_locacao_icon', 'is_verificado_icon',
        'media_avaliacoes_display', 'is_destaque', 'is_active'
    ]
    list_filter = [
        'is_active', 'is_verificado', 'is_destaque',
        'tipo_espaco', 'tem_acessibilidade', 'aceita_locacao',
        'cidade__estado', 'cidade', 'created_at'
    ]
    search_fields = ['nome', 'descricao_breve', 'endereco', 'bairro']
    list_editable = ['is_destaque', 'is_active']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    # Configuração do formulário
    fieldsets = (
        ('📍 Informações Básicas', {
            'fields': (
                'nome', 'slug', 'tipo_espaco',
                'descricao_breve', 'descricao_completa',
                'foto_principal'
            )
        }),
        ('🏢 Localização', {
            'fields': (
                'cep', 'endereco', 'numero', 'complemento',
                'bairro', 'cidade', 'referencia'
            )
        }),
        ('📞 Contatos', {
            'fields': (
                'telefone', 'telefone2', 'whatsapp',
                'email', 'website', 'instagram', 'facebook'
            )
        }),
        ('⚙️ Características', {
            'fields': (
                'tem_acessibilidade', 'aceita_locacao',
                'capacidade_maxima', 'area_m2',
                'comodidades', 'especialidades'
            )
        }),
        ('💰 Valores e Disponibilidade', {
            'fields': (
                'valor_hora', 'valor_diaria', 'valor_mensal',
                'disponibilidade_periodos',
                'horario_funcionamento'
            ),
            'classes': ('collapse',)
        }),
        ('🎯 Configurações do Sistema', {
            'fields': (
                'proprietario', 'is_active', 'is_verificado', 'is_destaque',
                'pontuacao_destaque', 'views_count'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Campos somente leitura
    readonly_fields = ['slug', 'views_count', 'created_at', 'updated_at']
    
    # Configuração de autocomplete
    autocomplete_fields = ['cidade', 'proprietario']
    
    # Configuração de filtros horizontais
    filter_horizontal = ['comodidades', 'especialidades', 'disponibilidade_periodos']
    
    # Inlines
    inlines = [GaleriaEspacoInline, EspecialidadeDetalhadaInline, AvaliacaoEspacoInline]
    
    # Ações personalizadas
    actions = ['ativar_espacos', 'desativar_espacos', 'verificar_espacos', 'destacar_espacos']
    
    # ===============================================================
    # MÉTODOS DE EXIBIÇÃO PERSONALIZADOS
    # ===============================================================
    
    def foto_miniatura(self, obj):
        """Exibe miniatura da foto principal"""
        if obj.foto_principal:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius: 8px; object-fit: cover;"/>',
                obj.foto_principal.url
            )
        return format_html(
            '<div style="width:60px;height:60px;background:#f0f0f0;border-radius:8px;'
            'display:flex;align-items:center;justify-content:center;">'
            '<span style="color:#999;">Sem foto</span></div>'
        )
    foto_miniatura.short_description = 'Foto'
    
    def tipo_espaco_badge(self, obj):
        """Exibe o tipo de espaço com badge colorido"""
        colors = {
            'consultorio': '#3B82F6',
            'clinica': '#10B981',
            'studio': '#8B5CF6',
            'espaco_holistico': '#F59E0B',
            'spa': '#EC4899',
            'centro_terapeutico': '#06B6D4'
        }
        color = colors.get(obj.tipo_espaco, '#6B7280')
        return format_html(
            '<span style="background:{}; color:white; padding:4px 12px; '
            'border-radius:12px; font-size:11px; font-weight:500;">{}</span>',
            color, obj.get_tipo_espaco_display()
        )
    tipo_espaco_badge.short_description = 'Tipo'
    
    def cidade_estado(self, obj):
        """Exibe cidade e estado formatados"""
        return f"{obj.cidade.nome}/{obj.cidade.estado.sigla}"
    cidade_estado.short_description = 'Localização'
    cidade_estado.admin_order_field = 'cidade'
    
    def tem_acessibilidade_icon(self, obj):
        """Ícone para acessibilidade"""
        if obj.tem_acessibilidade:
            return format_html(
                '<span style="color:#10B981;" title="Acessível">✓</span>'
            )
        return format_html(
            '<span style="color:#EF4444;" title="Não acessível">✗</span>'
        )
    tem_acessibilidade_icon.short_description = 'Acessível'
    
    def aceita_locacao_icon(self, obj):
        """Ícone para locação"""
        if obj.aceita_locacao:
            return format_html(
                '<span style="color:#10B981;" title="Aceita locação">✓</span>'
            )
        return format_html(
            '<span style="color:#EF4444;" title="Não aceita locação">✗</span>'
        )
    aceita_locacao_icon.short_description = 'Locação'
    
    def is_verificado_icon(self, obj):
        """Ícone de verificação"""
        if obj.is_verificado:
            return format_html(
                '<span style="color:#10B981;font-size:16px;" title="Verificado">✓</span>'
            )
        return format_html(
            '<span style="color:#FCD34D;" title="Pendente">⚠</span>'
        )
    is_verificado_icon.short_description = 'Verificado'
    
    def media_avaliacoes_display(self, obj):
        """Exibe média de avaliações com estrelas"""
        media = obj.media_avaliacoes or 0
        total = obj.total_avaliacoes or 0
        
        if total == 0:
            return format_html('<span style="color:#999;">Sem avaliações</span>')
        
        stars = '⭐' * int(media)
        return format_html(
            '<span title="{} avaliações">{} {:.1f}</span>',
            total, stars, media
        )
    media_avaliacoes_display.short_description = 'Avaliações'
    
    # ===============================================================
    # AÇÕES PERSONALIZADAS
    # ===============================================================
    
    def ativar_espacos(self, request, queryset):
        """Ativa espaços selecionados"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} espaço(s) ativado(s) com sucesso!')
    ativar_espacos.short_description = '✅ Ativar espaços selecionados'
    
    def desativar_espacos(self, request, queryset):
        """Desativa espaços selecionados"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} espaço(s) desativado(s) com sucesso!')
    desativar_espacos.short_description = '❌ Desativar espaços selecionados'
    
    def verificar_espacos(self, request, queryset):
        """Marca espaços como verificados"""
        count = queryset.update(is_verificado=True)
        self.message_user(request, f'{count} espaço(s) verificado(s) com sucesso!')
    verificar_espacos.short_description = '✓ Verificar espaços selecionados'
    
    def destacar_espacos(self, request, queryset):
        """Marca espaços como destaque"""
        count = queryset.update(is_destaque=True)
        self.message_user(request, f'{count} espaço(s) marcado(s) como destaque!')
    destacar_espacos.short_description = '⭐ Destacar espaços selecionados'
    
    # ===============================================================
    # OTIMIZAÇÃO DE QUERIES
    # ===============================================================
    
    def get_queryset(self, request):
        """Otimiza queries com select_related e prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'cidade', 'cidade__estado', 'proprietario'
        ).prefetch_related(
            'comodidades', 'especialidades', 'avaliacoes'
        ).annotate(
            media_avaliacoes=Avg('avaliacoes__nota'),
            total_avaliacoes=Count('avaliacoes')
        )


# ===============================================================
# ADMIN PARA MODELOS AUXILIARES
# ===============================================================

@admin.register(TipoEspaco)
class TipoEspacoAdmin(admin.ModelAdmin):
    """Admin para tipos de espaço"""
    list_display = ['nome', 'slug', 'ordem', 'is_active']
    list_editable = ['ordem', 'is_active']
    prepopulated_fields = {'slug': ('nome',)}
    ordering = ['ordem', 'nome']


@admin.register(Comodidade)
class ComodidadeAdmin(admin.ModelAdmin):
    """Admin para comodidades"""
    list_display = ['nome', 'categoria', 'icone', 'is_destaque', 'is_active']
    list_filter = ['categoria', 'is_destaque', 'is_active']
    list_editable = ['is_destaque', 'is_active']
    search_fields = ['nome', 'descricao']
    ordering = ['-is_destaque', 'categoria', 'nome']
    
    fieldsets = (
        ('Informações', {
            'fields': ('nome', 'slug', 'descricao', 'categoria')
        }),
        ('Visual', {
            'fields': ('icone', 'cor')
        }),
        ('Configurações', {
            'fields': ('is_destaque', 'is_active')
        })
    )
    prepopulated_fields = {'slug': ('nome',)}


@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    """Admin para especialidades/terapias"""
    list_display = ['nome', 'categoria', 'is_destaque', 'is_active']
    list_filter = ['categoria', 'is_destaque', 'is_active']
    list_editable = ['is_destaque', 'is_active']
    search_fields = ['nome', 'descricao']
    prepopulated_fields = {'slug': ('nome',)}
    ordering = ['-is_destaque', 'categoria', 'nome']


@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    """Admin para estados"""
    list_display = ['nome', 'sigla', 'regiao']
    list_filter = ['regiao']
    search_fields = ['nome', 'sigla']
    ordering = ['nome']


@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    """Admin para cidades"""
    list_display = ['nome', 'estado', 'populacao_display', 'is_capital']
    list_filter = ['estado', 'is_capital']
    search_fields = ['nome', 'estado__nome']
    autocomplete_fields = ['estado']
    ordering = ['nome']
    
    def populacao_display(self, obj):
        """Formata população com separador de milhares"""
        if obj.populacao:
            return f"{obj.populacao:,}".replace(',', '.')
        return '-'
    populacao_display.short_description = 'População'


@admin.register(AvaliacaoEspaco)
class AvaliacaoEspacoAdmin(admin.ModelAdmin):
    """Admin para avaliações de espaços"""
    list_display = [
        'espaco', 'nome', 'nota_stars', 'comentario_resumo',
        'is_active', 'created_at'
    ]
    list_filter = ['nota', 'is_active', 'created_at']
    search_fields = ['espaco__nome', 'nome', 'email', 'comentario']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def nota_stars(self, obj):
        """Exibe nota com estrelas"""
        return '⭐' * obj.nota + '☆' * (5 - obj.nota)
    nota_stars.short_description = 'Nota'
    
    def comentario_resumo(self, obj):
        """Exibe resumo do comentário"""
        if obj.comentario:
            return obj.comentario[:50] + ('...' if len(obj.comentario) > 50 else '')
        return '-'
    comentario_resumo.short_description = 'Comentário'
    
    actions = ['aprovar_avaliacoes', 'reprovar_avaliacoes']
    
    def aprovar_avaliacoes(self, request, queryset):
        """Aprova avaliações selecionadas"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} avaliação(ões) aprovada(s)!')
    aprovar_avaliacoes.short_description = '✅ Aprovar avaliações'
    
    def reprovar_avaliacoes(self, request, queryset):
        """Remove avaliações selecionadas"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} avaliação(ões) removida(s)!')
    reprovar_avaliacoes.short_description = '❌ Remover avaliações'


@admin.register(ContatoEspaco)
class ContatoEspacoAdmin(admin.ModelAdmin):
    """Admin para contatos recebidos"""
    list_display = [
        'espaco', 'nome', 'email', 'telefone',
        'assunto', 'is_lido', 'is_respondido', 'created_at'
    ]
    list_filter = ['is_lido', 'is_respondido', 'created_at']
    search_fields = ['espaco__nome', 'nome', 'email', 'assunto', 'mensagem']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Espaço', {
            'fields': ('espaco',)
        }),
        ('Contato', {
            'fields': ('nome', 'email', 'telefone', 'assunto', 'mensagem')
        }),
        ('Status', {
            'fields': ('is_lido', 'is_respondido', 'respondido_em', 'resposta')
        }),
        ('Sistema', {
            'fields': ('created_at',)
        })
    )
    
    actions = ['marcar_como_lido', 'marcar_como_respondido']
    
    def marcar_como_lido(self, request, queryset):
        """Marca contatos como lidos"""
        count = queryset.update(is_lido=True)
        self.message_user(request, f'{count} contato(s) marcado(s) como lido(s)!')
    marcar_como_lido.short_description = '✓ Marcar como lido'
    
    def marcar_como_respondido(self, request, queryset):
        """Marca contatos como respondidos"""
        from django.utils import timezone
        count = queryset.update(is_respondido=True, respondido_em=timezone.now())
        self.message_user(request, f'{count} contato(s) marcado(s) como respondido(s)!')
    marcar_como_respondido.short_description = '✉️ Marcar como respondido'


# ===============================================================
# CONFIGURAÇÃO DO ADMIN SITE
# ===============================================================

admin.site.site_header = "Espaço Vital - Administração"
admin.site.site_title = "Espaço Vital Admin"
admin.site.index_title = "Painel de Controle"