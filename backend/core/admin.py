# ===============================================================
# Título: Admin do App Core - Espaço Vital (Versão Corrigida)
# Descrição: Interface administrativa para modelos do core
# Autor: Will
# Data: 07/09/2025
# ===============================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from django.contrib.admin import SimpleListFilter
from .models import Contact, Newsletter, FAQ, SiteConfiguration


# ===============================================================
# FILTROS PERSONALIZADOS
# ===============================================================

class CreatedDateFilter(SimpleListFilter):
    """
    Filtro personalizado para data de criação
    """
    title = 'Data de Criação'
    parameter_name = 'created_date'
    
    def lookups(self, request, model_admin):
        return [
            ('today', 'Hoje'),
            ('week', 'Última semana'),
            ('month', 'Último mês'),
            ('year', 'Último ano'),
        ]
    
    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(created_at__date=now.date())
        elif self.value() == 'week':
            return queryset.filter(created_at__gte=now - timezone.timedelta(days=7))
        elif self.value() == 'month':
            return queryset.filter(created_at__gte=now - timezone.timedelta(days=30))
        elif self.value() == 'year':
            return queryset.filter(created_at__gte=now - timezone.timedelta(days=365))
        return queryset


# ===============================================================
# ADMINS DOS MODELOS
# ===============================================================

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    Admin para modelo Contact
    """
    list_display = [
        'name', 'email', 'subject_display', 'status_display', 
        'created_at', 'has_response'
    ]
    list_filter = [
        'status', 'subject', CreatedDateFilter, 'responded_at'
    ]
    search_fields = [
        'name', 'email', 'message'
    ]
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    fieldsets = [
        ('Informações do Contato', {
            'fields': ('name', 'email', 'phone', 'subject')
        }),
        ('Mensagem', {
            'fields': ('message',)
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
    
    # Configurações da lista
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def subject_display(self, obj):
        """
        Exibe o assunto com cor baseada no tipo
        """
        colors = {
            'general': 'blue',
            'therapist': 'green',
            'space': 'purple',
            'partnership': 'orange',
            'support': 'red',
            'complaint': 'darkred',
            'suggestion': 'teal',
        }
        color = colors.get(obj.subject, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_subject_display()
        )
    subject_display.short_description = 'Assunto'
    
    def status_display(self, obj):
        """
        Exibe o status com badge colorido
        """
        colors = {
            'pending': '#fbbf24',      # amarelo
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
                '<span style="color: green;">✓ Sim</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Não</span>'
        )
    has_response.short_description = 'Respondido'
    
    def mark_as_resolved(self, request, queryset):
        """
        Ação para marcar como resolvido
        """
        updated = queryset.update(
            status='resolved',
            responded_at=timezone.now(),
            responded_by=request.user
        )
        self.message_user(
            request, 
            f'{updated} contato(s) marcado(s) como resolvido(s).'
        )
    mark_as_resolved.short_description = 'Marcar como resolvido'
    
    def mark_as_in_progress(self, request, queryset):
        """
        Ação para marcar como em andamento
        """
        updated = queryset.update(status='in_progress')
        self.message_user(
            request, 
            f'{updated} contato(s) marcado(s) como em andamento.'
        )
    mark_as_in_progress.short_description = 'Marcar como em andamento'


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """
    Admin para modelo Newsletter
    """
    list_display = [
        'email', 'name', 'is_active_display', 'confirmed_display', 
        'source', 'created_at'
    ]
    list_filter = [
        'is_active', 'confirmed_at', 'source', CreatedDateFilter
    ]
    search_fields = [
        'email', 'name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'confirmed_at', 'unsubscribed_at'
    ]
    
    # Ações personalizadas
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def is_active_display(self, obj):
        """
        Exibe status ativo/inativo com cores
        """
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Ativo</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inativo</span>'
        )
    is_active_display.short_description = 'Status'
    
    def confirmed_display(self, obj):
        """
        Exibe se o e-mail foi confirmado
        """
        if obj.confirmed_at:
            return format_html(
                '<span style="color: green;">✓ Confirmado</span>'
            )
        return format_html(
            '<span style="color: orange;">⏳ Pendente</span>'
        )
    confirmed_display.short_description = 'Confirmado'
    
    def activate_subscriptions(self, request, queryset):
        """
        Ativa inscrições selecionadas
        """
        updated = queryset.update(is_active=True, unsubscribed_at=None)
        self.message_user(
            request, 
            f'{updated} inscrição(ões) ativada(s).'
        )
    activate_subscriptions.short_description = 'Ativar inscrições'
    
    def deactivate_subscriptions(self, request, queryset):
        """
        Desativa inscrições selecionadas
        """
        updated = queryset.update(
            is_active=False, 
            unsubscribed_at=timezone.now()
        )
        self.message_user(
            request, 
            f'{updated} inscrição(ões) desativada(s).'
        )
    deactivate_subscriptions.short_description = 'Desativar inscrições'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """
    Admin para modelo FAQ
    """
    list_display = [
        'question_short', 'category_display', 'is_active', 
        'order', 'views_count', 'helpful_count'
    ]
    list_filter = [
        'category', 'is_active', CreatedDateFilter
    ]
    search_fields = [
        'question', 'answer'
    ]
    list_editable = [
        'order', 'is_active'
    ]
    
    fieldsets = [
        ('Pergunta e Resposta', {
            'fields': ('question', 'answer', 'category')
        }),
        ('Configurações', {
            'fields': ('is_active', 'order')
        }),
        ('Estatísticas', {
            'fields': ('views_count', 'helpful_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def question_short(self, obj):
        """
        Exibe pergunta truncada
        """
        if len(obj.question) > 60:
            return f'{obj.question[:60]}...'
        return obj.question
    question_short.short_description = 'Pergunta'
    
    def category_display(self, obj):
        """
        Exibe categoria com cor
        """
        colors = {
            'general': '#6b7280',
            'therapists': '#10b981',
            'clients': '#3b82f6',
            'spaces': '#8b5cf6',
            'payments': '#f59e0b',
            'technical': '#ef4444',
        }
        color = colors.get(obj.category, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_category_display()
        )
    category_display.short_description = 'Categoria'


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """
    Admin para configurações do site
    """
    fieldsets = [
        ('Informações Básicas', {
            'fields': ('site_name', 'site_description')
        }),
        ('Contato', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Manutenção', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
        ('Analytics', {
            'fields': ('google_analytics_id', 'facebook_pixel_id'),
            'classes': ('collapse',)
        }),
        ('Última Atualização', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    ]
    
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        """
        Impede criar mais de uma configuração
        """
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """
        Impede deletar a configuração
        """
        return False