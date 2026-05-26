"""
Título: Widgets Customizados - Espaços
Descrição: Widgets personalizados para formulários do app Espaços
Autor: Will
Data: 26/10/2025
"""

from django import forms
from django.utils.safestring import mark_safe
import json


class HorariosSemanaWidget(forms.Textarea):
    """
    Widget customizado para gerenciar horários da semana
    Interface inspirada no WhatsApp Business
    """
    
    template_name = 'django/forms/widgets/textarea.html'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'horarios-widget-input',
            'rows': 1,
            'style': 'display:none;'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
        
        self.dias_semana = [
            ('domingo', 'Domingo'),
            ('segunda', 'Segunda-feira'),
            ('terca', 'Terça-feira'),
            ('quarta', 'Quarta-feira'),
            ('quinta', 'Quinta-feira'),
            ('sexta', 'Sexta-feira'),
            ('sabado', 'Sábado'),
        ]
    
    class Media:
        css = {
            'all': ('admin/css/horarios_widget.css',)
        }
        js = ('admin/js/horarios_widget.js',)
    
    def render(self, name, value, attrs=None, renderer=None):
        """
        Renderiza o widget
        """
        # Renderiza o textarea hidden
        textarea_html = super().render(name, value, attrs, renderer)
        
        # Processa o valor
        if value is None or value == '':
            value = {}
        elif isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = {}
        
        # HTML do widget customizado
        html_parts = [textarea_html]
        html_parts.append('<div class="horarios-widget" id="horarios-widget" data-field-name="' + name + '">')
        html_parts.append('<div class="horarios-dias-list">')
        
        for dia_key, dia_nome in self.dias_semana:
            tem_horario = dia_key in value and value[dia_key]
            horarios_texto = ''
            
            if tem_horario:
                periodos = value[dia_key]
                horarios_list = []
                for periodo in periodos:
                    inicio = periodo.get('inicio', '')
                    fim = periodo.get('fim', '')
                    if inicio and fim:
                        horarios_list.append(f"{inicio} - {fim}")
                horarios_texto = ' e '.join(horarios_list) if horarios_list else 'Clique para definir horários'
            else:
                horarios_texto = 'Fechado'
            
            checked = 'checked' if tem_horario else ''
            disabled = '' if tem_horario else 'disabled'
            
            html_parts.append(f'''
                <div class="horario-dia-item" data-dia="{dia_key}">
                    <div class="horario-dia-toggle">
                        <label>
                            <input type="checkbox" class="dia-checkbox" data-dia="{dia_key}" {checked}>
                            <span class="toggle-switch"></span>
                        </label>
                    </div>
                    <div class="horario-dia-info">
                        <div class="horario-dia-nome">{dia_nome}</div>
                        <div class="horario-dia-horarios">{horarios_texto}</div>
                    </div>
                    <button type="button" class="horario-edit-btn" data-dia="{dia_key}" {disabled}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M9 5l7 7-7 7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            ''')
        
        html_parts.append('</div>')  # fecha horarios-dias-list
        html_parts.append('</div>')  # fecha horarios-widget
        
        return mark_safe(''.join(html_parts))