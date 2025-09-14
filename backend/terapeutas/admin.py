# ===============================================================
# Título: Admin do App Terapeutas - Espaço Vital
# Descrição: Interface administrativa para gerenciar terapeutas e especialidades
# Autor: Will | Empresa: Espaço VItal
# Data: 13/09/2025
# ===============================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg
from django.contrib.admin import SimpleListFilter
from .models import (
    Estado, Cidade, Especialidade, Terapeuta, 
    TerapeutaEspecialidade, Avaliacao, Contato
)


# ===============================================================
# FILTROS PERSONALIZADOS
# ===============================================================

class VerificadoFilter(SimpleListFilter):
    """
    Filtro personalizado para status de verificação
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
            return queryset.filter(verificado=True)
        elif self.value() == 'nao_verificado':
            return queryset.filter(verificado=False, data_verificacao__isnull=True)
        elif self.value() == 'pendente':
            return queryset.filter(verificado=False, data_verificacao__isnull=False)
        return queryset


class AvaliacaoFilter(SimpleListFilter):
    """
    Filtro por média de avaliações
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
            return queryset.annotate(
                media=Avg('avaliacoes__nota')
            ).filter(media=5.0)
        elif self.value() == '4+':
            return queryset.annotate(
                media=Avg('avaliacoes__nota')
            ).filter(media__gte=4.0)
        elif self.value() == '3+':
            return queryset.annotate(
                media=Avg('avaliacoes__nota')
            ).filter(media__gte=3.0)
        elif self.value() == 'sem_avaliacao':
            return queryset.annotate(
                total_avaliacoes=Count('avaliacoes')
            ).filter(total_avaliacoes=0)
        return queryset


# ===============================================================
# INLINE ADMINS
# ===============================================================

