/**
 * Título: JavaScript Admin - Máscara de Telefone e Ícones de Redes Sociais
 * Descrição: Aplica máscara automática no campo WhatsApp formato (xx) xxxxx-xxxx
 * Autor: Will
 * Data: 26/10/2025
 */

(function() {
    'use strict';

    // Aguarda o DOM carregar completamente
    document.addEventListener('DOMContentLoaded', function() {
        
        // === MÁSCARA DE TELEFONE ===
        const whatsappField = document.getElementById('id_whatsapp');
        
        if (whatsappField) {
            // Aplica máscara ao digitar
            whatsappField.addEventListener('input', function(e) {
                let value = e.target.value;
                
                // Remove tudo que não é número
                value = value.replace(/\D/g, '');
                
                // Aplica a máscara (xx) xxxxx-xxxx ou (xx) xxxx-xxxx
                if (value.length <= 10) {
                    // Telefone fixo: (xx) xxxx-xxxx
                    value = value.replace(/^(\d{2})(\d{4})(\d{0,4}).*/, '($1) $2-$3');
                } else {
                    // Celular: (xx) xxxxx-xxxx
                    value = value.replace(/^(\d{2})(\d{5})(\d{0,4}).*/, '($1) $2-$3');
                }
                
                e.target.value = value;
            });
            
            // Remove máscara ao submeter o formulário (envia só números)
            const form = whatsappField.closest('form');
            if (form) {
                form.addEventListener('submit', function() {
                    // Remove tudo que não é número antes de enviar
                    whatsappField.value = whatsappField.value.replace(/\D/g, '');
                });
            }
            
            // Aplica máscara inicial se já houver valor
            if (whatsappField.value) {
                const event = new Event('input', { bubbles: true });
                whatsappField.dispatchEvent(event);
            }
        }
        
        
        // === ÍCONES NAS REDES SOCIAIS ===
        addIconToField('id_instagram', 'fab fa-instagram', '#E4405F');
        addIconToField('id_facebook', 'fab fa-facebook', '#1877F2');
        addIconToField('id_youtube', 'fab fa-youtube', '#FF0000');
        addIconToField('id_tiktok', 'fab fa-tiktok', '#000000');
        
        
        /**
         * Adiciona ícone ao lado do campo
         */
        function addIconToField(fieldId, iconClass, color) {
            const field = document.getElementById(fieldId);
            
            if (field) {
                // Cria container do ícone
                const iconSpan = document.createElement('span');
                iconSpan.style.cssText = `
                    display: inline-block;
                    margin-left: 10px;
                    font-size: 20px;
                    color: ${color};
                    vertical-align: middle;
                `;
                
                // Cria o ícone
                const icon = document.createElement('i');
                icon.className = iconClass;
                iconSpan.appendChild(icon);
                
                // Insere o ícone após o campo
                field.parentNode.insertBefore(iconSpan, field.nextSibling);
            }
        }
        
    });
})();