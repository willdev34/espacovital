# ===============================================================
# Título: Admin Customizado para Permissões - Espaço Vital (Corrigido)
# Descrição: Customizações do Django Admin com permissões traduzidas
# Autor: Will
# Data: 27/09/2025
# ===============================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group, Permission
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from .models import Contact, Newsletter, FAQ, SiteConfiguration, Pais, Estado, Cidade, Especialidade

# ===============================================================
# FILTROS PERSONALIZADOS
# ===============================================================

class CreatedDateFilter(SimpleListFilter):
    """
    Filtro personalizado por data de criação
    """
    title = 'Data de Criação'
    parameter_name = 'created_date'
    
    def lookups(self, request, model_admin):
        return [
            ('today', 'Hoje'),
            ('week', 'Esta semana'),
            ('month', 'Este mês'),
            ('year', 'Este ano'),
        ]
    
    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(created_at__date=now.date())
        elif self.value() == 'week':
            start_week = now - timezone.timedelta(days=now.weekday())
            return queryset.filter(created_at__gte=start_week)
        elif self.value() == 'month':
            return queryset.filter(
                created_at__year=now.year,
                created_at__month=now.month
            )
        elif self.value() == 'year':
            return queryset.filter(created_at__year=now.year)
        return queryset

class UserGroupFilter(SimpleListFilter):
    """
    Filtro por grupos de usuários
    """
    title = 'Grupo de Usuário'
    parameter_name = 'user_group'
    
    def lookups(self, request, model_admin):
        return [(group.id, group.name) for group in Group.objects.all()]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(groups__id=self.value())
        return queryset

