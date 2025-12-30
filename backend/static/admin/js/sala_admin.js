/**
 * Título: JavaScript para Admin de Salas
 * Descrição: Atualiza lista de comodidades dinamicamente baseado no espaço selecionado
 * Autor: Will
 * Data: 29/12/2024
 */

// Função para atualizar comodidades quando o espaço é alterado
function updateComodidades(espacoId, keepSelected = false) {
    if (!espacoId) {
        // Se não tem espaço selecionado, limpa as comodidades
        const comodidadesSelect = document.querySelector('[name="comodidades"]');
        if (comodidadesSelect) {
            comodidadesSelect.innerHTML = '<option value="">Selecione um espaço primeiro</option>';
        }
        return;
    }
    
    // Guarda as comodidades selecionadas antes de atualizar (se estiver editando)
    const comodidadesSelect = document.querySelector('[name="comodidades"]');
    let selectedValues = [];
    
    if (keepSelected && comodidadesSelect) {
        selectedValues = Array.from(comodidadesSelect.selectedOptions).map(opt => opt.value);
    }
    
    // Faz requisição AJAX para buscar comodidades do espaço
    fetch(`/agendamentos/sala/get-comodidades/?espaco_id=${espacoId}`)
        .then(response => response.json())
        .then(data => {
            if (comodidadesSelect) {
                // Limpa opções atuais
                comodidadesSelect.innerHTML = '';
                
                // Adiciona novas opções
                data.comodidades.forEach(comodidade => {
                    const option = document.createElement('option');
                    option.value = comodidade.id;
                    option.text = comodidade.nome;
                    
                    // Marca como selecionada se estava antes
                    if (selectedValues.includes(String(comodidade.id))) {
                        option.selected = true;
                    }
                    
                    comodidadesSelect.appendChild(option);
                });
                
                // Se não tem comodidades
                if (data.comodidades.length === 0) {
                    comodidadesSelect.innerHTML = '<option value="">Este espaço não possui comodidades cadastradas</option>';
                }
            }
        })
        .catch(error => {
            console.error('Erro ao buscar comodidades:', error);
        });
}

// Aguarda o carregamento da página
document.addEventListener('DOMContentLoaded', function() {
    const espacoSelect = document.querySelector('[name="espaco"]');
    
    if (espacoSelect) {
        // Dispara atualização ao carregar se já tem espaço selecionado
        // keepSelected=true para manter as comodidades já selecionadas ao editar
        if (espacoSelect.value) {
            updateComodidades(espacoSelect.value, true);
        }
    }
});