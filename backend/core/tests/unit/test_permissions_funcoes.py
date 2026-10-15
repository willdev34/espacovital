# ===============================================================
# Título: Testes das Funções de Permissões e do Comando setup_permissions
# Descrição: Cobre criação de grupos, tradução de nomes, resumo de
#            permissões do usuário, atribuição a grupos, checagens de
#            perfil e o comando de gerenciamento setup_permissions.
# Autor: Will
# Data: 2026-10-15
# ===============================================================

from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command

from core import permissions
from core.permissions import (
    GROUPS_CONFIG,
    assign_user_to_group,
    create_groups_and_permissions,
    get_translated_permission_name,
    get_user_permissions_summary,
    is_admin_user,
    is_space_manager_user,
    is_therapist_user,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------
# Captura o que a função imprime com print().
# O pytest.ini usa "-p no:capture", então capsys não está disponível.
# ---------------------------------------------------------------
def _capturar_print(funcao):
    saida = StringIO()
    with redirect_stdout(saida):
        funcao()
    return saida.getvalue()


# ---------------------------------------------------------------
# Atalho: busca uma permissão pelo formato "app.codename"
# ---------------------------------------------------------------
def _permissao(nome_completo):
    app_label, codename = nome_completo.split('.', 1)
    return Permission.objects.get(
        codename=codename, content_type__app_label=app_label
    )


# ===============================================================
# create_groups_and_permissions
# ===============================================================
class TestCriarGruposEPermissoes:

    def test_cria_todos_os_grupos_com_suas_permissoes(self):
        # Roda a criação e confere cada grupo da configuração
        saida = _capturar_print(create_groups_and_permissions)

        for nome, config in GROUPS_CONFIG.items():
            grupo = Group.objects.get(name=nome)
            assert grupo.permissions.count() == len(set(config['permissions']))

        # Nenhuma permissão da configuração pode ficar sem modelo
        assert 'não encontrada' not in saida

    def test_rodar_duas_vezes_nao_duplica_nem_acumula(self):
        create_groups_and_permissions()
        antes = {g.name: g.permissions.count() for g in Group.objects.all()}

        create_groups_and_permissions()
        depois = {g.name: g.permissions.count() for g in Group.objects.all()}

        assert antes == depois

    def test_remove_permissoes_extras_do_grupo(self):
        # Uma permissão fora da configuração deve sair ao recriar
        create_groups_and_permissions()
        grupo = Group.objects.get(name='Gestores de Espaços')
        extra = _permissao('auth.delete_user')
        grupo.permissions.add(extra)

        create_groups_and_permissions()

        assert not grupo.permissions.filter(pk=extra.pk).exists()

    def test_avisa_quando_permissao_nao_existe(self, monkeypatch):
        config = {'Grupo Teste': {
            'description': 'x',
            'permissions': ['core.view_modelo_que_nao_existe'],
        }}
        monkeypatch.setattr(permissions, 'GROUPS_CONFIG', config)

        saida = _capturar_print(create_groups_and_permissions)

        assert 'não encontrada' in saida
        assert Group.objects.get(name='Grupo Teste').permissions.count() == 0

    def test_erro_inesperado_em_uma_permissao_nao_derruba_o_resto(
        self, monkeypatch
    ):
        # Item sem ponto quebra o split e cai no except genérico
        config = {'Grupo Teste': {
            'description': 'x',
            'permissions': ['semponto', 'core.view_faq'],
        }}
        monkeypatch.setattr(permissions, 'GROUPS_CONFIG', config)

        saida = _capturar_print(create_groups_and_permissions)

        assert 'Erro ao processar' in saida
        grupo = Group.objects.get(name='Grupo Teste')
        assert grupo.permissions.filter(codename='view_faq').exists()


# ===============================================================
# Tradução e resumo de permissões
# ===============================================================
class TestTraducaoEResumo:

    def test_traduz_permissao_conhecida(self):
        perm = _permissao('core.add_faq')
        assert get_translated_permission_name(perm) == 'Criar FAQs'

    def test_permissao_sem_traducao_usa_nome_original(self):
        # Permissão do Django que não está no dicionário
        perm = _permissao('auth.view_permission')
        assert get_translated_permission_name(perm) == perm.name

    def test_resumo_junta_diretas_e_de_grupo(self, usuario_comum):
        usuario_comum.user_permissions.add(_permissao('core.view_faq'))
        create_groups_and_permissions()
        usuario_comum.groups.add(Group.objects.get(name='Gestores de Espaços'))

        resumo = get_user_permissions_summary(usuario_comum)

        origens = {item['source'] for item in resumo}
        assert origens == {'Direto', 'Grupo: Gestores de Espaços'}
        nomes = {item['name'] for item in resumo}
        assert 'Visualizar FAQs' in nomes
        assert 'Visualizar Terapeutas' in nomes

    def test_resumo_vazio_para_usuario_sem_permissoes(self, usuario_comum):
        assert get_user_permissions_summary(usuario_comum) == []


# ===============================================================
# assign_user_to_group
# ===============================================================
class TestAtribuirGrupo:

    def test_adiciona_usuario_ao_grupo(self, usuario_comum):
        Group.objects.get_or_create(name='Terapeutas')[0]

        ok, mensagem = assign_user_to_group(usuario_comum, 'Terapeutas')

        assert ok is True
        assert 'Terapeutas' in mensagem
        assert usuario_comum.groups.filter(name='Terapeutas').exists()

    def test_grupo_inexistente_retorna_falso(self, usuario_comum):
        ok, mensagem = assign_user_to_group(usuario_comum, 'Grupo Fantasma')

        assert ok is False
        assert 'não encontrado' in mensagem
        assert usuario_comum.groups.count() == 0


# ===============================================================
# Checagens de perfil
# ===============================================================
class TestChecagensDePerfil:

    def test_superusuario_e_admin(self, usuario_admin):
        assert is_admin_user(usuario_admin) is True

    def test_membro_do_grupo_administradores_e_admin(self, usuario_comum):
        usuario_comum.groups.add(Group.objects.get_or_create(name='Administradores')[0])
        assert is_admin_user(usuario_comum) is True

    def test_usuario_comum_nao_e_admin(self, usuario_comum):
        assert is_admin_user(usuario_comum) is False

    def test_checagem_de_terapeuta(self, usuario_comum):
        assert is_therapist_user(usuario_comum) is False
        usuario_comum.groups.add(Group.objects.get_or_create(name='Terapeutas')[0])
        assert is_therapist_user(usuario_comum) is True

    def test_checagem_de_gestor_de_espacos(self, usuario_comum):
        assert is_space_manager_user(usuario_comum) is False
        usuario_comum.groups.add(Group.objects.get_or_create(name='Gestores de Espaços')[0])
        assert is_space_manager_user(usuario_comum) is True


# ===============================================================
# Comando: python manage.py setup_permissions
# ===============================================================
class TestComandoSetupPermissions:

    def _rodar(self, *args):
        saida = StringIO()
        call_command('setup_permissions', *args, stdout=saida)
        return saida.getvalue()

    def test_comando_cria_grupos_e_mostra_resumo(self):
        saida = self._rodar()

        assert 'configurado com sucesso' in saida
        for nome in GROUPS_CONFIG:
            assert nome in saida
            assert Group.objects.filter(name=nome).exists()

    def test_verbose_mostra_descricao_dos_grupos(self):
        saida = self._rodar('--verbose')

        for config in GROUPS_CONFIG.values():
            assert config['description'] in saida

    def test_reset_recria_grupos_existentes(self):
        Group.objects.get_or_create(name='Administradores')[0]
        # Um grupo ausente exercita o ramo "não existia" do reset
        Group.objects.filter(name='Editores de Conteúdo').delete()

        saida = self._rodar('--reset', '--verbose')

        assert "Grupo 'Administradores' removido" in saida
        # Os grupos que não existiam são apenas informados
        assert "não existia" in saida
        assert Group.objects.filter(name='Administradores').exists()

    def test_avisa_quando_grupo_nao_foi_criado(self):
        # Simula uma criação que não gera nenhum grupo
        with mock.patch(
            'core.management.commands.setup_permissions.'
            'create_groups_and_permissions'
        ):
            Group.objects.filter(name__in=GROUPS_CONFIG.keys()).delete()
            saida = self._rodar()

        assert 'não foi criado' in saida

    def test_erro_na_criacao_e_repassado(self):
        with mock.patch(
            'core.management.commands.setup_permissions.'
            'create_groups_and_permissions',
            side_effect=RuntimeError('falha simulada'),
        ):
            with pytest.raises(RuntimeError):
                self._rodar()