# ===============================================================
# CUSTOMIZAÇÃO DO ADMIN DE USUÁRIOS
# ===============================================================
class CustomUserAdmin(UserAdmin):
    """
    Admin customizado para usuários com seção detalhada de permissões
    """
    list_display = [
        'username', 'email', 'first_name', 'last_name', 
        'groups_display', 'permissions_summary_short', 'is_staff', 'is_active', 'date_joined'
    ]
    list_filter = [
        UserGroupFilter, 'is_staff', 'is_superuser', 'is_active', 'date_joined'
    ]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    # Fieldsets customizados com seção de permissões detalhada
    fieldsets = UserAdmin.fieldsets + (
        ('Resumo Detalhado de Permissões', {
            'fields': ('permissions_summary_detailed',),
            'classes': ('collapse',),
            'description': 'Visualização completa de todas as permissões do usuário'
        }),
        ('Configuração de Acesso ao Sistema', {
            'fields': ('system_access_info',),
            'description': 'Informações sobre que partes do sistema este usuário pode acessar'
        }),
    )
    
    readonly_fields = ['permissions_summary_detailed', 'system_access_info']
    
    def groups_display(self, obj):
        """
        Exibe os grupos do usuário com cores
        """
        groups = obj.groups.all()
        if not groups:
            return format_html(
                '<span style="color: #999; font-style: italic;">Nenhum grupo</span>'
            )
        
        # Cores para diferentes tipos de grupos
        group_colors = {
            'Administradores': '#dc2626',     # vermelho
            'Terapeutas': '#059669',          # verde
            'Gestores de Espaços': '#7c3aed', # roxo
            'Editores de Conteúdo': '#2563eb' # azul
        }
        
        group_tags = []
        for group in groups:
            color = group_colors.get(group.name, '#6b7280')
            group_tags.append(
                format_html(
                    '<span style="background-color: {}; color: white; '
                    'padding: 2px 6px; border-radius: 8px; font-size: 11px; '
                    'margin-right: 4px; display: inline-block;">{}</span>',
                    color, group.name
                )
            )
        
        return format_html(''.join(group_tags))
    
    groups_display.short_description = 'Grupos'
    
    def permissions_summary_short(self, obj):
        """
        Resumo curto das permissões para a listagem
        """
        if obj.is_superuser:
            return format_html(
                '<span style="color: #dc2626; font-weight: bold;">🔥 SUPER</span>'
            )
        
        groups = obj.groups.all()
        direct_perms = obj.user_permissions.count()
        group_perms = sum(group.permissions.count() for group in groups)
        total_perms = direct_perms + group_perms
        
        if total_perms == 0:
            return format_html(
                '<span style="color: #6b7280;">❌ Sem permissões</span>'
            )
        
        return format_html(
            '<span style="color: #059669; font-weight: bold;">✅ {} permissão(ões)</span>',
            total_perms
        )
    
    permissions_summary_short.short_description = 'Permissões'
    
    def permissions_summary_detailed(self, obj):
        """
        Exibe resumo detalhado das permissões do usuário
        """
        if obj.is_superuser:
            return format_html(
                '<div style="padding: 16px; background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); '
                'border: 1px solid #fecaca; border-radius: 8px; text-align: center;">'
                '<h3 style="color: #dc2626; margin: 0 0 8px 0;">🔥 SUPERUSUÁRIO</h3>'
                '<p style="margin: 0; color: #7f1d1d; font-size: 14px;">'
                'Este usuário tem acesso completo e irrestrito a todo o sistema. '
                'Pode realizar qualquer ação, incluindo gerenciar outros usuários e permissões.'
                '</p>'
                '</div>'
            )
        
        # Obter permissões
        direct_permissions = list(obj.user_permissions.all())
        groups = obj.groups.all()
        
        if not direct_permissions and not groups:
            return format_html(
                '<div style="padding: 16px; background: #f9fafb; border: 1px solid #e5e7eb; '
                'border-radius: 8px; text-align: center;">'
                '<p style="color: #6b7280; margin: 0;">❌ Este usuário não possui permissões específicas atribuídas.</p>'
                '<p style="color: #6b7280; margin: 8px 0 0 0; font-size: 12px;">'
                'Para dar acesso ao sistema, atribua o usuário a um grupo ou configure permissões individuais.'
                '</p>'
                '</div>'
            )
        
        html_parts = []
        
        # Seção de grupos
        if groups:
            html_parts.append(
                '<div style="margin-bottom: 24px;">'
                '<h4 style="color: #374151; margin: 0 0 12px 0; padding-bottom: 8px; '
                'border-bottom: 2px solid #e5e7eb;">👥 Permissões via Grupos</h4>'
            )
            
            for group in groups:
                group_perms = group.permissions.all()
                group_colors = {
                    'Administradores': '#dc2626',
                    'Terapeutas': '#059669',
                    'Gestores de Espaços': '#7c3aed',
                    'Editores de Conteúdo': '#2563eb'
                }
                color = group_colors.get(group.name, '#6b7280')
                
                html_parts.append(
                    '<div style="margin-bottom: 16px; padding: 12px; '
                    'background: {}; border-radius: 6px;">'.format(
                        '#f0f9ff' if color == '#2563eb' else
                        '#f0fdf4' if color == '#059669' else
                        '#faf5ff' if color == '#7c3aed' else
                        '#fef2f2'
                    )
                )
                
                html_parts.append(
                    '<div style="display: flex; align-items: center; margin-bottom: 8px;">'
                    '<span style="background-color: {}; color: white; padding: 4px 8px; '
                    'border-radius: 6px; font-size: 12px; font-weight: bold; margin-right: 8px;">{}</span>'
                    '<span style="color: #6b7280; font-size: 12px;">{} permissão(ões)</span>'
                    '</div>'.format(color, group.name, group_perms.count())
                )
                
                if group_perms.count() > 0:
                    html_parts.append('<div style="font-size: 11px; line-height: 1.4;">')
                    
                    # Agrupar permissões por app
                    perms_by_app = {}
                    for perm in group_perms:
                        app_name = perm.content_type.app_label
                        if app_name not in perms_by_app:
                            perms_by_app[app_name] = []
                        perms_by_app[app_name].append(perm)
                    
                    for app_name, perms in perms_by_app.items():
                        app_display = {
                            'terapeutas': '👨‍⚕️ Terapeutas',
                            'espacos': '🏢 Espaços',
                            'core': '⚙️ Core',
                            'auth': '🔐 Autenticação',
                            'admin': '🛠️ Admin'
                        }.get(app_name, app_name.title())
                        
                        html_parts.append(
                            '<strong style="color: {};">{}</strong>: '.format(color, app_display)
                        )
                        
                        perm_names = []
                        for perm in perms[:5]:  # Limitar a 5 para não sobrecarregar
                            perm_names.append(perm.name.replace('Can ', '').replace('Can view', 'Ver').replace('Can add', 'Criar').replace('Can change', 'Editar').replace('Can delete', 'Excluir'))
                        
                        html_parts.append(', '.join(perm_names))
                        if len(perms) > 5:
                            html_parts.append(f' e mais {len(perms) - 5}')
                        html_parts.append('<br>')
                    
                    html_parts.append('</div>')
                
                html_parts.append('</div>')
            
            html_parts.append('</div>')
        
        # Seção de permissões diretas
        if direct_permissions:
            html_parts.append(
                '<div style="margin-bottom: 16px;">'
                '<h4 style="color: #374151; margin: 0 0 12px 0; padding-bottom: 8px; '
                'border-bottom: 2px solid #e5e7eb;">📋 Permissões Individuais</h4>'
                '<div style="padding: 12px; background: #fef3f2; border-radius: 6px; '
                'border-left: 4px solid #f59e0b;">'
                '<p style="margin: 0 0 8px 0; color: #92400e; font-size: 12px; font-weight: bold;">'
                '⚠️ Atenção: Permissões individuais devem ser usadas apenas em casos específicos.'
                '</p>'
            )
            
            # Agrupar permissões diretas por app
            direct_by_app = {}
            for perm in direct_permissions:
                app_name = perm.content_type.app_label
                if app_name not in direct_by_app:
                    direct_by_app[app_name] = []
                direct_by_app[app_name].append(perm)
            
            for app_name, perms in direct_by_app.items():
                app_display = {
                    'terapeutas': '👨‍⚕️ Terapeutas',
                    'espacos': '🏢 Espaços', 
                    'core': '⚙️ Core',
                    'auth': '🔐 Autenticação'
                }.get(app_name, app_name.title())
                
                html_parts.append(
                    '<strong style="color: #92400e;">{}</strong>: '.format(app_display)
                )
                
                perm_names = [perm.name for perm in perms[:3]]
                html_parts.append(', '.join(perm_names))
                if len(perms) > 3:
                    html_parts.append(f' e mais {len(perms) - 3}')
                html_parts.append('<br>')
            
            html_parts.append('</div></div>')
        
        return format_html(
            '<div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; '
            'max-height: 400px; overflow-y: auto; padding: 16px; '
            'background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); '
            'border: 1px solid #e2e8f0; border-radius: 8px;">{}</div>',
            ''.join(html_parts)
        )
    
    permissions_summary_detailed.short_description = 'Permissões Detalhadas'
    
    def system_access_info(self, obj):
        """
        Informações sobre acesso ao sistema baseado nas permissões
        """
        if obj.is_superuser:
            html_content = '''
            <div style="padding: 16px; background: #fef2f2; border: 1px solid #fecaca; 
            border-radius: 8px;">
                <h4 style="color: #dc2626; margin: 0 0 12px 0;">🔥 Acesso de Superusuário</h4>
                <ul style="margin: 0; padding-left: 20px; color: #7f1d1d;">
                    <li>✅ Painel administrativo completo</li>
                    <li>✅ Gerenciar todos os usuários</li>
                    <li>✅ Configurar permissões e grupos</li>
                    <li>✅ Verificar e moderar terapeutas</li>
                    <li>✅ Gerenciar espaços terapêuticos</li>
                    <li>✅ Configurações do sistema</li>
                    <li>✅ Todas as funcionalidades futuras</li>
                </ul>
            </div>
            '''
            return format_html(html_content)
        
        groups = obj.groups.all()
        access_info = []
        
        for group in groups:
            if group.name == 'Administradores':
                access_info.append({
                    'title': '👑 Acesso de Administrador',
                    'color': '#dc2626',
                    'bg_color': '#fef2f2',
                    'items': [
                        '✅ Painel administrativo completo',
                        '✅ Gerenciar todos os terapeutas',
                        '✅ Verificar e aprovar perfis',
                        '✅ Gerenciar especialidades e cidades',
                        '✅ Configurar usuários e permissões',
                        '✅ Acesso a relatórios e métricas'
                    ]
                })
            elif group.name == 'Terapeutas':
                access_info.append({
                    'title': '👨‍⚕️ Acesso de Terapeuta',
                    'color': '#059669',
                    'bg_color': '#f0fdf4',
                    'items': [
                        '✅ Gerenciar seu próprio perfil',
                        '✅ Editar informações profissionais',
                        '✅ Visualizar suas avaliações',
                        '✅ Responder contatos recebidos',
                        '❌ Não pode verificar outros terapeutas',
                        '❌ Não pode gerenciar usuários'
                    ]
                })
            elif group.name == 'Gestores de Espaços':
                access_info.append({
                    'title': '🏢 Acesso de Gestor de Espaços',
                    'color': '#7c3aed',
                    'bg_color': '#faf5ff',
                    'items': [
                        '✅ Gerenciar espaços terapêuticos',
                        '✅ Visualizar terapeutas cadastrados',
                        '✅ Acessar informações de localização',
                        '❌ Não pode modificar terapeutas',
                        '❌ Não pode gerenciar usuários'
                    ]
                })
            elif group.name == 'Editores de Conteúdo':
                access_info.append({
                    'title': '📝 Acesso de Editor de Conteúdo',
                    'color': '#2563eb',
                    'bg_color': '#f0f9ff',
                    'items': [
                        '✅ Gerenciar FAQs e conteúdo',
                        '✅ Visualizar contatos dos usuários',
                        '✅ Acessar informações para conteúdo',
                        '❌ Não pode modificar terapeutas',
                        '❌ Não pode gerenciar usuários'
                    ]
                })
        
        if not access_info:
            html_content = '''
            <div style="padding: 16px; background: #f9fafb; border: 1px solid #e5e7eb; 
            border-radius: 8px; text-align: center;">
                <p style="color: #6b7280; margin: 0;">❌ Este usuário não tem acesso ao sistema administrativo.</p>
                <p style="color: #6b7280; margin: 8px 0 0 0; font-size: 12px;">
                Para dar acesso, atribua o usuário a um dos grupos disponíveis.
                </p>
            </div>
            '''
            return format_html(html_content)
        
        html_parts = []
        for info in access_info:
            html_parts.append(
                '<div style="margin-bottom: 16px; padding: 16px; background: {}; '
                'border-radius: 8px; border-left: 4px solid {};">'.format(
                    info['bg_color'], info['color']
                )
            )
            html_parts.append(
                '<h4 style="color: {}; margin: 0 0 12px 0;">{}</h4>'.format(
                    info['color'], info['title']
                )
            )
            html_parts.append('<ul style="margin: 0; padding-left: 20px; line-height: 1.6;">')
            for item in info['items']:
                html_parts.append('<li style="margin-bottom: 4px;">{}</li>'.format(item))
            html_parts.append('</ul></div>')
        
        final_html = '''
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
            {}
        </div>
        '''.format(''.join(html_parts))
        
        return format_html(final_html)
    
    system_access_info.short_description = 'Acesso ao Sistema'

