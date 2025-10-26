# ===============================================================
# Título: Admin do App Espaços - Espaço Vital
# Descrição: Configuração do painel administrativo para espaços
# Autor: Will
# Data: 12/10/2025
# ===============================================================

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Q
from django.contrib.admin import SimpleListFilter
from django import forms
from core.models import Especialidade, Pais, Estado, Cidade
from .models import (
    Espaco, Comodidade, AvaliacaoEspaco, 
    ContatoEspaco, EspacoEspecialidade, FotoGaleriaEspaco
)


# ===============================================================
# FORMULÁRIO CUSTOMIZADO PARA ESPAÇO
# ===============================================================

# ===============================================================
# FORMULÁRIO CUSTOMIZADO PARA ESPAÇO
# ===============================================================

class EspacoAdminForm(forms.ModelForm):
    """
    Formulário customizado com campos de disponibilidade como checkboxes
    e upload de galeria com até 7 fotos
    """
    # ===== ADICIONAR ESTE CAMPO ESTADO (mesmo que já exista no model) =====
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.none(),
        required=False,
        label='Estado',
        help_text='Selecione o estado (apenas Brasil)'
    )
    
    # Checkboxes para disponibilidade
    disponibilidade_manha = forms.BooleanField(
        required=False,
        label='Manhã',
        help_text='Disponível no período da manhã'
    )
    disponibilidade_tarde = forms.BooleanField(
        required=False,
        label='Tarde',
        help_text='Disponível no período da tarde'
    )
    disponibilidade_noite = forms.BooleanField(
        required=False,
        label='Noite',
        help_text='Disponível no período da noite'
    )
    disponibilidade_finais_semana = forms.BooleanField(
        required=False,
        label='Finais de semana',
        help_text='Disponível aos finais de semana'
    )
    
    class Meta:
        model = Espaco
        fields = '__all__'
        widgets = {
            'foto_galeria': forms.Textarea(attrs={
                'rows': 3,
                'readonly': 'readonly',
                'style': 'display: none;'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ===== CORREÇÃO: POPULAR VALORES AO EDITAR =====
        # Se está editando e tem cidade cadastrada
        if self.instance.pk and self.instance.cidade:
            if self.instance.cidade.estado:
                estado = self.instance.cidade.estado
                pais = estado.pais
                
                # Carregar estados do país
                self.fields['estado'].queryset = Estado.objects.filter(pais=pais, ativo=True).order_by('nome')
                # IMPORTANTE: Setar o valor inicial do estado
                self.fields['estado'].initial = estado
                
                # Filtrar cidades do estado
                self.fields['cidade'].queryset = Cidade.objects.filter(estado=estado, ativo=True).order_by('nome')
        
        # Preencher checkboxes de disponibilidade baseado no JSON
        if self.instance.pk and self.instance.disponibilidade:
            self.fields['disponibilidade_manha'].initial = 'manha' in self.instance.disponibilidade
            self.fields['disponibilidade_tarde'].initial = 'tarde' in self.instance.disponibilidade
            self.fields['disponibilidade_noite'].initial = 'noite' in self.instance.disponibilidade
            self.fields['disponibilidade_finais_semana'].initial = 'finais_de_semana' in self.instance.disponibilidade
        
        # Configurar campos de país, estado e cidade com cascata
        if 'pais' in self.fields:
            self.fields['pais'].queryset = Pais.objects.filter(ativo=True).order_by('nome')
            
        # Estado: configurar queryset dinamicamente
        if 'estado' in self.fields:
            if self.instance.pk and self.instance.pais:
                self.fields['estado'].queryset = Estado.objects.filter(
                    pais=self.instance.pais,
                    ativo=True
                ).order_by('nome')
            elif 'pais' in self.data:
                try:
                    pais_id = int(self.data.get('pais'))
                    self.fields['estado'].queryset = Estado.objects.filter(
                        pais_id=pais_id,
                        ativo=True
                    ).order_by('nome')
                except (ValueError, TypeError):
                    pass
        
        # Cidade: configurar queryset dinamicamente
        if 'cidade' in self.fields:
            self.fields['cidade'].queryset = Cidade.objects.none()
            self.fields['cidade'].required = False
            
            if self.instance.pk and self.instance.estado:
                self.fields['cidade'].queryset = Cidade.objects.filter(
                    estado=self.instance.estado,
                    ativo=True
                ).order_by('nome')
            elif 'estado' in self.data:
                try:
                    estado_id = int(self.data.get('estado'))
                    self.fields['cidade'].queryset = Cidade.objects.filter(
                        estado_id=estado_id,
                        ativo=True
                    ).order_by('nome')
                except (ValueError, TypeError):
                    pass
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Salvar disponibilidade como lista no JSON
        disponibilidade = []
        if self.cleaned_data.get('disponibilidade_manha'):
            disponibilidade.append('manha')
        if self.cleaned_data.get('disponibilidade_tarde'):
            disponibilidade.append('tarde')
        if self.cleaned_data.get('disponibilidade_noite'):
            disponibilidade.append('noite')
        if self.cleaned_data.get('disponibilidade_finais_semana'):
            disponibilidade.append('finais_de_semana')
        
        instance.disponibilidade = disponibilidade
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance
    
# ===============================================================
# FILTROS PERSONALIZADOS
# ===============================================================

class VerificadoEspacoFilter(SimpleListFilter):
    """Filtro por status de verificação"""
    title = 'Status de Verificação'
    parameter_name = 'verificado'
    
    def lookups(self, request, model_admin):
        return [
            ('verificado', '✓ Verificados'),
            ('nao_verificado', '✗ Não Verificados'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'verificado':
            return queryset.filter(is_verificado=True)
        elif self.value() == 'nao_verificado':
            return queryset.filter(is_verificado=False)
        return queryset


class AvaliacaoEspacoFilter(SimpleListFilter):
    """Filtro por avaliação"""
    title = 'Avaliação'
    parameter_name = 'avaliacao'
    
    def lookups(self, request, model_admin):
        return [
            ('5', '⭐⭐⭐⭐⭐ (5 estrelas)'),
            ('4+', '⭐⭐⭐⭐ (4+ estrelas)'),
            ('3+', '⭐⭐⭐ (3+ estrelas)'),
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
    """Filtro por tipo de espaço"""
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
# INLINE PARA GALERIA DE FOTOS
# ===============================================================

class FotoGaleriaEspacoInline(admin.TabularInline):
    """
    Inline para fotos da galeria do espaço
    Permite upload de até 7 fotos
    """
    model = FotoGaleriaEspaco
    extra = 1
    max_num = 7
    fields = ['imagem', 'descricao', 'ordem']
    verbose_name = 'Foto da Galeria'
    verbose_name_plural = '📸 Galeria de Fotos (até 7 fotos)'
    
    class Media:
        css = {
            'all': ('admin/css/custom_gallery.css',)
        }

# ===============================================================
# INLINES PARA RELACIONAMENTOS
# ===============================================================

class EspacoEspecialidadeInline(admin.TabularInline):
    """Inline para especialidades do espaço"""
    model = EspacoEspecialidade
    extra = 1
    min_num = 1
    max_num = 10
    fields = ['especialidade', 'preco_sessao', 'duracao_sessao', 'is_destaque', 'observacoes']
    autocomplete_fields = ['especialidade']
    verbose_name = 'Especialidade'
    verbose_name_plural = 'Especialidades Oferecidas'
    
    def get_formset(self, request, obj=None, **kwargs):
        """Customiza o formset para ajustar largura do campo observações"""
        formset = super().get_formset(request, obj, **kwargs)
        
        # Ajustar widget do campo observações
        if 'observacoes' in formset.form.base_fields:
            formset.form.base_fields['observacoes'].widget.attrs.update({
                'style': 'width: 300px; max-width: 300px;',
                'rows': 2
            })
        
        return formset


class AvaliacaoEspacoInline(admin.TabularInline):
    """Inline para avaliações do espaço"""
    model = AvaliacaoEspaco
    extra = 0
    fields = ['usuario', 'nota', 'comentario', 'is_active']
    readonly_fields = ['created_at']
    verbose_name = 'Avaliação'
    verbose_name_plural = 'Últimas Avaliações'
    
    def get_queryset(self, request):
        """Ordena por data de criação (mais recente primeiro)"""
        qs = super().get_queryset(request)
        return qs.order_by('-created_at')
    
    def has_add_permission(self, request, obj=None):
        """Não permite adicionar avaliações diretamente"""
        return False


# ===============================================================
# ADMIN PRINCIPAL - ESPACOS
# ===============================================================

@admin.register(Espaco)
class EspacoAdmin(admin.ModelAdmin):
    """Admin principal para Espaços Terapêuticos"""
    form = EspacoAdminForm
    
    list_display = [
        'nome_display', 'get_localizacao', 'tipo_espaco_display', 'status_display', 
        'rating_display', 'total_avaliacoes_display', 'comodidades_count', 'created_at'
    ]
    list_filter = [
        VerificadoEspacoFilter, AvaliacaoEspacoFilter, TipoEspacoFilter,
        'is_destaque', 'is_premium', 'aceita_locacao', 'tem_acessibilidade',
        'is_active', 'pais'
    ]
    search_fields = [
        'nome', 'descricao_breve', 'email', 'telefone',
        'cidade__nome', 'cidade_texto', 'bairro'
    ]
    readonly_fields = [
        'slug', 'created_at', 'updated_at'
    ]
    
    # Inlines
    inlines = [FotoGaleriaEspacoInline, EspacoEspecialidadeInline, AvaliacaoEspacoInline]
    
    # Configurações da lista
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Ações personalizadas
    actions = ['verificar_espacos', 'remover_verificacao', 'marcar_destaque', 'marcar_premium']
    
    # Campos com seleção múltipla horizontal
    filter_horizontal = ['comodidades']
    
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
                'pais', 'estado', 'cidade', 'cidade_texto', 'bairro', 'endereco', 'cep'
            ),
            'description': '''
                <strong>🌎 Como preencher:</strong><br>
                • <strong>Brasil:</strong> Selecione País → Estado → Cidade (do banco de dados)<br>
                • <strong>Outros países:</strong> Selecione País → digite a cidade no campo "Cidade (outros países)"
            '''
        }),
        ('Características', {
            'fields': (
                'tipo_espaco', 'aceita_locacao', 'tem_acessibilidade'
            )
        }),
        ('Disponibilidade', {
            'fields': (
                'disponibilidade_manha', 
                'disponibilidade_tarde', 
                'disponibilidade_noite', 
                'disponibilidade_finais_semana'
            ),
            'description': 'Marque os períodos em que o espaço está disponível'
        }),
        ('Comodidades', {
            'fields': (
                'comodidades',
            ),
            'description': 'Selecione as comodidades disponíveis no espaço'
        }),
        ('Contato', {
            'fields': (
                'telefone', 'email', 'whatsapp', 'website', 'instagram'
            )
        }),
        ('Foto Principal', {
            'fields': (
                'foto_principal',
            ),
            'description': '''
                <strong>📸 Foto de Destaque:</strong><br>
                Uma foto principal que representa o espaço
            '''
        }),
        ('Status e Configurações', {
            'fields': (
                ('is_verificado', 'data_verificacao'),
                'is_destaque', 
                'is_premium', 
                'is_active'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    ]
    
    # ===============================================================
    # MÉTODOS DE EXIBIÇÃO
    # ===============================================================
    
    def nome_display(self, obj):
        """Exibe nome com ícone se tiver foto"""
        if obj.foto_principal:
            return format_html(
                '<span style="display: flex; align-items: center;">'
                '📷 <strong style="margin-left: 5px;">{}</strong>'
                '</span>',
                obj.nome
            )
        return format_html('<strong>{}</strong>', obj.nome)
    nome_display.short_description = 'Nome do Espaço'
    nome_display.admin_order_field = 'nome'
    
    def get_localizacao(self, obj):
        """Exibe localização completa"""
        if obj.cidade:
            # Brasil com cidade do banco
            return f"{obj.cidade.nome}/{obj.estado.sigla if obj.estado else ''}"
        elif obj.cidade_texto:
            # Outros países com cidade em texto
            return f"{obj.cidade_texto}/{obj.pais.codigo if obj.pais else ''}"
        return '-'
    get_localizacao.short_description = 'Localização'
    
    def tipo_espaco_display(self, obj):
        """Exibe tipo de espaço com cor"""
        colors = {
            'clinica': '#059669',
            'centro_holistico': '#7c3aed',
            'estudio': '#2563eb',
            'spa': '#ec4899',
            'consultorio': '#f59e0b',
        }
        color = colors.get(obj.tipo_espaco, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; white-space: nowrap; display: inline-block;">{}</span>',
            color,
            obj.get_tipo_espaco_display()
        )
    tipo_espaco_display.short_description = 'Tipo'
    tipo_espaco_display.admin_order_field = 'tipo_espaco'
    
    def status_display(self, obj):
        """Exibe badges de status"""
        badges = []
        
        if obj.is_verificado:
            badges.append(
                '<span style="background: #059669; color: white; padding: 2px 6px; '
                'border-radius: 4px; font-size: 10px; margin-right: 4px; '
                'white-space: nowrap; display: inline-block;">✓ Verificado</span>'
            )
        
        if obj.is_premium:
            badges.append(
                '<span style="background: #f59e0b; color: white; padding: 2px 6px; '
                'border-radius: 4px; font-size: 10px; margin-right: 4px; '
                'white-space: nowrap; display: inline-block;">⭐ Premium</span>'
            )
        
        if obj.is_destaque:
            badges.append(
                '<span style="background: #7c3aed; color: white; padding: 2px 6px; '
                'border-radius: 4px; font-size: 10px; white-space: nowrap; '
                'display: inline-block;">🔥 Destaque</span>'
            )
        
        if not badges:
            return mark_safe('<span style="color: #9ca3af;">-</span>')
        
        return mark_safe(''.join(badges))

    status_display.short_description = 'Status'
    
    def rating_display(self, obj):
        """Exibe média de avaliações com estrelas"""
        media = obj.media_avaliacoes
        if media and media > 0:
            stars = '⭐' * int(round(media))
            return format_html(
                '<span title="Média: {:.1f}">{} {:.1f}</span>',
                media, stars, media
            )
        return format_html('<span style="color: #9ca3af;">Sem avaliações</span>')
    rating_display.short_description = 'Avaliação'
    
    def total_avaliacoes_display(self, obj):
        """Total de avaliações"""
        total = obj.total_avaliacoes
        if total > 0:
            return format_html(
                '<span style="color: #059669; font-weight: bold;">{}</span>',
                total
            )
        return format_html('<span style="color: #9ca3af;">0</span>')
    total_avaliacoes_display.short_description = '# Avaliações'
    
    def comodidades_count(self, obj):
        """Contador de comodidades"""
        count = obj.comodidades.count()
        if count > 0:
            return format_html(
                '<span style="color: #2563eb; font-weight: bold;">{}</span>',
                count
            )
        return format_html('<span style="color: #9ca3af;">0</span>')
    comodidades_count.short_description = '# Comodidades'
    
    # ===============================================================
    # AÇÕES PERSONALIZADAS
    # ===============================================================
    
    def verificar_espacos(self, request, queryset):
        """Ação para verificar espaços"""
        updated = queryset.update(is_verificado=True)
        self.message_user(request, f'{updated} espaço(s) verificado(s) com sucesso.')
    verificar_espacos.short_description = '✓ Verificar espaços'
    
    def remover_verificacao(self, request, queryset):
        """Ação para remover verificação"""
        updated = queryset.update(is_verificado=False)
        self.message_user(request, f'Verificação removida de {updated} espaço(s).')
    remover_verificacao.short_description = '✗ Remover verificação'
    
    def marcar_destaque(self, request, queryset):
        """Ação para marcar como destaque"""
        updated = queryset.update(is_destaque=True)
        self.message_user(request, f'{updated} espaço(s) marcado(s) como destaque.')
    marcar_destaque.short_description = '🔥 Marcar como destaque'
    
    def marcar_premium(self, request, queryset):
        """Ação para marcar como premium"""
        updated = queryset.update(is_premium=True)
        self.message_user(request, f'{updated} espaço(s) marcado(s) como premium.')
    marcar_premium.short_description = '⭐ Marcar como premium'
    
    # ===============================================================
    # OTIMIZAÇÃO DE QUERIES
    # ===============================================================
    
    def get_queryset(self, request):
        """Otimiza queries com select_related e prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'cidade', 'cidade__estado', 'estado', 'pais', 'responsavel'
        ).prefetch_related(
            'comodidades', 'avaliacoes'
        )
    
    # ===============================================================
    # CUSTOMIZAR LABELS DOS CAMPOS
    # ===============================================================
    
    def get_form(self, request, obj=None, **kwargs):
        """Customiza labels dos campos removendo 'is_'"""
        form = super().get_form(request, obj, **kwargs)
        
        # Remover "is_" dos labels
        if 'is_verificado' in form.base_fields:
            form.base_fields['is_verificado'].label = 'Verificado'
        if 'is_destaque' in form.base_fields:
            form.base_fields['is_destaque'].label = 'Destaque'
        if 'is_premium' in form.base_fields:
            form.base_fields['is_premium'].label = 'Premium'
        if 'is_active' in form.base_fields:
            form.base_fields['is_active'].label = 'Ativo'
        
        return form
    
    class Media:
        css = {
            'all': ('admin/css/custom_espacos.css',)
        }


# ===============================================================
# ADMINS PARA MODELS AUXILIARES
# ===============================================================

@admin.register(Comodidade)
class ComodidadeAdmin(admin.ModelAdmin):
    """Admin para Comodidades"""
    list_display = [
        'nome', 'icone_display', 'destaque_display', 
        'total_espacos', 'is_destaque', 'is_active'
    ]
    list_filter = ['is_destaque', 'is_active']
    search_fields = ['nome', 'descricao']
    list_editable = ['is_destaque', 'is_active']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('nome',)}
    
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
        """Exibe o ícone da comodidade"""
        if obj.icone:
            return format_html(
                '<span style="font-size: 16px;" title="{}">{}</span>',
                obj.nome, obj.icone
            )
        return format_html('<span style="color: gray;">-</span>')
    icone_display.short_description = 'Ícone'
    
    def destaque_display(self, obj):
        """Exibe status de destaque com ícone"""
        if obj.is_destaque:
            return format_html('<span style="color: gold;">⭐ Destaque</span>')
        return format_html('<span style="color: gray;">-</span>')
    destaque_display.short_description = 'Status'
    
    def total_espacos(self, obj):
        """Total de espaços com esta comodidade"""
        return obj.espacos.filter(is_active=True).count()
    total_espacos.short_description = 'Espaços'


# ===============================================================
# ADMINS PARA AVALIAÇÕES E CONTATOS
# ===============================================================

@admin.register(AvaliacaoEspaco)
class AvaliacaoEspacoAdmin(admin.ModelAdmin):
    """Admin para Avaliações de Espaços"""
    list_display = [
        'espaco', 'usuario', 'nota_display', 'comentario_truncado', 
        'is_active', 'created_at'
    ]
    list_filter = ['nota', 'is_active', 'created_at']
    search_fields = ['espaco__nome', 'usuario__username', 'comentario']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('Avaliação', {
            'fields': ('espaco', 'usuario', 'nota', 'comentario')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def nota_display(self, obj):
        """Exibe nota com estrelas"""
        stars = '⭐' * obj.nota
        return format_html('<span title="{} estrelas">{}</span>', obj.nota, stars)
    nota_display.short_description = 'Nota'
    
    def comentario_truncado(self, obj):
        """Comentário truncado"""
        if len(obj.comentario) > 50:
            return f'{obj.comentario[:50]}...'
        return obj.comentario
    comentario_truncado.short_description = 'Comentário'


@admin.register(ContatoEspaco)
class ContatoEspacoAdmin(admin.ModelAdmin):
    """Admin para Contatos de Espaços"""
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
        """Assunto truncado"""
        if len(obj.assunto) > 30:
            return f'{obj.assunto[:30]}...'
        return obj.assunto
    assunto_truncado.short_description = 'Assunto'
    
    def status_display(self, obj):
        """Exibe status de resposta"""
        if obj.is_respondido:
            return format_html('<span style="color: #059669;">✓ Respondido</span>')
        return format_html('<span style="color: #f59e0b;">⏳ Pendente</span>')
    status_display.short_description = 'Status'