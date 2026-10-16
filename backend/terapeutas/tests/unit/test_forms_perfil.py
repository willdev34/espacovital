# ===============================================================
# Título: Testes do Formulário de Edição de Perfil do Terapeuta
# Descrição: Cobre a validação e a formatação de CPF/CNPJ, o limite
#            da bio curta, o preenchimento inicial a partir do
#            terapeuta existente, o filtro de cidades por estado e o
#            salvamento dos campos de lista e relacionamentos.
# Autor: Will
# Data: 2026-10-15
# ===============================================================

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models import Cidade, Especialidade, Estado
from terapeutas.forms import TerapeutaEditarPerfilForm
from terapeutas.models import Terapeuta

pytestmark = pytest.mark.django_db

User = get_user_model()

# CPF e CNPJ válidos usados só como exemplo nos testes
CPF_VALIDO = '52998224725'
CNPJ_VALIDO = '11222333000181'


@pytest.fixture
def terapeuta():
    usuario = User.objects.create_user(
        username='perfil_form', email='perfil@form.com', password='senha123'
    )
    return Terapeuta.objects.create(
        user=usuario, nome_completo='Terapeuta Form',
        nome_exibicao='Terapeuta Form', slug='terapeuta-form',
        bio_curta='Bio curta.', bio_completa='<p>Bio.</p>',
        formacao='Formação', is_active=True,
    )


# ---------------------------------------------------------------
# Dados mínimos para o formulário ser válido
# ---------------------------------------------------------------
def _dados(**extras):
    dados = {
        'nome_completo': 'Terapeuta Form Editado',
        'nome_exibicao': 'Terapeuta Editado',
        'email_profissional': 'profissional@form.com',
        'formacao': 'Formação completa',
        'experiencia_anos': 5,
        'bio_curta': 'Bio curta editada.',
        'bio_completa': '<p>Bio completa editada.</p>',
    }
    dados.update(extras)
    return dados


# ---------------------------------------------------------------
# Roda clean_cpf_cnpj direto, sem precisar do formulário inteiro
# ---------------------------------------------------------------
def _limpar_documento(valor):
    form = TerapeutaEditarPerfilForm()
    form.cleaned_data = {'cpf_cnpj': valor}
    return form.clean_cpf_cnpj()


# ===============================================================
# CPF e CNPJ
# ===============================================================
class TestDocumento:

    def test_documento_vazio_e_aceito(self):
        assert _limpar_documento('') == ''

    def test_cpf_valido_e_formatado(self):
        assert _limpar_documento(CPF_VALIDO) == '529.982.247-25'

    def test_cpf_ja_formatado_continua_valido(self):
        assert _limpar_documento('529.982.247-25') == '529.982.247-25'

    def test_cpf_com_digito_verificador_errado(self):
        with pytest.raises(ValidationError, match='CPF inválido'):
            _limpar_documento('52998224726')

    def test_cpf_com_todos_digitos_iguais(self):
        with pytest.raises(ValidationError, match='CPF inválido'):
            _limpar_documento('11111111111')

    def test_cnpj_valido_e_formatado(self):
        assert _limpar_documento(CNPJ_VALIDO) == '11.222.333/0001-81'

    def test_cnpj_com_digito_verificador_errado(self):
        with pytest.raises(ValidationError, match='CNPJ inválido'):
            _limpar_documento('11222333000182')

    def test_cnpj_com_segundo_digito_errado(self):
        # Primeiro dígito correto (8), segundo alterado
        with pytest.raises(ValidationError, match='CNPJ inválido'):
            _limpar_documento('11222333000180')

    def test_cnpj_com_todos_digitos_iguais(self):
        with pytest.raises(ValidationError, match='CNPJ inválido'):
            _limpar_documento('11111111111111')

    def test_quantidade_de_digitos_invalida(self):
        with pytest.raises(ValidationError, match='11 dígitos'):
            _limpar_documento('12345')

    def test_cpf_com_segundo_digito_errado(self):
        # Primeiro dígito correto (2), segundo alterado
        with pytest.raises(ValidationError, match='CPF inválido'):
            _limpar_documento('52998224720')


