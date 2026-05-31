# ===============================================================
# Título: Admin do App Terapeutas - Espaço Vital (Versão Corrigida)
# Descrição: Interface administrativa para gerenciar terapeutas e especialidades
# ===============================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg
from django.contrib.admin import SimpleListFilter
from django.db import models
from .models import (
    Terapeuta, TerapeutaEspecialidade, Especialidade, 
    Avaliacao, Contato, SessionType, ProfileType, ClientType,
    FotoGaleriaTerapeuta
)

from django import forms
from core.models import Pais, Estado, Cidade

class TerapeutaAdminForm(forms.ModelForm):
    class Meta:
        model = Terapeuta
        fields = '__all__'

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
            return queryset.filter(rating_medio=5)
        elif self.value() == '4+':
            return queryset.filter(rating_medio__gte=4)
        elif self.value() == '3+':
            return queryset.filter(rating_medio__gte=3)
        elif self.value() == 'sem_avaliacao':
            return queryset.filter(rating_medio__isnull=True)
        return queryset

# ===============================================================
# INLINES
# ===============================================================

# ===============================================================
# INLINE PARA GALERIA DE FOTOS
# ===============================================================

class FotoGaleriaTerapeutaInline(admin.TabularInline):
    """
    Inline para fotos da galeria do terapeuta
    Permite upload de até 7 fotos
    """
    model = FotoGaleriaTerapeuta
    extra = 1
    max_num = 7
    fields = ['imagem', 'descricao', 'ordem']
    verbose_name = 'Foto da Galeria'
    verbose_name_plural = '📸 Galeria de Fotos (até 7 fotos)'
    
    class Media:
        css = {
            'all': ('admin/css/custom_gallery.css',)
        }

class TerapeutaEspecialidadeInline(admin.TabularInline):
    """
    Inline para especialidades do terapeuta
    """
    model = TerapeutaEspecialidade
    extra = 1
    verbose_name = 'Especialidade'
    verbose_name_plural = 'Especialidades do Terapeuta'

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Diminuir largura do campo observações
        if 'observacoes' in formset.form.base_fields:
            formset.form.base_fields['observacoes'].widget.attrs.update({
                'style': 'width: 250px;',
                'rows': 2
            })
        # Diminuir largura do campo preço da sessão
        if 'preco_sessao' in formset.form.base_fields:
            formset.form.base_fields['preco_sessao'].widget.attrs.update({
                'style': 'width: 80px;'
            })
        # Diminuir largura do campo experiencia_anos
        if 'experiencia_anos' in formset.form.base_fields:
            formset.form.base_fields['experiencia_anos'].widget.attrs.update({
                'style': 'width: 50px;'
            })
        return formset

class AvaliacaoInline(admin.TabularInline):
    """
    Inline para avaliações do terapeuta
    """
    model = Avaliacao
    extra = 0
    readonly_fields = ['cliente', 'nota', 'comentario', 'created_at']
    can_delete = False
    verbose_name = 'Avaliação'
    verbose_name_plural = 'Avaliações Recebidas'
    
    def has_add_permission(self, request, obj):
        return False

# ===============================================================
# ADMINS PRINCIPAIS
# ===============================================================

# @admin.register(Especialidade)
# class EspecialidadeAdmin(admin.ModelAdmin):
#     """
#     Admin para Especialidades
#     """
#     list_display = ['nome', 'destaque', 'ordem', 'total_terapeutas', 'is_active']
#     list_filter = ['destaque', 'is_active']
#     search_fields = ['nome', 'descricao_curta', 'descricao_completa']
#     list_editable = ['destaque', 'ordem']
#     ordering = ['ordem', 'nome']
    