class TerapeutaEspecialidadeInline(admin.TabularInline):
    """
    Inline para especialidades do terapeuta
    """
    model = TerapeutaEspecialidade
    extra = 1
    fields = [
        'especialidade', 'principal', 'preco_sessao', 
        'duracao_sessao', 'anos_experiencia', 'certificacao'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('especialidade')


class AvaliacaoInline(admin.TabularInline):
    """
    Inline para avaliações do terapeuta
    """
    model = Avaliacao
    extra = 0
    readonly_fields = ['created_at', 'cliente', 'nota', 'comentario']
    fields = ['created_at', 'cliente', 'nota', 'recomenda', 'verificada']
    
    def has_add_permission(self, request, obj=None):
        return False


# ===============================================================
# ADMINS DOS MODELOS
# ===============================================================

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    """
    Admin para Estados
    """
    list_display = ['nome', 'sigla', 'total_cidades']
    search_fields = ['nome', 'sigla']
    ordering = ['nome']
    
    def total_cidades(self, obj):
        return obj.cidades.count()
    total_cidades.short_description = 'Cidades'


@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    """
    Admin para Cidades
    """
    list_display = ['nome', 'estado', 'total_terapeutas']
    list_filter = ['estado']
    search_fields = ['nome', 'estado__nome']
    ordering = ['estado__nome', 'nome']
    
    def total_terapeutas(self, obj):
        return obj.terapeuta_set.filter(is_active=True).count()
    total_terapeutas.short_description = 'Terapeutas'


@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    """
    Admin para Especialidades
    """
    list_display = [
        'nome', 'cor_destaque_display', 'destaque_display', 
        'total_terapeutas', 'ordem', 'is_active'
    ]
    list_filter = ['destaque', 'is_active']
    search_fields = ['nome', 'descricao_curta']
    list_editable = ['ordem', 'is_active']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao_curta', 'descricao_completa')
        }),
        ('Personalização', {
            'fields': ('icone', 'cor_destaque', 'ordem')
        }),
        ('Configurações', {
            'fields': ('destaque', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def cor_destaque_display(self, obj):
        """
        Exibe a cor como um quadrado colorido
        """
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; '
            'border: 1px solid #ddd; border-radius: 3px;"></div>',
            obj.cor_destaque
        )
    cor_destaque_display.short_description = 'Cor'
    
    def destaque_display(self, obj):
        """
        Exibe status de destaque com ícone
        """
        if obj.destaque:
            return format_html(
                '<span style="color: gold;">⭐ Destaque</span>'
            )
        return format_html(
            '<span style="color: gray;">-</span>'
        )
    destaque_display.short_description = 'Status'
    
    def total_terapeutas(self, obj):
        """
        Total de terapeutas com esta especialidade
        """
        return obj.terapeuta_set.filter(is_active=True).count()
    total_terapeutas.short_description = 'Terapeutas'


@admin.register(Terapeuta)
class TerapeutaAdmin(admin.ModelAdmin):
    """
    Admin principal para Terapeutas
    """
    list_display = [
        'nome_exibicao', 'cidade', 'status_display', 'rating_display',
        'total_avaliacoes', 'visualizacoes', 'created_at'
    ]
    list_filter = [
        VerificadoFilter, AvaliacaoFilter, 'destaque', 'premium',
        'is_active', 'cidade__estado', 'tipos_sessao'
    ]
    search_fields = [
        'nome_completo', 'nome_exibicao', 'email_profissional',
        'especialidades__nome', 'cidade__nome'
    ]
    readonly_fields = [
    'slug', 'visualizacoes', 'total_contatos', 
    'rating_medio', 'total_avaliacoes', 'created_at', 'updated_at'
    ]
    
    # Inlines
    inlines = [TerapeutaEspecialidadeInline, AvaliacaoInline]
    
    # Configurações da lista
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Ações personalizadas
    actions = ['verificar_terapeutas', 'remover_verificacao', 'marcar_destaque']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': (
                'user', 'nome_completo', 'nome_exibicao', 'slug'
            )
        }),
        ('Contato', {
            'fields': (
                'email_profissional', 'telefone', 'whatsapp'
            )
        }),
        ('Localização', {
            'fields': (
                'cidade', 'bairro', 'endereco'
            )
        }),
        ('Informações Profissionais', {
            'fields': (
                'registro_profissional', 'formacao', 'experiencia_anos'
            )
        }),
        ('Configurações de Atendimento', {
            'fields': (
                'tipos_sessao', 'tipo_perfil', 'para_quem', 'acessibilidade'
            )
        }),
        ('Descrições', {
            'fields': (
                'bio_curta', 'bio_completa', 'metodologia'
            )
        }),
        ('Mídia', {
            'fields': (
                'foto_perfil', 'foto_capa'
            )
        }),
        ('Status e Verificação', {
            'fields': (
                'verificado', 'data_verificacao', 'destaque', 'premium'
            )
        }),
        ('Métricas', {
            'fields': (
                'visualizacoes', 'total_contatos', 'rating_medio', 'total_avaliacoes'
            ),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': (
                'is_active', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    ]
    
    def status_display(self, obj):
        """
        Exibe status do terapeuta com cores
        """
        status = []
        
        if obj.verificado:
            status.append('<span style="color: green; font-weight: bold;">✓ Verificado</span>')
        else:
            status.append('<span style="color: red;">✗ Não Verificado</span>')
        
        if obj.premium:
            status.append('<span style="color: gold;">👑 Premium</span>')
        
        if obj.destaque:
            status.append('<span style="color: purple;">⭐ Destaque</span>')
        
        return format_html(' | '.join(status))
    status_display.short_description = 'Status'
    
    def rating_display(self, obj):
        """
        Exibe rating com estrelas
        """
        rating = obj.rating_medio
        if rating > 0:
            stars = '⭐' * int(rating)
            return format_html(
                '<span title="{} estrelas">{} ({})</span>',
                rating, stars, rating
            )
        return format_html('<span style="color: gray;">Sem avaliações</span>')
    rating_display.short_description = 'Avaliação'
    
    def verificar_terapeutas(self, request, queryset):
        """
        Ação para verificar terapeutas selecionados
        """
        updated = queryset.update(
            verificado=True,
            data_verificacao=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} terapeuta(s) verificado(s) com sucesso.'
        )
    verificar_terapeutas.short_description = 'Verificar terapeutas selecionados'
    
    def remover_verificacao(self, request, queryset):
        """
        Ação para remover verificação
        """
        updated = queryset.update(
            verificado=False,
            data_verificacao=None
        )
        self.message_user(
            request,
            f'Verificação removida de {updated} terapeuta(s).'
        )
    remover_verificacao.short_description = 'Remover verificação'
    
    def marcar_destaque(self, request, queryset):
        """
        Ação para marcar como destaque
        """
        updated = queryset.update(destaque=True)
        self.message_user(
            request,
            f'{updated} terapeuta(s) marcado(s) como destaque.'
        )
    marcar_destaque.short_description = 'Marcar como destaque'


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    """
    Admin para Avaliações
    """
    list_display = [
        'terapeuta', 'cliente_nome', 'nota_display', 
        'recomenda', 'verificada', 'created_at'
    ]
    list_filter = [
        'nota', 'recomenda', 'verificada', 'created_at'
    ]
    search_fields = [
        'terapeuta__nome_exibicao', 'cliente__username',
        'cliente__first_name', 'cliente__last_name', 'comentario'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Avaliação', {
            'fields': ('terapeuta', 'cliente', 'nota', 'comentario')
        }),
        ('Detalhes', {
            'fields': ('data_sessao', 'recomenda', 'verificada')
        }),
        ('Sistema', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def cliente_nome(self, obj):
        """
        Nome do cliente
        """
        return obj.cliente.get_full_name() or obj.cliente.username
    cliente_nome.short_description = 'Cliente'
    
    def nota_display(self, obj):
        """
        Nota com estrelas
        """
        stars = '⭐' * obj.nota
        return format_html(
            '<span title="{} estrelas">{} ({})</span>',
            obj.nota, stars, obj.nota
        )
    nota_display.short_description = 'Nota'


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    """
    Admin para Contatos
    """
    list_display = [
        'nome', 'terapeuta', 'assunto_truncado', 
        'status_display', 'especialidade_interesse', 'created_at'
    ]
    list_filter = [
        'status', 'especialidade_interesse', 'created_at'
    ]
    search_fields = [
        'nome', 'email', 'terapeuta__nome_exibicao', 
        'assunto', 'mensagem'
    ]
    readonly_fields = ['created_at', 'updated_at', 'ip_origem']
    
    fieldsets = [
        ('Informações do Contato', {
            'fields': ('nome', 'email', 'telefone')
        }),
        ('Destinatário', {
            'fields': ('terapeuta', 'especialidade_interesse')
        }),
        ('Mensagem', {
            'fields': ('assunto', 'mensagem', 'status')
        }),
        ('Informações Técnicas', {
            'fields': ('ip_origem', 'created_at', 'updated_at'),
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
        colors = {
            'enviado': '#fbbf24',      # amarelo
            'lido': '#3b82f6',         # azul
            'respondido': '#10b981',   # verde
            'arquivado': '#6b7280',    # cinza
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'


# ===============================================================
# CONFIGURAÇÕES EXTRAS DO ADMIN
# ===============================================================

# Personalizar título do admin
admin.site.site_header = "Espaço Vital - Administração"
admin.site.site_title = "Espaço Vital Admin"
admin.site.index_title = "Painel de Controle - Terapeutas"