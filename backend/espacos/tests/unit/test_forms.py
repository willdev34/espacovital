# ===============================================================
# Título: Testes dos Formulários de Espaços
# Descrição: Cobre ContatoEspacoForm, AvaliacaoEspacoForm, EspacoForm
#            (WhatsApp, CEP, Instagram, localização Brasil e exterior,
#            estado a partir da cidade), BuscaEspacoForm e
#            ComodidadeForm.
# Autor: Will
# Data: 2026-10-15
# ===============================================================

import pytest

from core.models import Cidade, Especialidade, Estado, Pais
from espacos.forms import (
    AvaliacaoEspacoForm, BuscaEspacoForm, ComodidadeForm,
    ContatoEspacoForm, EspacoForm,
)
from espacos.models import Comodidade, Espaco

pytestmark = pytest.mark.django_db


# ===============================================================
# Contato com o espaço
# ===============================================================
class TestContatoEspacoForm:

    def _dados(self, **extras):
        dados = {
            'nome': 'Maria', 'email': 'maria@teste.com',
            'telefone': '(21) 98765-4321', 'assunto': 'Valores',
            'mensagem': 'Quero saber os valores das salas.',
        }
        dados.update(extras)
        return dados

    def test_dados_validos(self):
        assert ContatoEspacoForm(data=self._dados()).is_valid()

    def test_telefone_e_opcional(self):
        assert ContatoEspacoForm(data=self._dados(telefone='')).is_valid()

    def test_telefone_com_poucos_digitos(self):
        form = ContatoEspacoForm(data=self._dados(telefone='(21) 9876-43'))

        assert not form.is_valid()
        assert 'telefone' in form.errors

    def test_mensagem_muito_curta(self):
        form = ContatoEspacoForm(data=self._dados(mensagem='Oi'))

        assert not form.is_valid()
        assert 'pelo menos 10' in form.errors['mensagem'][0]


# ===============================================================
# Avaliação
# ===============================================================
class TestAvaliacaoEspacoForm:

    def test_avaliacao_valida(self):
        form = AvaliacaoEspacoForm(
            data={'nota': 5, 'comentario': 'Ambiente muito acolhedor.'}
        )

        assert form.is_valid(), form.errors

    def test_nota_vai_de_uma_a_cinco_estrelas(self):
        form = AvaliacaoEspacoForm()
        opcoes = [valor for valor, _ in form.fields['nota'].widget.choices]

        assert opcoes == [1, 2, 3, 4, 5]
        assert form.fields['nota'].widget.choices[0][1] == '1 estrela'
        assert form.fields['nota'].widget.choices[1][1] == '2 estrelas'

    def test_palavra_inadequada_e_recusada(self):
        form = AvaliacaoEspacoForm(
            data={'nota': 1, 'comentario': 'Lugar idiota e sujo.'}
        )

        assert not form.is_valid()
        assert 'respeitoso' in form.errors['comentario'][0]


# ===============================================================
# Espaço (dashboard e admin)
# ===============================================================
@pytest.fixture
def brasil():
    pais = Pais.objects.create(nome='Brasil', codigo='BRA', ddi='+55')
    estado = Estado.objects.create(
        nome='Rio de Janeiro', sigla='RJ', pais=pais
    )
    cidade = Cidade.objects.create(nome='Niterói', estado=estado)
    return {'pais': pais, 'estado': estado, 'cidade': cidade}


def _dados_espaco(**extras):
    dados = {
        'nome': 'Espaço Form', 'descricao_breve': 'Breve',
        'cep': '20040020', 'bairro': 'Centro', 'tipo_espaco': 'clinica',
        'email': 'contato@espaco.com', 'cidade_texto': 'Lisboa',
    }
    dados.update(extras)
    return dados


