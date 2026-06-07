# ===============================================================
# Título: Testes Unitários - Models do App Terapeutas
# Descrição: Testa criação, slug, __str__, get_absolute_url e
#            propriedades de localização do model Terapeuta
# ===============================================================

import pytest
from django.contrib.auth.models import User
from django.utils.text import slugify
from core.models import Pais, Estado, Cidade, Especialidade
from terapeutas.models import Terapeuta, TerapeutaEspecialidade, PlanoChoices


# ---------------------------------------------------------------
# Fixture compartilhada: cria estrutura mínima para um Terapeuta
# ---------------------------------------------------------------
@pytest.fixture
def dados_localizacao(db):
    pais = Pais.objects.create(nome='Brasil', codigo='BRA', ddi='+55')
    estado = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ', pais=pais)
    cidade = Cidade.objects.create(nome='Rio de Janeiro', estado=estado)
    return {'pais': pais, 'estado': estado, 'cidade': cidade}


@pytest.fixture
def usuario(db):
    # cria um usuário base para vincular ao terapeuta
    return User.objects.create_user(
        username='terapeuta_teste',
        email='terapeuta@teste.com',
        password='senha123',
    )


@pytest.fixture
def terapeuta(db, usuario, dados_localizacao):
    # cria um terapeuta completo para reutilizar nos testes
    return Terapeuta.objects.create(
        user=usuario,
        nome_exibicao='Ana Silva',
        cidade_principal=dados_localizacao['cidade'],
        estado=dados_localizacao['estado'],
        pais=dados_localizacao['pais'],
    )


# ---------------------------------------------------------------
# Testes de criação e campos padrão
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestTerapeutaModel:

    def test_cria_terapeuta_com_dados_validos(self, terapeuta):
        # então o terapeuta deve existir no banco
        assert Terapeuta.objects.filter(nome_exibicao='Ana Silva').exists()

    def test_str_retorna_nome_exibicao(self, terapeuta):
        # então __str__ deve retornar o nome de exibição
        assert str(terapeuta) == 'Ana Silva'

    def test_slug_gerado_automaticamente(self, terapeuta):
        # então o slug deve ser gerado a partir do nome de exibição
        assert terapeuta.slug == slugify('Ana Silva')

    def test_slug_nao_sobrescrito_se_ja_existir(self, usuario, dados_localizacao):
        # dado um terapeuta com slug já definido
        t = Terapeuta.objects.create(
            user=usuario,
            nome_exibicao='Carlos Souza',
            slug='meu-slug-fixo',
            cidade_principal=dados_localizacao['cidade'],
        )

        # então o slug não deve ser alterado
        assert t.slug == 'meu-slug-fixo'

    def test_plano_padrao_basic(self, terapeuta):
        # então o plano padrão deve ser Basic
        assert terapeuta.plano == PlanoChoices.BASIC

    def test_verificado_padrao_false(self, terapeuta):
        # então verificado deve ser False por padrão
        assert terapeuta.verificado is False

    def test_is_active_padrao_true(self, terapeuta):
        # então is_active deve ser True por padrão
        assert terapeuta.is_active is True

    def test_get_absolute_url(self, terapeuta):
        # então a URL deve conter o slug do terapeuta
        url = terapeuta.get_absolute_url()
        assert terapeuta.slug in url

    def test_visualizacoes_padrao_zero(self, terapeuta):
        # então visualizações deve começar em zero
        assert terapeuta.visualizacoes == 0

    def test_total_contatos_padrao_zero(self, terapeuta):
        # então total_contatos deve começar em zero
        assert terapeuta.total_contatos == 0


# ---------------------------------------------------------------
# Testes do relacionamento TerapeutaEspecialidade
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestTerapeutaEspecialidadeModel:

    def test_vincula_especialidade_ao_terapeuta(self, terapeuta):
        # dado uma especialidade existente
        especialidade = Especialidade.objects.create(nome='Reiki')

        # quando vinculada ao terapeuta
        vinculo = TerapeutaEspecialidade.objects.create(
            terapeuta=terapeuta,
            especialidade=especialidade,
        )

        # então o vínculo deve existir
        assert TerapeutaEspecialidade.objects.filter(
            terapeuta=terapeuta,
            especialidade=especialidade,
        ).exists()

    def test_str_vinculo_terapeuta_especialidade(self, terapeuta):
        # dado um vínculo criado
        especialidade = Especialidade.objects.create(nome='Acupuntura')
        vinculo = TerapeutaEspecialidade.objects.create(
            terapeuta=terapeuta,
            especialidade=especialidade,
        )

        # então __str__ deve conter o nome do terapeuta e da especialidade
        resultado = str(vinculo)
        assert 'Ana Silva' in resultado or 'Acupuntura' in resultado