#     fieldsets = [
#         ('Informações Básicas', {
#             'fields': ('nome', 'slug', 'descricao_curta')
#         }),
#         ('Descrição Completa', {
#             'fields': ('descricao_completa',),
#             'classes': ('collapse',)
#         }),
#         ('Configurações', {
#             'fields': ('destaque', 'ordem', 'cor_destaque')
#         }),
#         ('Sistema', {
#             'fields': ('is_active', 'created_at', 'updated_at'),
#             'classes': ('collapse',)
#         })
#     ]
    
#     readonly_fields = ['slug', 'created_at', 'updated_at']
    
#     def total_terapeutas(self, obj):
#         """
#         Total de terapeutas com esta especialidade
#         """
#         return obj.terapeuta_set.filter(is_active=True).count()
#     total_terapeutas.short_description = 'Terapeutas'

@admin.register(Terapeuta)
class TerapeutaAdmin(admin.ModelAdmin):
    """
    Admin principal para Terapeutas com controle total para admin
    """
    form = TerapeutaAdminForm    

    list_display = [
        'nome_exibicao', 'user_display', 'cidade_principal_display', 'verificado',
        'premium', 'destaque', 'is_active'
    ]
    list_filter = [
        'destaque', 'premium', 'is_active'
    ]
    # Filtros complexos temporariamente desabilitados para debug
    # VerificadoFilter, AvaliacaoFilter, 'cidade_principal__estado', 'tipos_sessao'
    search_fields = [
        'nome_completo', 'nome_exibicao', 'email_profissional',
        'user__username', 'user__email', 'cidade_principal__nome'
    ]
    readonly_fields = [
        'user_info', 'slug', 'visualizacoes', 'total_contatos', 
        'rating_medio', 'total_avaliacoes', 'created_at', 'updated_at'
    ]

    filter_horizontal = [
        #'especialidades', 'cidades_atendimento'
    ]
    
    # Inlines
    inlines = [TerapeutaEspecialidadeInline, FotoGaleriaTerapeutaInline]
    # AvaliacaoInline temporariamente desabilitado para debug do erro 500
    
    # Configurações da lista
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Ações personalizadas
    actions = ['verificar_terapeutas', 'remover_verificacao', 'marcar_destaque', 'remover_destaque', 'ativar_terapeutas', 'desativar_terapeutas', 'exportar_para_csv',]
    
    def get_fieldsets(self, request, obj=None):
        """
        Fieldsets dinâmicos baseados em permissões
        ADMIN: Vê tudo, pode atribuir qualquer usuário
        TERAPEUTA: Apenas campos que pode editar
        """
        if self.is_admin_user(request.user):
            # ADMIN VÊ TUDO
            return [
                ('Atribuição de Usuário', {
                    'fields': ('user', 'user_info'),
                    'description': '⚠️ APENAS ADMIN: Selecione o usuário que será o terapeuta. Cada usuário pode ter apenas 1 perfil.'
                }),
                ('Informações Básicas', {
                    'fields': ('nome_completo', 'nome_exibicao', 'slug')
                }),
                ('Contato', {
                    'fields': ('email_profissional', 'whatsapp','whatsapp_ativo', ),
                    'classes': ('collapse',),
                }),
                
                ('Redes Sociais', {
                    'fields': ('instagram', 'facebook', 'youtube', 'tiktok', ),
                    'classes': ('collapse',),
                }),
                ('Localização', {
                    'fields': ('pais', 'estado', 'cidade_principal', 'cidade_texto', 'cidades_atendimento', 'bairro', 'endereco'),
                    'description': '''
                        <strong>🌎 Como preencher:</strong><br>
                        • <strong>Brasil:</strong> País → Estado → Cidade<br>
                        • <strong>Outros países:</strong> País → digite a cidade
                    '''
                }),
                ('Informações Profissionais', {
                    'fields': ('registro_profissional', 'formacao', 'experiencia_anos')
                }),
                ('Configurações de Atendimento', {
                    'fields': ('tipos_sessao', 'para_quem', 'acessibilidade')
                }),
                ('Descrições', {
                    'fields': ('bio_curta', 'bio_completa', 'metodologia')
                }),
                ('Mídia', {
                    'fields': ('foto_perfil', 'foto_capa'),
                    'classes': ('collapse',)
                }),
                ('Status e Verificação (ADMIN)', {
                    'fields': ('verificado', 'destaque', 'premium', 'data_verificacao'),
                    'classes': ('collapse',),
                    'description': '🔒 Configurações exclusivas para administradores'
                }),
                ('Métricas', {
                    'fields': ('visualizacoes', 'total_contatos', 'rating_medio', 'total_avaliacoes'),
                    'classes': ('collapse',)
                }),
                ('Sistema', {
                    'fields': ('is_active', 'created_at', 'updated_at'),
                    'classes': ('collapse',)
                })
            ]
        else:
            # TERAPEUTA VÊ APENAS O NECESSÁRIO
            return [
                ('Informações do Usuário', {
                    'fields': ('user_info',),
                    'description': 'Usuário associado a este perfil (não editável)'
                }),
                ('Informações Básicas', {
                    'fields': ('nome_completo', 'nome_exibicao', 'slug')
                }),
                ('Contato', {
                    'fields': ('email_profissional', 'telefone', 'whatsapp')
                }),
                ('Localização', {
                    'fields': ('cidade_principal', 'cidades_atendimento', 'bairro', 'endereco')
                }),
                ('Informações Profissionais', {
                    'fields': ('registro_profissional', 'formacao', 'experiencia_anos')
                }),
                ('Configurações de Atendimento', {
                    'fields': ('tipos_sessao', 'para_quem', 'acessibilidade')
                }),
                ('Descrições', {
                    'fields': ('bio_curta', 'bio_completa', 'metodologia')
                }),
                ('Mídia', {
                    'fields': ('foto_perfil', 'foto_capa'),
                    'classes': ('collapse',)
                }),
            ]
    
    def get_readonly_fields(self, request, obj=None):
        """
        Campos readonly baseados em permissões
        """
        base_readonly = [
            'slug', 'visualizacoes', 'total_contatos', 
            'rating_medio', 'total_avaliacoes', 'created_at', 'updated_at'
        ]
        
        if self.is_admin_user(request.user):
            # ADMIN: Apenas user_info é readonly (mas pode alterar o user em si)
            base_readonly.append('user_info')
        else:
            # TERAPEUTA: Não pode alterar campos administrativos
            base_readonly.extend([
                'user_info', 'verificado', 'destaque', 'premium', 
                'data_verificacao', 'is_active'
            ])
        
        return base_readonly
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Customizar formulário baseado em permissões
        """
        form = super().get_form(request, obj, **kwargs)
        
        if self.is_admin_user(request.user):
            # ADMIN: Pode escolher qualquer usuário que ainda não tem perfil
            if 'user' in form.base_fields:
                # Filtrar usuários que já têm perfil de terapeuta
                from django.contrib.auth.models import User
                
                existing_users = Terapeuta.objects.values_list('user_id', flat=True)
                available_users = User.objects.exclude(id__in=existing_users)
                
                # Se estamos editando, incluir o usuário atual
                if obj and obj.user:
                    available_users = available_users | User.objects.filter(id=obj.user.id)
                
                form.base_fields['user'].queryset = available_users
                form.base_fields['user'].help_text = (
                    'Selecione o usuário que será associado a este perfil de terapeuta. '
                    'Apenas usuários que ainda não possuem perfil aparecem na lista.'
                )
        else:
            # TERAPEUTA: Não pode alterar o usuário
            if 'user' in form.base_fields:
                del form.base_fields['user']
        
        return form
    
    # Temporariamente simplificado para debug
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    class Media:
        """
        Adiciona JavaScript customizado para máscara de telefone e ícones de redes sociais
        """
        js = ('js/terapeuta_admin.js',)
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',)
        }
    
    def has_add_permission(self, request):
        """
        Controlar permissão de adicionar
        """
        if self.is_admin_user(request.user):
            # ADMIN: Pode sempre criar novos perfis
            return True
        
        # TERAPEUTA: Só pode criar se não tiver perfil ainda
        if hasattr(request.user, 'terapeuta'):
            return False  # Já tem perfil
        
        # Se for do grupo Terapeutas, pode criar seu perfil
        return request.user.groups.filter(name='Terapeutas').exists()
    
    def has_change_permission(self, request, obj=None):
        """
        Controlar permissão de editar
        """
        if self.is_admin_user(request.user):
            # ADMIN: Pode editar qualquer perfil
            return True
        
        # TERAPEUTA: Só pode editar seu próprio perfil
        if obj is not None:
            return obj.user == request.user
        
        return True
    
    def has_delete_permission(self, request, obj=None):
        """
        Controlar permissão de deletar
        """
        # APENAS ADMIN pode deletar perfis
        return self.is_admin_user(request.user)
    
    def save_model(self, request, obj, form, change):
        """
        Salvar modelo com validações de segurança
        """
        # Se for criação e não for admin, definir usuário como o logado
        if not change and not self.is_admin_user(request.user):
            obj.user = request.user
        
        # Validação extra: Verificar se o usuário já tem perfil
        if hasattr(form, 'cleaned_data') and 'user' in form.cleaned_data:
            user_selecionado = form.cleaned_data['user']
            
            # Verificar se já existe um terapeuta para este usuário
            existing_terapeuta = Terapeuta.objects.filter(user=user_selecionado).exclude(pk=obj.pk).first()
            if existing_terapeuta:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f'O usuário {user_selecionado.username} já possui um perfil de terapeuta. '
                    f'Cada usuário pode ter apenas 1 perfil de terapeuta.'
                )
        
        super().save_model(request, obj, form, change)
        
        # Log de ações administrativas
        if self.is_admin_user(request.user):
            action = 'criado' if not change else 'editado'
            self.message_user(
                request,
                f'Perfil de terapeuta {action} com sucesso para o usuário {obj.user.username}.',
                level='SUCCESS'
            )
    
    # ===============================================================
    # MÉTODOS DE EXIBIÇÃO
    # ===============================================================
    
    def user_display(self, obj):
        """
        Exibe informações do usuário na listagem
        """
        if obj.user:
            groups = obj.user.groups.all()
            groups_text = ', '.join([g.name for g in groups]) if groups else 'Nenhum grupo'
            
            return format_html(
                '<div style="line-height: 1.4;">'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}</small><br>'
                '<small style="color: #059669; font-size: 10px;">{}</small>'
                '</div>',
                obj.user.get_full_name() or obj.user.username,
                obj.user.email,
                groups_text
            )
        return '-'
    user_display.short_description = 'Usuário'
    
    def user_info(self, obj):
        """
        Exibe informações detalhadas do usuário (readonly)
        """
        if obj and obj.user:
            user = obj.user
            groups = user.groups.all()
            
            # Verificar se é o único perfil deste usuário
            profile_count = Terapeuta.objects.filter(user=user).count()
            uniqueness_info = ''
            if profile_count == 1:
                uniqueness_info = (
                    '<div style="margin-top: 8px; padding: 8px; background: #f0fdf4; '
                    'border-radius: 4px; border-left: 3px solid #059669;">'
                    '<small style="color: #059669; font-weight: bold;">✅ Perfil único: '
                    'Este é o único perfil de terapeuta deste usuário.</small>'
                    '</div>'
                )
            
            # Formatação dos grupos
            groups_html = ''
            if groups:
                group_colors = {
                    'Administradores': '#dc2626',
                    'Terapeutas': '#059669',
                    'Gestores de Espaços': '#7c3aed',
                    'Editores de Conteúdo': '#2563eb'
                }
                
                group_tags = []
                for group in groups:
                    color = group_colors.get(group.name, '#6b7280')
                    group_tags.append(
                        '<span style="background-color: {}; color: white; '
                        'padding: 4px 8px; border-radius: 12px; font-size: 12px; '
                        'margin-right: 6px; margin-bottom: 4px; display: inline-block; '
                        'font-weight: 500;">{}</span>'.format(color, group.name)
                    )
                groups_html = (
                    '<div style="margin-top: 12px;">'
                    '<strong style="color: #374151; display: block; margin-bottom: 6px;">Grupos de Permissão:</strong>'
                    '<div style="line-height: 1.6;">{}</div>'
                    '</div>'.format(''.join(group_tags))
                )
            
            # Status do usuário
            status_color = '#10b981' if user.is_active else '#ef4444'
            status_text = '✅ Ativo' if user.is_active else '❌ Inativo'
            
            html_content = '''
            <div style="padding: 16px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
            border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px; 
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                
                <div>
                <strong style="color: #374151; display: block; margin-bottom: 4px;">👤 Nome de usuário:</strong>
                <span style="color: #6b7280; font-family: monospace; background: #f9fafb; 
                padding: 2px 6px; border-radius: 4px;">{}</span>
                </div>
                
                <div>
                <strong style="color: #374151; display: block; margin-bottom: 4px;">📧 E-mail:</strong>
                <span style="color: #6b7280;">{}</span>
                </div>
                
                <div>
                <strong style="color: #374151; display: block; margin-bottom: 4px;">📝 Nome completo:</strong>
                <span style="color: #6b7280;">{}</span>
                </div>
                
                <div>
                <strong style="color: #374151; display: block; margin-bottom: 4px;">📅 Data de cadastro:</strong>
                <span style="color: #6b7280;">{}</span>
                </div>
                
                </div>
                
                <div style="border-top: 1px solid #e5e7eb; padding-top: 12px;">
                <strong style="color: #374151; display: block; margin-bottom: 6px;">🔒 Status da conta:</strong>
                <span style="color: {}; font-weight: 600;">{}</span>
                </div>
                
                {}
                {}
            </div>
            '''.format(
                user.username,
                user.email or 'Não informado',
                user.get_full_name() or 'Não informado',
                user.date_joined.strftime('%d/%m/%Y às %H:%M') if user.date_joined else 'Não informado',
                status_color,
                status_text,
                groups_html,
                uniqueness_info
            )
            
            return format_html(html_content)
        
        return format_html(
            '<div style="padding: 16px; background: #fef2f2; border: 1px solid #fecaca; '
            'border-radius: 8px; color: #dc2626; text-align: center;">'
            '⚠️ Nenhum usuário associado'
            '</div>'
        )
    user_info.short_description = 'Informações do Usuário'
    
    def status_display(self, obj):
        """
        Status com ícones e cores
        """
        status_parts = []
        
        if obj.verificado:
            status_parts.append(
                '<span style="color: #10b981; font-weight: bold;">✓ Verificado</span>'
            )
        else:
            status_parts.append(
                '<span style="color: #f59e0b;">⏳ Pendente</span>'
            )
        
        if obj.destaque:
            status_parts.append(
                '<span style="color: #dc2626;">★ Destaque</span>'
            )
        
        if obj.premium:
            status_parts.append(
                '<span style="color: #7c3aed;">💎 Premium</span>'
            )
        
        if not obj.is_active:
            status_parts.append(
                '<span style="color: #6b7280;">💤 Inativo</span>'
            )
        
        return format_html('<br>'.join(status_parts))
    status_display.short_description = 'Status'
    
    def rating_display(self, obj):
        """
        Avaliação com estrelas
        """
        if obj.rating_medio:
            stars = '⭐' * int(obj.rating_medio)
            return format_html(
                '<span title="Média: {}">{} ({})</span>',
                obj.rating_medio, stars, obj.rating_medio
            )
        return '📊 Sem avaliações'
    rating_display.short_description = 'Avaliação'
    
    # ===============================================================
    # AÇÕES PERSONALIZADAS (APENAS ADMIN)
    # ===============================================================
    
    def verificar_terapeutas(self, request, queryset):
        """
        Ação para verificar terapeutas (apenas admin)
        """
        if not self.is_admin_user(request.user):
            self.message_user(
                request,
                'Apenas administradores podem verificar terapeutas.',
                level='ERROR'
            )
            return
        
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
        Ação para remover verificação (apenas admin)
        """
        if not self.is_admin_user(request.user):
            self.message_user(
                request,
                'Apenas administradores podem remover verificação.',
                level='ERROR'
            )
            return
        
        updated = queryset.update(
            verificado=False,
            data_verificacao=None
        )
        self.message_user(
            request,
            f'{updated} terapeuta(s) teve(ram) verificação removida.'
        )
    remover_verificacao.short_description = 'Remover verificação'
    
    def marcar_destaque(self, request, queryset):
        """
        Ação para marcar como destaque (apenas admin)
        """
        if not self.is_admin_user(request.user):
            self.message_user(
                request,
                'Apenas administradores podem marcar destaques.',
                level='ERROR'
            )
            return
        
        updated = queryset.update(destaque=True)
        self.message_user(
            request,
            f'{updated} terapeuta(s) marcado(s) como destaque.'
        )
    marcar_destaque.short_description = 'Marcar como destaque'

    def remover_destaque(self, request, queryset):
        """
        Ação para remover de destaque (apenas admin)
        """
        if not self.is_admin_user(request.user):
            self.message_user(
                request,
                'Apenas administradores podem remover destaques.',
                level='ERROR'
            )
            return
        
        updated = queryset.update(destaque=False)
        self.message_user(
            request,
            f'{updated} terapeuta(s) removido(s) do destaque.'
        )
    remover_destaque.short_description = 'Remover do destaque'
    
    def ativar_terapeutas(self, request, queryset):
        """
        Ação para ativar terapeutas (tornar perfil ativo)
        """
        if not self.is_admin_user(request.user):
            self.message_user(
                request,
                'Apenas administradores podem ativar terapeutas.',
                level='ERROR'
            )
            return
        
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} terapeuta(s) ativado(s) com sucesso.',
            level='SUCCESS'
        )
    ativar_terapeutas.short_description = 'Ativar terapeutas selecionados'
    
    def desativar_terapeutas(self, request, queryset):
        """
        Ação para desativar terapeutas (suspender perfil)
        """
        if not self.is_admin_user(request.user):
            self.message_user(
                request,
                'Apenas administradores podem desativar terapeutas.',
                level='ERROR'
            )
            return
        
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} terapeuta(s) desativado(s) com sucesso.',
            level='WARNING'
        )
    desativar_terapeutas.short_description = 'Desativar terapeutas selecionados'
    
    def exportar_para_csv(self, request, queryset):
        """
        Ação para exportar terapeutas selecionados para CSV
        """
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        # Criar resposta HTTP com CSV
        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="terapeutas_{timestamp}.csv"'
        
        # Criar writer CSV
        writer = csv.writer(response)
        
        # Cabeçalhos
        writer.writerow([
            'ID',
            'Nome',
            'Email',
            'Telefone',
            'CRP/CRT',
            'Cidade',
            'Estado',
            'Verificado',
            'Destaque',
            'Plano',
            'Ativo',
            'Data Cadastro'
        ])
        
        # Dados dos terapeutas
        for terapeuta in queryset:
            writer.writerow([
                terapeuta.id,
                terapeuta.nome_exibicao,
                terapeuta.usuario.email if terapeuta.usuario else '',
                terapeuta.telefone or '',
                terapeuta.crp_crt or '',
                terapeuta.get_cidade_principal_display(),
                '',  # Estado já está na cidade
                'Sim' if terapeuta.verificado else 'Não',
                'Sim' if terapeuta.destaque else 'Não',
                terapeuta.get_plano_display(),
                'Sim' if terapeuta.ativo else 'Não',
                terapeuta.created_at.strftime('%d/%m/%Y %H:%M')
            ])
        
        self.message_user(
            request,
            f'{queryset.count()} terapeuta(s) exportado(s) com sucesso.',
            level='SUCCESS'
        )
        
        return response
    exportar_para_csv.short_description = 'Exportar selecionados para CSV'
    
    # ===============================================================
    # MÉTODOS UTILITÁRIOS
    # ===============================================================
    
    def is_admin_user(self, user):
        """
        Verifica se o usuário é administrador
        """
        return user.is_superuser or user.groups.filter(name='Administradores').exists()
    
    def get_cidade_principal_display(self, obj):
        """Exibe cidade principal na listagem do admin"""
        if obj.cidade_principal:
            return f"{obj.cidade_principal.nome} - {obj.cidade_principal.estado.sigla}"
        return "Não informado"

    get_cidade_principal_display.short_description = 'Cidade Principal'
    get_cidade_principal_display.admin_order_field = 'cidade_principal__nome'

    def cidade_principal_display(self, obj):
        """Exibe cidade principal ou cidade texto"""
        return obj.get_cidade_principal_display()
    cidade_principal_display.short_description = 'Cidade'

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """
        Customiza widgets para campos com múltipla seleção (JSONField)
        """
        from django import forms
        import json
        
        if db_field.name == 'tipos_sessao':
            # Criar um campo customizado para JSONField
            class TiposSessaoField(forms.MultipleChoiceField):
                def prepare_value(self, value):
                    # Converter JSONField para lista
                    if isinstance(value, str):
                        return json.loads(value) if value else []
                    return value or []
                
                def to_python(self, value):
                    # Retorna lista (será salva como JSON automaticamente)
                    if not value:
                        return []
                    return list(value)
            
            return TiposSessaoField(
                choices=[
                    ('presencial', 'Presencial'),
                    ('online', 'On-line'), 
                    ('domicilio', 'Domicílio')
                ],
                widget=forms.CheckboxSelectMultiple(),
                help_text='Selecione os tipos de sessão que você oferece',
                required=False
            )
        
        elif db_field.name == 'para_quem':
            # Criar um campo customizado para JSONField
            class ParaQuemField(forms.MultipleChoiceField):
                def prepare_value(self, value):
                    # Converter JSONField para lista
                    if isinstance(value, str):
                        return json.loads(value) if value else []
                    return value or []
                
                def to_python(self, value):
                    # Retorna lista (será salva como JSON automaticamente)
                    if not value:
                        return []
                    return list(value)
            
            return ParaQuemField(
                choices=[
                    ('adultos', 'Adultos'),
                    ('criancas', 'Crianças'),
                    ('idosos', 'Idosos'),
                    ('casais', 'Casais'),
                    ('grupos', 'Grupos')
                ],
                widget=forms.CheckboxSelectMultiple(),
                help_text='Selecione os públicos que você atende',
                required=False
            )
        
        return super().formfield_for_dbfield(db_field, request, **kwargs)

# ===============================================================
# ADMINS PARA AVALIAÇÕES E CONTATOS
# ===============================================================

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
    
    def cliente_nome(self, obj):
        return obj.cliente.get_full_name() or obj.cliente.username
    cliente_nome.short_description = 'Cliente'
    
    def nota_display(self, obj):
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
    
    def assunto_truncado(self, obj):
        if len(obj.assunto) > 50:
            return f'{obj.assunto[:50]}...'
        return obj.assunto
    assunto_truncado.short_description = 'Assunto'
    
    def status_display(self, obj):
        colors = {
            'enviado': '#fbbf24',
            'lido': '#3b82f6',
            'respondido': '#10b981',
            'arquivado': '#6b7280',
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
# admin.site.site_header = "Espaço Vital - Administração"
# admin.site.site_title = "Espaço Vital Admin"
# admin.site.index_title = "Painel de Controle - Terapeutas"