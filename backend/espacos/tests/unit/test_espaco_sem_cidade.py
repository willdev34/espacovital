# ===============================================================
# Título: Testes do Espaço sem Cidade do Banco
# Descrição: A cidade do Espaço é opcional (outro país usa texto
#            livre ou nada). Garante que salvar gera o slug e que o
#            texto de exibição funciona nesses casos. Antes,
#            Espaco.save() quebrava com AttributeError sem cidade.
# Autor: Will
# Data: 15/10/2026
# ===============================================================

import pytest
from django.contrib.auth import get_user_model

from core.models import Cidade, Estado, Pais
from espacos.models import Espaco

User = get_user_model()


def criar_espaco(responsavel, **extra):
    """Espaço mínimo; cada teste informa só a cidade que quer testar"""
    campos = {
        'nome': 'Espaço Lótus',
        'descricao_breve': 'Teste.',
        'descricao_completa': '<p>Teste.</p>',
        'endereco': 'Rua A, 1',
        'cep': '20000-000',
        'bairro': 'Centro',
        'tipo_espaco': 'clinica',
        'responsavel': responsavel,
    }
    campos.update(extra)
    return Espaco.objects.create(**campos)


@pytest.fixture
def dono(db):
    return User.objects.create_user(username='dono_sem_cidade', password='x')


@pytest.mark.django_db
class TestEspacoSemCidade:

    def test_slug_so_com_o_nome_quando_nao_ha_cidade(self, dono):
        espaco = criar_espaco(dono)
        assert espaco.slug == 'espaco-lotus'

    def test_slug_usa_o_texto_livre_de_outro_pais(self, dono):
        espaco = criar_espaco(dono, cidade_texto='Lisboa')
        assert espaco.slug == 'espaco-lotus-lisboa'

    def test_slug_usa_a_cidade_do_banco(self, dono):
        pais = Pais.objects.create(nome='Brasil', codigo='BR')
        estado = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ', pais=pais)
        cidade = Cidade.objects.create(nome='Niterói', estado=estado)
        espaco = criar_espaco(dono, cidade=cidade)
        assert espaco.slug == 'espaco-lotus-niteroi'

    def test_texto_de_exibicao_com_cidade_do_banco_mantem_o_formato(self, dono):
        pais = Pais.objects.create(nome='Brasil', codigo='BR')
        estado = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ', pais=pais)
        cidade = Cidade.objects.create(nome='Niterói', estado=estado)
        espaco = criar_espaco(dono, cidade=cidade)
        assert espaco.nome_completo == f'Espaço Lótus - {cidade}'

    def test_slug_repetido_ganha_numero(self, dono):
        primeiro = criar_espaco(dono)
        segundo = criar_espaco(dono)
        assert primeiro.slug == 'espaco-lotus'
        assert segundo.slug == 'espaco-lotus-1'

    def test_texto_de_exibicao_sem_cidade_e_so_o_nome(self, dono):
        espaco = criar_espaco(dono)
        assert espaco.nome_completo == 'Espaço Lótus'
        assert str(espaco) == 'Espaço Lótus'

    def test_texto_de_exibicao_com_texto_livre(self, dono):
        espaco = criar_espaco(dono, cidade_texto='Lisboa')
        assert espaco.nome_completo == 'Espaço Lótus - Lisboa'
