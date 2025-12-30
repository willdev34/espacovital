from django.contrib import admin

# Register your models here.
"""
Título: Admin do Sistema de Agendamento de Salas
Descrição: Configuração do Django Admin para gerenciar Salas, Agendamentos, Multas e PIX
Autor: Will
Data: 29/12/2024
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from .models import Sala, Agendamento, Multa, PIXConfig


# ==========================================
# FORMS CUSTOMIZADOS
# ==========================================
class SalaAdminForm(forms.ModelForm):
    """
    Form customizado para filtrar comodidades baseado no espaço selecionado
    """
    
    class Meta:
        model = Sala
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se já existe uma sala (editando), filtra comodidades do espaço
        if self.instance and self.instance.pk and self.instance.espaco:
            self.fields['comodidades'].queryset = self.instance.espaco.comodidades.all()
        
        # Se está criando nova sala mas já selecionou espaço via GET
        elif 'espaco' in self.data:
            try:
                espaco_id = int(self.data.get('espaco'))
                from espacos.models import Espaco
                espaco = Espaco.objects.get(pk=espaco_id)
                self.fields['comodidades'].queryset = espaco.comodidades.all()
            except (ValueError, TypeError, Espaco.DoesNotExist):
                pass
        else:
            # Se não tem espaço selecionado, não mostra comodidades
            self.fields['comodidades'].queryset = self.fields['comodidades'].queryset.none()
        
        # Adiciona classe CSS e widget customizado
        self.fields['comodidades'].widget.attrs.update({
            'class': 'comodidades-selector',
            'size': '10'
        })
        
        # Adiciona JavaScript para atualizar comodidades ao mudar espaço
        self.fields['espaco'].widget.attrs.update({
            'onchange': 'updateComodidades(this.value)'
        })

# ==========================================
# ADMIN: SALA
# ==========================================
@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    """
    Admin para gerenciar salas/salões dos espaços terapêuticos.
    """
    form = SalaAdminForm
    
    list_display = [
        'nome',
        'espaco',
        'capacidade',
        'valor_sessao_formatted',
        'duracao_sessao',
        'horario_abertura',
        'horario_fechamento',
        'status_badge',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'espaco',
        'duracao_sessao',
        'created_at'
    ]
    
    search_fields = [
        'nome',
        'espaco__nome_fantasia',
        'espaco__razao_social'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'preview_foto'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('espaco', 'nome', 'capacidade', 'foto', 'preview_foto')
        }),
        ('Configurações Financeiras', {
            'fields': ('valor_sessao',)
        }),
        ('Configurações de Tempo', {
            'fields': ('duracao_sessao', 'horario_abertura', 'horario_fechamento')
        }),
        ('Comodidades', {
            'fields': ('comodidades',),
            'description': 'Configure as comodidades disponíveis na sala (JSON format)'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    class Media:
        js = ('admin/js/sala_admin.js',)
    
    def valor_sessao_formatted(self, obj):
        """Formata o valor da sessão em reais"""
        return f"R$ {obj.valor_sessao:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    valor_sessao_formatted.short_description = 'Valor/Sessão'
    
    def status_badge(self, obj):
        """Exibe badge colorido para o status da sala"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #56C596; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">ATIVA</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">INATIVA</span>'
        )
    status_badge.short_description = 'Status'
    
    def preview_foto(self, obj):
        """Preview da foto da sala"""
        if obj.foto:
            return mark_safe(f'<img src="{obj.foto.url}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />')
        return "Sem foto"
    preview_foto.short_description = 'Preview da Foto'