# ===============================================================
# CUSTOMIZAÇÃO DO ADMIN DE GRUPOS  
# ===============================================================

class CustomGroupAdmin(GroupAdmin):
    """
    Admin customizado para grupos com descrições
    """
    list_display = ['name', 'description_display', 'users_count', 'permissions_count']
    search_fields = ['name']
    
    def description_display(self, obj):
        """
        Exibe descrição do grupo
        """
        descriptions = {
            'Administradores': 'Acesso total ao sistema - podem gerenciar tudo',
            'Terapeutas': 'Profissionais que podem gerenciar seus próprios perfis',
            'Gestores de Espaços': 'Responsáveis por espaços terapêuticos',
            'Editores de Conteúdo': 'Responsáveis pelo blog e conteúdo educativo'
        }
        
        description = descriptions.get(obj.name, '')
        if description:
            return format_html(
                '<span style="color: #6b7280; font-style: italic;">{}</span>',
                description
            )
        return '-'
    
    description_display.short_description = 'Descrição'
    
    def users_count(self, obj):
        """
        Conta usuários no grupo
        """
        count = obj.user_set.count()
        if count > 0:
            url = reverse('admin:auth_user_changelist') + f'?groups__id__exact={obj.id}'
            return format_html(
                '<a href="{}" style="color: #059669; font-weight: bold;">{} usuário(s)</a>',
                url, count
            )
        return format_html(
            '<span style="color: #6b7280;">0 usuários</span>'
        )
    
    users_count.short_description = 'Usuários'
    
    def permissions_count(self, obj):
        """
        Conta permissões do grupo
        """
        count = obj.permissions.count()
        return format_html(
            '<span style="color: #7c3aed; font-weight: bold;">{} permissão(ões)</span>',
            count
        )
    
    permissions_count.short_description = 'Permissões'

