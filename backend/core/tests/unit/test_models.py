# ===============================================================
# Título: Testes Unitários - Models do App Core
# Descrição: Testa os models base, localização (Pais, Estado, Cidade)
#            e o ActiveManager do app core
# ===============================================================

import pytest
from core.models import (
    Pais, Estado, Cidade, Especialidade,
    BaseModel, ActiveManager
)


# ---------------------------------------------------------------
# Testes do model Pais
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestPaisModel:

    def test_cria_pais_com_dados_validos(self):
        # dado dados válidos de um país
        pais = Pais.objects.create(
            nome='Brasil',
            codigo='BRA',
            ddi='+55',
        )

        # então deve existir no banco
        assert Pais.objects.filter(codigo='BRA').exists()
        assert pais.nome == 'Brasil'

    def test_str_retorna_nome_do_pais(self):
        # dado um país criado
        pais = Pais.objects.create(nome='Portugal', codigo='PRT', ddi='+351')

        # então __str__ deve retornar o nome
        assert str(pais) == 'Portugal'

    def test_ativo_padrao_true(self):
        # dado um país criado sem definir ativo
        pais = Pais.objects.create(nome='Argentina', codigo='ARG', ddi='+54')

        # então ativo deve ser True por padrão
        assert pais.ativo is True

    def test_codigo_unico(self):
        # dado um país já existente
        Pais.objects.create(nome='Chile', codigo='CHL', ddi='+56')

        # então criar outro com o mesmo código deve lançar erro
        with pytest.raises(Exception):
            Pais.objects.create(nome='Chile Duplicado', codigo='CHL', ddi='+56')


# ---------------------------------------------------------------
# Testes do model Estado
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestEstadoModel:

    @pytest.fixture
    def pais_brasil(self):
        # fixture local: cria o Brasil para os testes de estado
        return Pais.objects.create(nome='Brasil', codigo='BRA', ddi='+55')

    def test_cria_estado_com_dados_validos(self, pais_brasil):
        # dado dados válidos de um estado
        estado = Estado.objects.create(
            nome='Rio de Janeiro',
            sigla='RJ',
            pais=pais_brasil,
        )

        # então deve existir no banco
        assert Estado.objects.filter(sigla='RJ').exists()
        assert estado.nome == 'Rio de Janeiro'

    def test_str_retorna_nome_do_estado(self, pais_brasil):
        # dado um estado criado
        estado = Estado.objects.create(
            nome='São Paulo', sigla='SP', pais=pais_brasil
        )

        # então __str__ deve retornar nome, sigla e país
        assert str(estado) == 'São Paulo (SP) - Brasil'

    def test_ativo_padrao_true(self, pais_brasil):
        # dado um estado criado sem definir ativo
        estado = Estado.objects.create(
            nome='Minas Gerais', sigla='MG', pais=pais_brasil
        )

        # então ativo deve ser True por padrão
        assert estado.ativo is True

    def test_estado_pertence_ao_pais(self, pais_brasil):
        # dado um estado vinculado ao Brasil
        estado = Estado.objects.create(
            nome='Bahia', sigla='BA', pais=pais_brasil
        )

        # então o FK deve apontar para o Brasil
        assert estado.pais == pais_brasil


# ---------------------------------------------------------------
# Testes do model Cidade
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestCidadeModel:

    @pytest.fixture
    def estado_rj(self):
        # fixture local: cria País + Estado RJ para os testes de cidade
        pais = Pais.objects.create(nome='Brasil', codigo='BRA', ddi='+55')
        return Estado.objects.create(nome='Rio de Janeiro', sigla='RJ', pais=pais)

    def test_cria_cidade_com_dados_validos(self, estado_rj):
        # dado dados válidos de uma cidade
        cidade = Cidade.objects.create(
            nome='Niterói',
            estado=estado_rj,
        )

        # então deve existir no banco
        assert Cidade.objects.filter(nome='Niterói').exists()
        assert cidade.estado == estado_rj

    def test_str_retorna_nome_da_cidade(self, estado_rj):
        # dado uma cidade criada
        cidade = Cidade.objects.create(nome='Petrópolis', estado=estado_rj)

        # então __str__ deve retornar cidade, sigla do estado e código do país
        assert str(cidade) == 'Petrópolis - RJ, BRA'

    def test_ativo_padrao_true(self, estado_rj):
        # dado uma cidade criada sem definir ativo
        cidade = Cidade.objects.create(nome='Volta Redonda', estado=estado_rj)

        # então ativo deve ser True por padrão
        assert cidade.ativo is True


# ---------------------------------------------------------------
# Testes do ActiveManager
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestActiveManager:

    def test_active_manager_retorna_somente_ativos(self):
        # dado especialidades ativas e inativas
        Especialidade.objects.create(nome='Reiki Ativo', is_active=True)
        Especialidade.objects.create(nome='Reiki Inativo', is_active=False)

        # quando o manager active é usado
        resultado = Especialidade.active.all()

        # então deve retornar apenas os ativos
        nomes = list(resultado.values_list('nome', flat=True))
        assert 'Reiki Ativo' in nomes
        assert 'Reiki Inativo' not in nomes

    def test_objects_manager_retorna_todos(self):
        # dado especialidades ativas e inativas
        Especialidade.objects.create(nome='Yoga Ativo', is_active=True)
        Especialidade.objects.create(nome='Yoga Inativo', is_active=False)

        # quando o manager padrão é usado
        todos = Especialidade.objects.filter(nome__contains='Yoga')

        # então deve retornar os dois
        assert todos.count() == 2