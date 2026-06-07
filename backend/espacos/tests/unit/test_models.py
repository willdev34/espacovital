# ===============================================================
# Título: Testes Unitários - Models do App Espacos
# Descrição: Testa criação, slug, properties e badges do
#            model Espaco e Comodidade
# ===============================================================

import pytest
from django.contrib.auth.models import User
from core.models import Pais, Estado, Cidade, Especialidade
from espacos.models import Espaco, Comodidade, FotoGaleriaEspaco


# ---------------------------------------------------------------
# Fixtures compartilhadas
# ---------------------------------------------------------------
@pytest.fixture
def dados_localizacao(db):
    pais = Pais.objects.create(nome='Brasil', codigo='BRA', ddi='+55')
    estado = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ', pais=pais)
    cidade = Cidade.objects.create(nome='Rio de Janeiro', estado=estado)
    return {'pais': pais, 'estado': estado, 'cidade': cidade}


@pytest.fixture
def usuario(db):
    return User.objects.create_user(
        username='dono_espaco',
        email='dono@teste.com',
        password='senha123',
    )


@pytest.fixture
def espaco(db, usuario, dados_localizacao):
    # cria um espaço completo para reutilizar nos testes
    return Espaco.objects.create(
        nome='Centro Holístico Zen',
        descricao_breve='Espaço de terapias holísticas no centro do Rio.',
        responsavel=usuario,
        cidade=dados_localizacao['cidade'],
        estado=dados_localizacao['estado'],
        pais=dados_localizacao['pais'],
    )


# ---------------------------------------------------------------
# Testes de criação e campos padrão
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestEspacoModel:

    def test_cria_espaco_com_dados_validos(self, espaco):
        # então o espaço deve existir no banco
        assert Espaco.objects.filter(nome='Centro Holístico Zen').exists()

    def test_str_retorna_nome(self, espaco):
        # então __str__ deve retornar nome e localização do espaço
        assert str(espaco) == 'Centro Holístico Zen - Rio de Janeiro - RJ, BRA'

    def test_slug_gerado_automaticamente(self, espaco):
        # então o slug deve ser gerado a partir do nome e cidade
        assert 'centro-holistico-zen' in espaco.slug

    def test_slug_incrementado_para_duplicatas(self, usuario, dados_localizacao):
        Espaco.objects.create(
            nome='Espaço Zen',
            descricao_breve='Primeiro',
            responsavel=usuario,
            cidade=dados_localizacao['cidade'],
        )
        segundo = Espaco.objects.create(
            nome='Espaço Zen',
            descricao_breve='Segundo',
            responsavel=usuario,
            cidade=dados_localizacao['cidade'],
        )

        # então o segundo deve ter slug incrementado
        assert segundo.slug.endswith('-1')

    def test_is_active_padrao_true(self, espaco):
        # então is_active deve ser True por padrão
        assert espaco.is_active is True

    def test_is_verificado_padrao_false(self, espaco):
        # então is_verificado deve ser False por padrão
        assert espaco.is_verificado is False

    def test_is_premium_padrao_false(self, espaco):
        # então is_premium deve ser False por padrão
        assert espaco.is_premium is False

    def test_get_absolute_url(self, espaco):
        # então a URL deve conter o slug do espaço
        url = espaco.get_absolute_url()
        assert espaco.slug in url

    def test_property_nome_completo(self, espaco):
        # então nome_completo deve conter o nome e a cidade
        assert 'Centro Holístico Zen' in espaco.nome_completo
        assert 'Rio de Janeiro' in espaco.nome_completo

    def test_property_media_avaliacoes_sem_avaliacoes(self, espaco):
        # dado um espaço sem avaliações
        # então a média deve ser 0
        assert espaco.media_avaliacoes == 0

    def test_property_total_avaliacoes_sem_avaliacoes(self, espaco):
        # dado um espaço sem avaliações
        # então o total deve ser 0
        assert espaco.total_avaliacoes == 0

    def test_property_especialidades_lista_vazia(self, espaco):
        # dado um espaço sem especialidades vinculadas
        # então a lista deve ser string vazia
        assert espaco.especialidades_lista == ''

    def test_property_especialidades_lista_com_dados(self, espaco):
        # dado especialidades vinculadas ao espaço
        esp1 = Especialidade.objects.create(nome='Reiki')
        esp2 = Especialidade.objects.create(nome='Yoga')
        espaco.especialidades.add(esp1, esp2)

        # então a lista deve conter os nomes
        lista = espaco.especialidades_lista
        assert 'Reiki' in lista or 'Yoga' in lista

    def test_property_comodidades_destaque_vazio(self, espaco):
        # dado um espaço sem comodidades em destaque
        # então deve retornar queryset vazio
        assert espaco.comodidades_destaque.count() == 0

    def test_get_status_badges_espaco_simples(self, espaco):
        # dado um espaço sem verificação, premium ou destaque
        badges = espaco.get_status_badges()

        # então não deve retornar badges
        assert badges == []

    def test_get_status_badges_espaco_verificado(self, espaco):
        # dado um espaço verificado
        espaco.is_verificado = True
        espaco.save()

        # então deve retornar o badge de verificado
        badges = espaco.get_status_badges()
        tipos = [b['tipo'] for b in badges]
        assert 'verificado' in tipos

    def test_get_status_badges_espaco_premium(self, espaco):
        # dado um espaço premium
        espaco.is_premium = True
        espaco.save()

        # então deve retornar o badge de premium
        badges = espaco.get_status_badges()
        tipos = [b['tipo'] for b in badges]
        assert 'premium' in tipos


# ---------------------------------------------------------------
# Testes do model Comodidade
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestComodidadeModel:

    def test_cria_comodidade_com_dados_validos(self):
        # dado dados válidos de uma comodidade
        comodidade = Comodidade.objects.create(nome='Ar-condicionado')

        # então deve existir no banco
        assert Comodidade.objects.filter(nome='Ar-condicionado').exists()

    def test_str_retorna_nome(self):
        # então __str__ deve retornar o nome
        comodidade = Comodidade.objects.create(nome='Maca')
        assert str(comodidade) == 'Maca'

    def test_slug_gerado_automaticamente(self):
        # então o slug deve ser gerado a partir do nome
        comodidade = Comodidade.objects.create(nome='Sala de Espera')
        assert comodidade.slug == 'sala-de-espera'

    def test_is_destaque_padrao_false(self):
        # então is_destaque deve ser False por padrão
        comodidade = Comodidade.objects.create(nome='Wi-Fi')
        assert comodidade.is_destaque is False