# ===============================================================
# ADMIN PARA MODELS DO CORE
# ===============================================================

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    Admin para formulários de contato
    """
    list_display = [
        'name', 'email', 'subject_display', 'status_display', 
        'created_at', 'has_response'
    ]
    list_filter = [
        'subject', 'status', CreatedDateFilter, 'responded_at'
    ]
    search_fields = [
        'name', 'email', 'message'
    ]
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    
    fieldsets = [
        ('Informações do Contato', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Mensagem', {
            'fields': ('subject', 'message')
        }),
        ('Status e Resposta', {
            'fields': ('status', 'responded_at', 'responded_by', 'internal_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    # Ações personalizadas
    actions = ['mark_as_resolved', 'mark_as_in_progress']
    
    def subject_display(self, obj):
        """
        Exibe o assunto com cor baseada no tipo
        """
        colors = {
            'general': '#6b7280',
            'therapist': '#059669',
            'space': '#7c3aed',
            'partnership': '#f59e0b',
            'support': '#ef4444',
            'complaint': '#dc2626',
            'suggestion': '#2563eb',
        }
        color = colors.get(obj.subject, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_subject_display()
        )
    subject_display.short_description = 'Assunto'
    
    def status_display(self, obj):
        """
        Status com cores
        """
        colors = {
            'pending': '#f59e0b',      # amarelo
            'in_progress': '#3b82f6',  # azul
            'resolved': '#10b981',     # verde
            'closed': '#6b7280',       # cinza
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def has_response(self, obj):
        """
        Indica se já foi respondido
        """
        if obj.responded_at:
            return format_html(
                '<span style="color: #10b981;">✓ Sim</span>'
            )
        return format_html(
            '<span style="color: #f59e0b;">⏳ Não</span>'
        )
    has_response.short_description = 'Respondido'
    
    def mark_as_resolved(self, request, queryset):
        """
        Marca mensagens como resolvidas
        """
        updated = queryset.update(
            status='resolved',
            responded_at=timezone.now(),
            responded_by=request.user
        )
        self.message_user(
            request, 
            f'{updated} mensagem(ns) marcada(s) como resolvida(s).'
        )
    mark_as_resolved.short_description = 'Marcar como resolvido'
    
    def mark_as_in_progress(self, request, queryset):
        """
        Marca mensagens como em andamento
        """
        updated = queryset.update(status='in_progress')
        self.message_user(
            request, 
            f'{updated} mensagem(ns) marcada(s) como em andamento.'
        )
    mark_as_in_progress.short_description = 'Marcar como em andamento'

# ===============================================================
# REGISTRAR APENAS OS ADMINS BÁSICOS (sem substituir)
# ===============================================================

# Desregistrar os admins padrão
admin.site.unregister(User)
admin.site.unregister(Group)

# Registrar os admins customizados
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)

# ===============================================================
# CONFIGURAÇÕES EXTRAS DO ADMIN
# ===============================================================

# Personalizar título do admin
admin.site.site_header = "Espaço Vital - Administração"
admin.site.site_title = "Espaço Vital Admin"
admin.site.index_title = "Painel de Controle"
admin.site.site_url = "/"  # Link para voltar ao site

# ===============================================================
# ADMINS DE LOCALIZAÇÃO
# ===============================================================

@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    """
    Admin para Países
    Sistema internacional de localização
    """
    list_display = ['nome', 'codigo', 'ddi', 'total_estados', 'ativo', 'created_at']
    list_filter = ['ativo']
    search_fields = ['nome', 'codigo', 'ddi']
    ordering = ['nome']
    list_editable = ['ativo']
    
    fieldsets = [
        ('Informações do País', {
            'fields': ('nome', 'codigo', 'ddi')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    ]
    
    def total_estados(self, obj):
        """Conta total de estados/províncias do país"""
        return obj.estados.count()
    total_estados.short_description = 'Estados/Províncias'

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    """
    Admin para Estados/Províncias
    Compartilhado entre todos os apps - Sistema Internacional
    """
    list_display = ['nome', 'sigla', 'pais', 'total_cidades', 'ativo', 'created_at']
    list_filter = ['pais', 'ativo']
    search_fields = ['nome', 'sigla', 'pais__nome']
    ordering = ['pais__nome', 'nome']
    list_editable = ['ativo']
    
    fieldsets = [
        ('Informações do Estado', {
            'fields': ('pais', 'nome', 'sigla'),
            'description': '''
                <strong>🗺️ Como cadastrar estados:</strong><br>
                • <strong>Brasil:</strong> Use siglas oficiais (RJ, SP, MG, etc.)<br>
                • <strong>EUA:</strong> Use siglas dos estados (CA, NY, FL, etc.)<br>
                • <strong>Portugal:</strong> Use distritos (Lisboa, Porto, Faro, etc.) ou crie um genérico "PT"<br>
                • <strong>Países pequenos sem estados:</strong> Crie um estado genérico com sigla do país (ex: "Uruguai" - "UY")
            '''
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    ]
    
    def total_cidades(self, obj):
        """Conta total de cidades do estado"""
        return obj.cidades.count()
    total_cidades.short_description = 'Cidades'

@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    """
    Admin para Cidades
    Compartilhado entre todos os apps - Sistema Internacional
    Com suporte para países sem estados
    """
    search_fields = ['nome', 'estado__nome', 'estado__sigla']
    list_display = ['nome', 'get_estado', 'get_pais', 'total_terapeutas', 'total_espacos', 'ativo', 'created_at']
    list_filter = ['estado__pais', 'estado', 'ativo']
    search_fields = ['nome', 'estado__nome', 'estado__sigla', 'estado__pais__nome']
    ordering = ['estado__pais__nome', 'estado__nome', 'nome']
    list_editable = ['ativo']
    
    fieldsets = [
        ('Informações da Cidade', {
            'fields': ('nome', 'estado'),
            'description': '''
                <strong>📍 Como cadastrar cidades:</strong><br>
                • <strong>Brasil e países com estados:</strong> Selecione o Estado<br>
                • <strong>Países sem estados:</strong> Primeiro crie um estado "genérico" para o país (ex: "Portugal - Lisboa" ou "Uruguai - Nacional")
            '''
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    ]
    
    def get_estado(self, obj):
        """Retorna estado com sigla"""
        return f'{obj.estado.nome} ({obj.estado.sigla})'
    get_estado.short_description = 'Estado'
    get_estado.admin_order_field = 'estado__nome'
    
    def get_pais(self, obj):
        """Retorna país"""
        return obj.estado.pais.nome
    get_pais.short_description = 'País'
    get_pais.admin_order_field = 'estado__pais__nome'
    
    def total_terapeutas(self, obj):
        """Conta terapeutas que atendem nesta cidade"""
        try:
            from terapeutas.models import Terapeuta
            return Terapeuta.objects.filter(
                Q(cidade_principal=obj) | Q(cidades_atendimento=obj),
                is_active=True
            ).distinct().count()
        except:
            return 0
    total_terapeutas.short_description = 'Terapeutas'
    
    def total_espacos(self, obj):
        """Conta espaços nesta cidade"""
        try:
            from espacos.models import Espaco
            return Espaco.objects.filter(
                cidade=obj,
                is_active=True
            ).count()
        except:
            return 0
    total_espacos.short_description = 'Espaços'

@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    """
    Título: Admin Especialidade/Terapia
    Descrição: Interface administrativa para gerenciar especialidades e terapias
    Autor: Will
    Data: Novembro 2025
    """
    # ===============================================================
    # Campos exibidos na listagem
    # ===============================================================
    list_display = [
        'nome', 
        'categoria', 
        'destaque', 
        'ordem', 
        'tem_foto',
        'tem_beneficios',
        'tem_conteudo_completo',  # NOVO
        'is_active'
    ]
    
    # ===============================================================
    # Filtros laterais
    # ===============================================================
    list_filter = ['destaque', 'is_active', 'categoria']
    
    # ===============================================================
    # Campos de busca
    # ===============================================================
    search_fields = ['nome', 'descricao_curta', 'descricao_completa']
    
    # ===============================================================
    # Slug automático
    # ===============================================================
    prepopulated_fields = {'slug': ('nome',)}
    
    # ===============================================================
    # Ordenação
    # ===============================================================
    ordering = ['-destaque', 'ordem', 'nome']
    
    # ===============================================================
    # Campos editáveis direto na listagem
    # ===============================================================
    list_editable = ['destaque', 'ordem']
    
    # ===============================================================
    # Organização dos campos no formulário
    # ===============================================================
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'categoria', 'foto', 'preview_foto')
        }),
        ('Descrições', {
            'fields': ('descricao_curta', 'descricao_completa', 'beneficios'),
            'description': 'Use a descrição curta para cards e a completa para a página individual'
        }),
        # ===============================================================
        # NOVO FIELDSET: Conteúdo Extenso
        # ===============================================================
        ('Conteúdo Extenso (Editor Rico)', {
            'fields': ('conteudo_completo',),
            'classes': ('wide',),
            'description': '''
                Use o editor para criar conteúdo estruturado com seções como:
                • Introdução
                • O que é a terapia
                • Em que a terapia pode ajudar
                • O que esperar numa sessão
                • O que sentirá após uma sessão
                • Quantas sessões são necessárias
                • Como escolher um terapeuta
            '''
        }),
        # ===============================================================
        # NOVO FIELDSET: Sites de Referência
        # ===============================================================
        ('Sites de Referência', {
            'fields': ('sites_referencia',),
            'classes': ('collapse',),
            'description': 'Adicione URLs de sites de referência sobre a terapia (uma por linha)'
        }),
        ('Configurações de Exibição', {
            'fields': ('cor_destaque', 'ordem', 'destaque', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    # ===============================================================
    # Preview da foto (somente leitura)
    # ===============================================================
    readonly_fields = ['preview_foto']
    
    # ===============================================================
    # Métodos customizados para listagem
    # ===============================================================
    @admin.display(boolean=True, description='Tem Foto?')
    def tem_foto(self, obj):
        """
        Indica se a especialidade tem foto cadastrada
        """
        return bool(obj.foto)
    
    @admin.display(boolean=True, description='Tem Benefícios?')
    def tem_beneficios(self, obj):
        """
        Indica se a especialidade tem benefícios cadastrados
        """
        return bool(obj.beneficios)
    
    # ===============================================================
    # NOVO MÉTODO: Indicador de conteúdo completo
    # ===============================================================
    @admin.display(boolean=True, description='Tem Conteúdo Completo?')
    def tem_conteudo_completo(self, obj):
        """
        Indica se a especialidade tem conteúdo completo cadastrado
        """
        return bool(obj.conteudo_completo)
    
    def preview_foto(self, obj):
        """
        Exibe preview da foto no formulário de edição
        """
        if obj.foto:
            from django.utils.html import format_html
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.foto.url
            )
        return "Nenhuma foto cadastrada"
    preview_foto.short_description = "Preview da Foto"