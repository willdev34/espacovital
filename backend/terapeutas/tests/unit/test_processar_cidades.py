# ===============================================================
# Título: Testes de processar_multiplas_cidades - Terapeutas
# Descrição: Cobre a função que salva a cidade principal e as cidades
#            adicionais enviadas no formulário do terapeuta: cidade
#            ausente, inválida, duplicada e limpeza das antigas.
# Autor: Will
# Data: 2026-10-15
# ===============================================================

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from core.models import Cidade, Estado
from terapeutas.models import Terapeuta
from terapeutas.views import processar_multiplas_cidades

pytestmark = pytest.mark.django_db

User = get_user_model()


# ---------------------------------------------------------------
# Dados base: um estado, quatro cidades e um terapeuta
# ---------------------------------------------------------------
@pytest.fixture
def cenario():
    estado = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
    cidades = [
        Cidade.objects.create(nome=nome, estado=estado)
        for nome in ('Rio de Janeiro', 'Niterói', 'Petrópolis', 'Volta Redonda')
    ]
    user = User.objects.create_user(
        username='cidades_user', email='cidades@teste.com', password='senha123'
    )
    terapeuta = Terapeuta.objects.create(
        user=user,
        nome_completo='Terapeuta Cidades',
        nome_exibicao='Terapeuta Cidades',
        slug='terapeuta-cidades',
        bio_curta='Bio curta.',
        bio_completa='<p>Bio.</p>',
        formacao='Formação',
        is_active=True,
    )
    return terapeuta, cidades


# ---------------------------------------------------------------
# Monta uma requisição POST com os campos informados
# ---------------------------------------------------------------
def _post(dados):
    return RequestFactory().post('/dashboard/perfil/', dados)


class TestProcessarMultiplasCidades:

    def test_cidade_principal_ausente(self, cenario):
        terapeuta, _ = cenario

        ok, mensagem = processar_multiplas_cidades(_post({}), terapeuta)

        assert ok is False
        assert 'obrigatória' in mensagem

    def test_cidade_principal_inexistente(self, cenario):
        terapeuta, _ = cenario

        ok, mensagem = processar_multiplas_cidades(
            _post({'cidade_principal': 999999}), terapeuta
        )

        assert ok is False
        assert 'inválida' in mensagem

    def test_salva_cidade_principal_e_adicionais(self, cenario):
        terapeuta, (rio, niteroi, petropolis, _) = cenario
        dados = {
            'cidade_principal': rio.id,
            'cidade_adicional_1': niteroi.id,
            'cidade_adicional_2': petropolis.id,
        }

        ok, _ = processar_multiplas_cidades(_post(dados), terapeuta)

        terapeuta.refresh_from_db()
        assert ok is True
        assert terapeuta.cidade_principal == rio
        assert set(terapeuta.cidades_atendimento.all()) == {niteroi, petropolis}

    def test_ignora_adicional_igual_a_principal(self, cenario):
        terapeuta, (rio, niteroi, _, _) = cenario
        dados = {
            'cidade_principal': rio.id,
            'cidade_adicional_1': rio.id,
            'cidade_adicional_2': niteroi.id,
        }

        processar_multiplas_cidades(_post(dados), terapeuta)

        assert set(terapeuta.cidades_atendimento.all()) == {niteroi}

    def test_ignora_adicional_inexistente_ou_vazia(self, cenario):
        terapeuta, (rio, niteroi, _, _) = cenario
        dados = {
            'cidade_principal': rio.id,
            'cidade_adicional_1': 999999,
            'cidade_adicional_2': '',
            'cidade_adicional_3': niteroi.id,
        }

        ok, _ = processar_multiplas_cidades(_post(dados), terapeuta)

        assert ok is True
        assert set(terapeuta.cidades_atendimento.all()) == {niteroi}

    def test_substitui_cidades_antigas_pelas_novas(self, cenario):
        terapeuta, (rio, niteroi, petropolis, volta) = cenario
        terapeuta.cidades_atendimento.add(niteroi, petropolis)

        processar_multiplas_cidades(
            _post({'cidade_principal': rio.id, 'cidade_adicional_1': volta.id}),
            terapeuta,
        )

        assert set(terapeuta.cidades_atendimento.all()) == {volta}

    def test_sem_adicionais_limpa_as_antigas(self, cenario):
        terapeuta, (rio, niteroi, _, _) = cenario
        terapeuta.cidades_atendimento.add(niteroi)

        ok, _ = processar_multiplas_cidades(
            _post({'cidade_principal': rio.id}), terapeuta
        )

        assert ok is True
        assert terapeuta.cidades_atendimento.count() == 0
