// ===============================================================
// Título: JavaScript - Múltiplas Cidades Terapeuta
// Descrição: Funcionalidade do botão + para adicionar cidades
// Autor: Will | Empresa: Espaço Vital
// Data: 28/09/2025
// Arquivo: backend/static/js/multiplas_cidades.js
// ===============================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // Container onde ficam os campos de cidade
    const cidadesContainer = document.getElementById('cidades-container');
    const btnAdicionarCidade = document.getElementById('btn-adicionar-cidade');
    let contadorCidades = 1; // Começa com 1 (cidade principal)
    
    /**
     * Adiciona um novo campo de cidade
     */
    function adicionarCampoCity() {
        contadorCidades++;
        
        // HTML do novo campo de cidade
        const novoCampo = `
            <div class="cidade-adicional flex items-center space-x-3 mt-3" data-cidade="${contadorCidades}">
                <!-- Select de Estado -->
                <div class="flex-1">
                    <select name="estado_adicional_${contadorCidades}" 
                            class="estado-select w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent"
                            onchange="carregarCidadesPorEstado(this, ${contadorCidades})">
                        <option value="">Selecione o Estado</option>
                        ${getOpcoesEstados()}
                    </select>
                </div>
                
                <!-- Select de Cidade -->
                <div class="flex-1">
                    <select name="cidade_adicional_${contadorCidades}" 
                            class="cidade-select w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled>
                        <option value="">Primeiro selecione o estado</option>
                    </select>
                </div>
                
                <!-- Botão Remover -->
                <button type="button" 
                        class="btn-remover-cidade bg-red-500 hover:bg-red-600 text-white px-3 py-3 rounded-lg transition-colors"
                        onclick="removerCampoCity(${contadorCidades})"
                        title="Remover cidade">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        // Inserir antes do botão "+"
        btnAdicionarCidade.insertAdjacentHTML('beforebegin', novoCampo);
        
        // Limitar máximo de 5 cidades adicionais
        if (contadorCidades >= 6) {
            btnAdicionarCidade.style.display = 'none';
        }
        
        // Animação smooth
        const novoCampoElement = document.querySelector(`[data-cidade="${contadorCidades}"]`);
        novoCampoElement.style.opacity = '0';
        novoCampoElement.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            novoCampoElement.style.transition = 'all 0.3s ease';
            novoCampoElement.style.opacity = '1';
            novoCampoElement.style.transform = 'translateY(0)';
        }, 10);
    }
    
    /**
     * Remove um campo de cidade
     */
    window.removerCampoCity = function(numeroCidade) {
        const campoParaRemover = document.querySelector(`[data-cidade="${numeroCidade}"]`);
        
        if (campoParaRemover) {
            // Animação de saída
            campoParaRemover.style.transition = 'all 0.3s ease';
            campoParaRemover.style.opacity = '0';
            campoParaRemover.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                campoParaRemover.remove();
                
                // Mostrar botão + se estava escondido
                if (btnAdicionarCidade.style.display === 'none') {
                    btnAdicionarCidade.style.display = 'flex';
                }
            }, 300);
        }
    }
    
    /**
     * Carrega cidades quando estado é selecionado
     */
    window.carregarCidadesPorEstado = function(selectEstado, numeroCidade) {
        const estadoId = selectEstado.value;
        const selectCidade = document.querySelector(`select[name="cidade_adicional_${numeroCidade}"]`);
        
        if (!estadoId) {
            selectCidade.innerHTML = '<option value="">Primeiro selecione o estado</option>';
            selectCidade.disabled = true;
            return;
        }
        
        // Loading state
        selectCidade.innerHTML = '<option value="">Carregando cidades...</option>';
        selectCidade.disabled = true;
        
        // AJAX para buscar cidades
        fetch(`/terapeutas/api/cidades-por-estado/?estado_id=${estadoId}`)
            .then(response => response.json())
            .then(data => {
                let opcoesCidades = '<option value="">Selecione a cidade</option>';
                
                data.cidades.forEach(cidade => {
                    opcoesCidades += `<option value="${cidade.id}">${cidade.nome}</option>`;
                });
                
                selectCidade.innerHTML = opcoesCidades;
                selectCidade.disabled = false;
            })
            .catch(error => {
                console.error('Erro ao carregar cidades:', error);
                selectCidade.innerHTML = '<option value="">Erro ao carregar cidades</option>';
            });
    }
    
    /**
     * Gera opções de estados (deve ser populado com dados do backend)
     */
    function getOpcoesEstados() {
        // Este será populado dinamicamente pelo Django no template
        return window.estadosOptions || '';
    }
    
    /**
     * Event listener do botão +
     */
    if (btnAdicionarCidade) {
        btnAdicionarCidade.addEventListener('click', adicionarCampoCity);
    }
    
    /**
     * Validação antes do submit
     */
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const cidadePrincipal = document.querySelector('select[name="cidade_principal"]').value;
            
            if (!cidadePrincipal) {
                e.preventDefault();
                alert('Por favor, selecione pelo menos a cidade principal.');
                return false;
            }
            
            // Verificar cidades duplicadas
            const cidadesSelecionadas = [cidadePrincipal];
            const cidadesAdicionais = document.querySelectorAll('select[name^="cidade_adicional_"]');
            
            for (let select of cidadesAdicionais) {
                if (select.value) {
                    if (cidadesSelecionadas.includes(select.value)) {
                        e.preventDefault();
                        alert('Não é possível selecionar a mesma cidade mais de uma vez.');
                        return false;
                    }
                    cidadesSelecionadas.push(select.value);
                }
            }
        });
    }
    
});