class TestEspacoForm:

    def test_espaco_fora_do_brasil_exige_cidade_em_texto(self):
        form = EspacoForm(data=_dados_espaco(cidade_texto=''))

        assert not form.is_valid()
        assert 'cidade_texto' in form.errors

    def test_espaco_fora_do_brasil_valido(self):
        form = EspacoForm(data=_dados_espaco())

        assert form.is_valid(), form.errors

    def test_brasil_exige_estado_e_cidade(self, brasil):
        form = EspacoForm(
            data=_dados_espaco(pais=brasil['pais'].id, cidade_texto='')
        )

        assert not form.is_valid()
        assert 'estado' in form.errors
        assert 'cidade' in form.errors

    def test_brasil_valido_e_estado_vem_da_cidade(self, brasil):
        form = EspacoForm(data=_dados_espaco(
            pais=brasil['pais'].id, estado=brasil['estado'].id,
            cidade=brasil['cidade'].id, cidade_texto='',
        ))

        assert form.is_valid(), form.errors
        espaco = form.save(commit=False)
        assert espaco.estado == brasil['estado']

    def test_whatsapp_e_salvo_so_com_numeros(self):
        form = EspacoForm(data=_dados_espaco(whatsapp='(21) 98765-4321'))

        assert form.is_valid(), form.errors
        assert form.cleaned_data['whatsapp'] == '21987654321'

    def test_whatsapp_com_digitos_a_menos(self):
        form = EspacoForm(data=_dados_espaco(whatsapp='12345'))

        assert not form.is_valid()
        assert 'Você digitou 5 dígitos' in form.errors['whatsapp'][0]

    def test_cep_e_formatado(self):
        form = EspacoForm(data=_dados_espaco(cep='20040020'))

        assert form.is_valid(), form.errors
        assert form.cleaned_data['cep'] == '20040-020'

    def test_cep_com_digitos_a_menos(self):
        form = EspacoForm(data=_dados_espaco(cep='2004'))

        assert not form.is_valid()
        assert 'CEP deve ter 8 dígitos' in form.errors['cep']

    def test_instagram_perde_a_arroba(self):
        form = EspacoForm(data=_dados_espaco(instagram='@meuespaco'))

        assert form.is_valid(), form.errors
        assert form.cleaned_data['instagram'] == 'meuespaco'

    def test_editar_espaco_com_cidade_filtra_cidades_do_estado(
        self, brasil, django_user_model
    ):
        outro_estado = Estado.objects.create(
            nome='São Paulo', sigla='SP', pais=brasil['pais']
        )
        campinas = Cidade.objects.create(nome='Campinas', estado=outro_estado)
        dono = django_user_model.objects.create_user(
            username='dono_form', email='d@form.com', password='senha123'
        )
        espaco = Espaco.objects.create(
            nome='Espaço Cidade', slug='espaco-cidade',
            descricao_breve='b', descricao_completa='<p>c</p>',
            endereco='Rua', cep='20040-020', bairro='Centro',
            tipo_espaco='clinica', cidade=brasil['cidade'],
            responsavel=dono, is_active=True,
        )

        form = EspacoForm(instance=espaco)

        cidades = list(form.fields['cidade'].queryset)
        assert brasil['cidade'] in cidades
        assert campinas not in cidades
        assert form.fields['estado'].initial == brasil['estado']


# ===============================================================
# Busca e comodidade
# ===============================================================
class TestBuscaEspacoForm:

    def test_formulario_vazio_e_valido(self):
        assert BuscaEspacoForm(data={}).is_valid()

    def test_listas_usam_apenas_registros_ativos(self):
        ativa = Especialidade.objects.create(nome='Reiki', is_active=True)
        inativa = Especialidade.objects.create(nome='Antiga', is_active=False)
        wifi = Comodidade.objects.create(nome='Wi-Fi', is_active=True)

        form = BuscaEspacoForm()

        assert ativa in form.fields['especialidades'].queryset
        assert inativa not in form.fields['especialidades'].queryset
        assert wifi in form.fields['comodidades'].queryset

    def test_ordem_invalida_e_recusada(self):
        form = BuscaEspacoForm(data={'ordem': 'aleatoria'})

        assert not form.is_valid()
        assert 'ordem' in form.errors

    def test_ordem_valida(self):
        assert BuscaEspacoForm(data={'ordem': 'nome'}).is_valid()


class TestComodidadeForm:

    def test_rotulos_em_portugues(self):
        form = ComodidadeForm()

        assert form.fields['nome'].label == 'Nome da Comodidade'
        assert form.fields['is_active'].label == 'Ativo?'

    def test_nome_e_obrigatorio(self):
        form = ComodidadeForm(data={'nome': '', 'slug': 'x'})

        assert not form.is_valid()
        assert 'nome' in form.errors
