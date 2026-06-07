# ===============================================================
# Título: Testes Unitários - Models do App Terapias
# Descrição: Testa criação, validações e comportamentos do
#            model Especialidade (centralizado no core)
# ===============================================================

import pytest
from django.utils.text import slugify
from core.models import Especialidade


# ---------------------------------------------------------------
# Testes de criação básica
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestEspecialidadeModel:

    def test_cria_especialidade_com_dados_validos(self):
        # dado um conjunto de dados válidos
        especialidade = Especialidade.objects.create(
            nome='Reiki',
            descricao_curta='Terapia de canalização de energia vital.',
        )

        # então o registro deve existir no banco
        assert Especialidade.objects.filter(nome='Reiki').exists()
        assert especialidade.nome == 'Reiki'

    def test_slug_gerado_automaticamente(self):
        # dado uma especialidade sem slug informado
        especialidade = Especialidade.objects.create(
            nome='Terapia Floral',
        )

        # então o slug deve ser gerado a partir do nome
        assert especialidade.slug == slugify('Terapia Floral')

    def test_slug_nao_sobrescrito_se_ja_existir(self):
        # dado uma especialidade com slug já definido
        especialidade = Especialidade.objects.create(
            nome='Aromaterapia',
            slug='meu-slug-customizado',
        )

        # então o slug original deve ser mantido
        assert especialidade.slug == 'meu-slug-customizado'

    def test_str_retorna_nome(self):
        # dado uma especialidade criada
        especialidade = Especialidade.objects.create(nome='Meditação')

        # então __str__ deve retornar o nome
        assert str(especialidade) == 'Meditação'

    def test_is_active_padrao_true(self):
        # dado uma especialidade criada sem definir is_active
        especialidade = Especialidade.objects.create(nome='Cristaloterapia')

        # então is_active deve ser True por padrão
        assert especialidade.is_active is True

    def test_destaque_padrao_false(self):
        # dado uma especialidade criada sem definir destaque
        especialidade = Especialidade.objects.create(nome='Quiropraxia')

        # então destaque deve ser False por padrão
        assert especialidade.destaque is False

    def test_nome_unico(self):
        # dado uma especialidade já existente
        Especialidade.objects.create(nome='Yoga')

        # então criar outra com o mesmo nome deve lançar erro
        with pytest.raises(Exception):
            Especialidade.objects.create(nome='Yoga')

    def test_get_absolute_url(self):
        # dado uma especialidade com slug definido
        especialidade = Especialidade.objects.create(
            nome='Acupuntura',
            slug='acupuntura',
        )

        # então a URL deve apontar para a página de detalhe
        url = especialidade.get_absolute_url()
        assert '/acupuntura' in url