# ==========================================
# ADMIN: AGENDAMENTO
# ==========================================
@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    """
    Admin para gerenciar agendamentos de salas.
    """
    
    list_display = [
        'data',
        'hora_inicio',
        'hora_fim',
        'sala',
        'terapeuta',
        'espaco',
        'valor_cobrado_formatted',
        'status_badge',
        'pagamento_badge',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'pago',
        'data',
        'espaco',
        'sala',
        'created_at'
    ]
    
    search_fields = [
        'sala__nome',
        'terapeuta__nome_completo',
        'terapeuta__user__email',
        'espaco__nome_fantasia',
        'observacoes'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'data'
    
    fieldsets = (
        ('Agendamento', {
            'fields': ('sala', 'terapeuta', 'espaco', 'data', 'hora_inicio', 'hora_fim')
        }),
        ('Financeiro', {
            'fields': ('valor_cobrado', 'pago', 'data_pagamento')
        }),
        ('Status e Observações', {
            'fields': ('status', 'observacoes')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['marcar_como_pago', 'marcar_como_confirmado', 'marcar_como_concluido']
    
    def valor_cobrado_formatted(self, obj):
        """Formata o valor cobrado em reais"""
        return f"R$ {obj.valor_cobrado:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    valor_cobrado_formatted.short_description = 'Valor'
    
    def status_badge(self, obj):
        """Exibe badge colorido para o status do agendamento"""
        colors = {
            'PENDENTE': '#ffc107',
            'CONFIRMADO': '#17a2b8',
            'CANCELADO': '#dc3545',
            'CONCLUIDO': '#56C596'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def pagamento_badge(self, obj):
        """Exibe badge colorido para o status de pagamento"""
        if obj.pago:
            return format_html(
                '<span style="background-color: #56C596; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ PAGO</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">⏳ PENDENTE</span>'
        )
    pagamento_badge.short_description = 'Pagamento'
    
    # Actions personalizadas
    def marcar_como_pago(self, request, queryset):
        """Marca agendamentos selecionados como pagos"""
        from django.utils import timezone
        updated = queryset.update(pago=True, data_pagamento=timezone.now())
        self.message_user(request, f'{updated} agendamento(s) marcado(s) como pago(s).')
    marcar_como_pago.short_description = "✓ Marcar como PAGO"
    
    def marcar_como_confirmado(self, request, queryset):
        """Marca agendamentos selecionados como confirmados"""
        updated = queryset.update(status='CONFIRMADO')
        self.message_user(request, f'{updated} agendamento(s) confirmado(s).')
    marcar_como_confirmado.short_description = "✓ Marcar como CONFIRMADO"
    
    def marcar_como_concluido(self, request, queryset):
        """Marca agendamentos selecionados como concluídos"""
        updated = queryset.update(status='CONCLUIDO')
        self.message_user(request, f'{updated} agendamento(s) marcado(s) como concluído(s).')
    marcar_como_concluido.short_description = "✓ Marcar como CONCLUÍDO"


# ==========================================
# ADMIN: MULTA
# ==========================================
@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    """
    Admin para gerenciar multas aplicadas aos terapeutas.
    """
    
    list_display = [
        'data_aplicacao',
        'terapeuta',
        'espaco',
        'motivo',
        'valor_formatted',
        'pagamento_badge',
        'agendamento'
    ]
    
    list_filter = [
        'pago',
        'espaco',
        'data_aplicacao',
        'created_at'
    ]
    
    search_fields = [
        'terapeuta__nome_completo',
        'espaco__nome_fantasia',
        'motivo',
        'agendamento__sala__nome'
    ]
    
    readonly_fields = [
        'data_aplicacao',
        'created_at',
        'updated_at',
        'preview_foto_evidencia'
    ]
    
    date_hierarchy = 'data_aplicacao'
    
    fieldsets = (
        ('Multa', {
            'fields': ('agendamento', 'terapeuta', 'espaco', 'motivo', 'valor')
        }),
        ('Evidência', {
            'fields': ('foto_evidencia', 'preview_foto_evidencia')
        }),
        ('Pagamento', {
            'fields': ('pago', 'data_pagamento')
        }),
        ('Metadados', {
            'fields': ('data_aplicacao', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['marcar_como_pago']
    
    def valor_formatted(self, obj):
        """Formata o valor da multa em reais"""
        return f"R$ {obj.valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    valor_formatted.short_description = 'Valor'
    
    def pagamento_badge(self, obj):
        """Exibe badge colorido para o status de pagamento da multa"""
        if obj.pago:
            return format_html(
                '<span style="background-color: #56C596; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ PAGO</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">⏳ PENDENTE</span>'
        )
    pagamento_badge.short_description = 'Pagamento'
    
    def preview_foto_evidencia(self, obj):
        """Preview da foto de evidência"""
        if obj.foto_evidencia:
            return mark_safe(f'<img src="{obj.foto_evidencia.url}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />')
        return "Sem foto de evidência"
    preview_foto_evidencia.short_description = 'Preview da Evidência'
    
    # Action personalizada
    def marcar_como_pago(self, request, queryset):
        """Marca multas selecionadas como pagas"""
        from django.utils import timezone
        updated = queryset.update(pago=True, data_pagamento=timezone.now())
        self.message_user(request, f'{updated} multa(s) marcada(s) como paga(s).')
    marcar_como_pago.short_description = "✓ Marcar como PAGO"


# ==========================================
# ADMIN: CONFIGURAÇÃO PIX
# ==========================================
@admin.register(PIXConfig)
class PIXConfigAdmin(admin.ModelAdmin):
    """
    Admin para gerenciar configurações de chave PIX dos espaços.
    """
    
    list_display = [
        'espaco',
        'tipo_chave',
        'chave_pix',
        'nome_recebedor',
        'status_badge',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'tipo_chave',
        'created_at'
    ]
    
    search_fields = [
        'espaco__nome_fantasia',
        'chave_pix',
        'nome_recebedor'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Espaço', {
            'fields': ('espaco',)
        }),
        ('Configuração PIX', {
            'fields': ('tipo_chave', 'chave_pix', 'nome_recebedor')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        """Exibe badge colorido para o status da configuração PIX"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #56C596; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">ATIVA</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">INATIVA</span>'
        )
    status_badge.short_description = 'Status'