# ===============================================================
# Bio curta
# ===============================================================
class TestBioCurta:

    def test_ate_200_caracteres_e_aceita(self, terapeuta):
        form = TerapeutaEditarPerfilForm(
            data=_dados(bio_curta='a' * 200), instance=terapeuta
        )

        assert 'bio_curta' not in form.errors

    def test_acima_de_200_caracteres_e_recusada(self, terapeuta):
        form = TerapeutaEditarPerfilForm(
            data=_dados(bio_curta='a' * 201), instance=terapeuta
        )

        assert not form.is_valid()
        assert 'bio_curta' in form.errors


# ===============================================================
# Preenchimento inicial e filtro de cidades
# ===============================================================
class TestInicializacao:

    def test_formulario_novo_nao_precisa_de_instancia(self):
        form = TerapeutaEditarPerfilForm()

        assert form.fields['tipos_sessao'].initial is None

    def test_preenche_campos_a_partir_do_terapeuta(self, terapeuta):
        reiki = Especialidade.objects.create(nome='Reiki')
        estado = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
        niteroi = Cidade.objects.create(nome='Niterói', estado=estado)
        terapeuta.tipos_sessao = ['online']
        terapeuta.para_quem = ['adultos']
        terapeuta.save()
        terapeuta.especialidades.add(reiki)
        terapeuta.cidades_atendimento.add(niteroi)

        form = TerapeutaEditarPerfilForm(instance=terapeuta)

        assert form.fields['tipos_sessao'].initial == ['online']
        assert form.fields['para_quem'].initial == ['adultos']
        assert form.fields['especialidades'].initial == [reiki.id]
        assert form.fields['cidades_atendimento'].initial == [niteroi.id]

    def test_filtra_cidades_pelo_estado_enviado(self, terapeuta):
        rj = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
        sp = Estado.objects.create(nome='São Paulo', sigla='SP')
        niteroi = Cidade.objects.create(nome='Niterói', estado=rj)
        campinas = Cidade.objects.create(nome='Campinas', estado=sp)

        form = TerapeutaEditarPerfilForm(
            data={'estado': rj.id}, instance=terapeuta
        )

        cidades = list(form.fields['cidade_principal'].queryset)
        assert niteroi in cidades
        assert campinas not in cidades

    def test_estado_enviado_invalido_nao_quebra(self, terapeuta):
        form = TerapeutaEditarPerfilForm(
            data={'estado': 'abc'}, instance=terapeuta
        )

        assert 'cidade_principal' in form.fields

    def test_usa_o_estado_do_terapeuta_quando_nada_foi_enviado(
        self, terapeuta
    ):
        rj = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
        sp = Estado.objects.create(nome='São Paulo', sigla='SP')
        niteroi = Cidade.objects.create(nome='Niterói', estado=rj)
        campinas = Cidade.objects.create(nome='Campinas', estado=sp)
        terapeuta.estado = rj
        terapeuta.save()

        form = TerapeutaEditarPerfilForm(instance=terapeuta)

        cidades = list(form.fields['cidade_principal'].queryset)
        assert niteroi in cidades
        assert campinas not in cidades


# ===============================================================
# Salvamento
# ===============================================================
class TestSalvar:

    def test_converte_listas_e_salva_relacionamentos(self, terapeuta):
        reiki = Especialidade.objects.create(nome='Reiki')
        estado = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
        niteroi = Cidade.objects.create(nome='Niterói', estado=estado)
        form = TerapeutaEditarPerfilForm(
            data=_dados(
                tipos_sessao=['presencial', 'online'],
                para_quem=['adultos', 'idosos'],
                cpf_cnpj=CPF_VALIDO,
                especialidades=[reiki.id],
                cidades_atendimento=[niteroi.id],
            ),
            instance=terapeuta,
        )

        assert form.is_valid(), form.errors
        salvo = form.save()

        salvo.refresh_from_db()
        assert salvo.tipos_sessao == ['presencial', 'online']
        assert salvo.para_quem == ['adultos', 'idosos']
        assert list(salvo.especialidades.all()) == [reiki]
        assert list(salvo.cidades_atendimento.all()) == [niteroi]
        assert salvo.nome_completo == 'Terapeuta Form Editado'

    def test_save_sem_commit_nao_grava_no_banco(self, terapeuta):
        form = TerapeutaEditarPerfilForm(
            data=_dados(tipos_sessao=['online']), instance=terapeuta
        )

        assert form.is_valid(), form.errors
        form.save(commit=False)

        terapeuta.refresh_from_db()
        assert terapeuta.nome_completo == 'Terapeuta Form'
