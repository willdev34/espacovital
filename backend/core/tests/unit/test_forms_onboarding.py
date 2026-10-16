# ===============================================================
# Título: Testes dos Formulários de Onboarding
# Descrição: Cobre o filtro de cidades pelo estado enviado e o
#            salvamento dos campos de lista do TerapeutaOnboardingForm
#            e do EspacoOnboardingForm.
# Autor: Will
# Data: 2026-10-15
# ===============================================================

import pytest

from core.forms_onboarding import EspacoOnboardingForm, TerapeutaOnboardingForm
from core.models import Cidade, Especialidade, Estado

pytestmark = pytest.mark.django_db


@pytest.fixture
def estados():
    rj = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
    sp = Estado.objects.create(nome='São Paulo', sigla='SP')
    return {
        'rj': rj, 'sp': sp,
        'niteroi': Cidade.objects.create(nome='Niterói', estado=rj),
        'campinas': Cidade.objects.create(nome='Campinas', estado=sp),
        'inativa': Cidade.objects.create(
            nome='Cidade Inativa', estado=rj, ativo=False
        ),
    }


class TestFiltroDeCidades:

    def test_terapeuta_lista_so_cidades_ativas_do_estado(self, estados):
        form = TerapeutaOnboardingForm(data={'estado': estados['rj'].id})

        cidades = list(form.fields['cidade_principal'].queryset)
        assert cidades == [estados['niteroi']]

    def test_espaco_lista_so_cidades_ativas_do_estado(self, estados):
        form = EspacoOnboardingForm(data={'estado': estados['rj'].id})

        cidades = list(form.fields['cidade'].queryset)
        assert cidades == [estados['niteroi']]

    @pytest.mark.parametrize('classe', [
        TerapeutaOnboardingForm, EspacoOnboardingForm
    ])
    def test_estado_invalido_nao_quebra(self, classe):
        form = classe(data={'estado': 'abc'})

        assert form.is_bound

    @pytest.mark.parametrize('classe', [
        TerapeutaOnboardingForm, EspacoOnboardingForm
    ])
    def test_sem_estado_nao_mexe_no_queryset(self, classe):
        form = classe()

        assert not form.is_bound


class TestSalvarTerapeuta:

    def _dados(self, estados, especialidade):
        return {
            'nome_completo': 'Terapeuta Onboarding',
            'nome_exibicao': 'Terapeuta On',
            'email_profissional': 'on@teste.com',
            'whatsapp': '21987654321',
            'estado': estados['rj'].id,
            'cidade_principal': estados['niteroi'].id,
            'formacao': 'Formação',
            'experiencia_anos': 3,
            'bio_curta': 'Bio curta.',
            'bio_completa': '<p>Bio.</p>',
            'tipos_sessao': ['online', 'presencial'],
            'para_quem': ['adultos'],
            'especialidades': [especialidade.id],
        }

    def test_converte_tipos_de_sessao_e_publico_em_listas(
        self, estados, django_user_model
    ):
        reiki = Especialidade.objects.create(nome='Reiki')
        form = TerapeutaOnboardingForm(data=self._dados(estados, reiki))
        assert form.is_valid(), form.errors

        terapeuta = form.save(commit=False)
        terapeuta.user = django_user_model.objects.create_user(
            username='on_user', email='on@user.com', password='senha123'
        )
        terapeuta.slug = 'terapeuta-onboarding'
        terapeuta.save()

        assert terapeuta.tipos_sessao == ['online', 'presencial']
        assert terapeuta.para_quem == ['adultos']
        # As especialidades passam pelo model intermediário e são gravadas
        # pela view de onboarding, não pelo formulário
        assert list(form.cleaned_data['especialidades']) == [reiki]
