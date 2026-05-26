/**
 * Título: JavaScript Widget de Horários - Versão Simples
 * Descrição: Transforma textarea JSON em interface visual
 * Autor: Will
 * Data: 26/10/2025
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Procura o campo horarios_semana
        const $textarea = $('#id_horarios_semana');
        if (!$textarea.length) return;
        
        // Esconde o textarea
        $textarea.hide();
        
        // Cria a interface visual
        const $widget = createWidget();
        $textarea.after($widget);
        
        // Carrega dados iniciais
        loadData();
    });
    
    function createWidget() {
        const dias = [
            ['domingo', 'Domingo'],
            ['segunda', 'Segunda-feira'],
            ['terca', 'Terça-feira'],
            ['quarta', 'Quarta-feira'],
            ['quinta', 'Quinta-feira'],
            ['sexta', 'Sexta-feira'],
            ['sabado', 'Sábado']
        ];
        
        let html = '<div class="horarios-widget-visual">';
        
        dias.forEach(([key, nome]) => {
            html += `
                <div class="horario-row" data-dia="${key}">
                    <label>
                        <input type="checkbox" class="dia-toggle" data-dia="${key}">
                        <strong>${nome}</strong>
                    </label>
                    <div class="horario-inputs" style="display:none;">
                        <input type="time" class="hora-inicio" value="09:00">
                        <span>às</span>
                        <input type="time" class="hora-fim" value="18:00">
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        const $widget = $(html);
        
        // Event handlers
        $widget.find('.dia-toggle').on('change', function() {
            const $row = $(this).closest('.horario-row');
            const $inputs = $row.find('.horario-inputs');
            
            if ($(this).is(':checked')) {
                $inputs.show();
            } else {
                $inputs.hide();
            }
            
            saveData();
        });
        
        $widget.find('input[type="time"]').on('change', saveData);
        
        return $widget;
    }
    
    function loadData() {
        const $textarea = $('#id_horarios_semana');
        let data = {};
        
        try {
            const value = $textarea.val();
            if (value) {
                data = JSON.parse(value);
            }
        } catch (e) {
            console.error('Erro ao parsear JSON:', e);
        }
        
        // Preenche a interface
        Object.keys(data).forEach(dia => {
            const periodos = data[dia];
            if (periodos && periodos.length > 0) {
                const periodo = periodos[0]; // Pega o primeiro período
                const $row = $(`.horario-row[data-dia="${dia}"]`);
                
                $row.find('.dia-toggle').prop('checked', true);
                $row.find('.horario-inputs').show();
                $row.find('.hora-inicio').val(periodo.inicio || '09:00');
                $row.find('.hora-fim').val(periodo.fim || '18:00');
            }
        });
    }
    
    function saveData() {
        const data = {};
        
        $('.horario-row').each(function() {
            const dia = $(this).data('dia');
            const isChecked = $(this).find('.dia-toggle').is(':checked');
            
            if (isChecked) {
                const inicio = $(this).find('.hora-inicio').val();
                const fim = $(this).find('.hora-fim').val();
                
                data[dia] = [{
                    inicio: inicio,
                    fim: fim
                }];
            }
        });
        
        $('#id_horarios_semana').val(JSON.stringify(data));
    }
    
})(django.jQuery);