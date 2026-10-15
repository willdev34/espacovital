# ===============================================================
# Título: Teste de Configuração das Permissões dos Grupos
# Descrição: Garante que toda permissão citada em GROUPS_CONFIG e em
#            PERMISSIONS_TRANSLATION aponta para um modelo que existe
#            no app indicado. Evita o erro "permissão não encontrada"
#            quando um modelo muda de app (ex.: Especialidade, Cidade
#            e Estado, que hoje vivem em core).
# Autor: Will
# Data: 2026-10-15
# ===============================================================

import pytest
from django.apps import apps

from core.permissions import GROUPS_CONFIG, PERMISSIONS_TRANSLATION


# ---------------------------------------------------------------
# Separa "app.acao_modelo" em (app, acao, modelo).
# Ex.: "core.view_cidade" -> ("core", "view", "cidade")
# ---------------------------------------------------------------
def _quebrar_permissao(permissao):
    app_label, codename = permissao.split('.', 1)
    acao, modelo = codename.split('_', 1)
    return app_label, acao, modelo


# ---------------------------------------------------------------
# Junta todas as permissões usadas nos grupos e na tradução,
# sem repetição, para o teste rodar uma vez por permissão.
# ---------------------------------------------------------------
def _todas_as_permissoes():
    usadas = set(PERMISSIONS_TRANSLATION)
    for config in GROUPS_CONFIG.values():
        usadas.update(config['permissions'])
    return sorted(usadas)


# ---------------------------------------------------------------
# Cada permissão deve apontar para um modelo existente no app.
# Se o modelo mudar de app, o teste falha e mostra qual permissão.
# ---------------------------------------------------------------
@pytest.mark.parametrize('permissao', _todas_as_permissoes())
def test_permissao_aponta_para_modelo_existente(permissao):
    app_label, _acao, modelo = _quebrar_permissao(permissao)

    # get_model levanta LookupError se o app ou o modelo não existir
    assert apps.get_model(app_label, modelo) is not None


# ---------------------------------------------------------------
# Toda permissão de grupo deve ter nome traduzido, para o admin
# mostrar texto em português e não o nome padrão do Django.
# ---------------------------------------------------------------
def test_permissoes_dos_grupos_tem_traducao():
    sem_traducao = []
    for config in GROUPS_CONFIG.values():
        for permissao in config['permissions']:
            if permissao not in PERMISSIONS_TRANSLATION:
                sem_traducao.append(permissao)

    # Mostra todas as faltantes de uma vez, em ordem estável
    assert sorted(set(sem_traducao)) == []
