# ===============================================================
# Título: Testes do Cadastro (Signup)
# Descrição: Cobre o CustomSignupForm (telefone, termos, tipo de
#            perfil e voucher), o CustomAccountAdapter (dados extras
#            na sessão e redirecionamento após confirmar e-mail) e o
#            fluxo completo de cadastro pela tela.
# Autor: Will
# Data: 15/10/2026
# ===============================================================

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from core.adapters import CustomAccountAdapter
from core.forms import CustomSignupForm
from core.models import Voucher

User = get_user_model()

SENHA_FORTE = 'Senh@Segura#2026'


# ---------------------------------------------------------------
# Dados de um cadastro válido. Cada teste troca só o que importa.
# ---------------------------------------------------------------
def dados_cadastro(**extra):
    dados = {
        'username': 'novo_usuario',
        'email': 'novo@exemplo.com',
        'password1': SENHA_FORTE,
        'password2': SENHA_FORTE,
        'first_name': 'Maria',
        'last_name': 'Silva',
        'phone': '(21) 98765-4321',
        'tipo_perfil': 'terapeuta',
        'aceite_termos': 'on',
        'voucher_code': '',
    }
    dados.update(extra)
    return dados


# ---------------------------------------------------------------
# Cria um voucher válido hoje, com ajustes opcionais
# ---------------------------------------------------------------
def criar_voucher(codigo='BEMVINDO', **extra):
    hoje = timezone.now().date()
    campos = {
        'codigo': codigo,
        'descricao': 'Voucher de teste',
        'data_inicio': hoje - timedelta(days=1),
        'data_expiracao': hoje + timedelta(days=30),
    }
    campos.update(extra)
    return Voucher.objects.create(**campos)


# ===============================================================
# FORMULÁRIO: CAMPOS GERAIS
# ===============================================================

@pytest.mark.django_db
class TestCadastroFormularioGeral:

    def test_dados_validos_passam(self):
        form = CustomSignupForm(data=dados_cadastro())
        assert form.is_valid(), form.errors

    def test_termos_sao_obrigatorios_com_mensagem_clara(self):
        form = CustomSignupForm(data=dados_cadastro(aceite_termos=''))
        assert not form.is_valid()
        assert form.errors['aceite_termos'] == [
            'Você precisa aceitar os termos para continuar.'
        ]

    def test_tipo_de_perfil_fora_da_lista_e_rejeitado(self):
        form = CustomSignupForm(data=dados_cadastro(tipo_perfil='admin'))
        assert not form.is_valid()
        assert 'tipo_perfil' in form.errors

    @pytest.mark.parametrize('tipo', ['terapeuta', 'espaco', 'ambos'])
    def test_tipos_de_perfil_aceitos(self, tipo):
        form = CustomSignupForm(data=dados_cadastro(tipo_perfil=tipo))
        assert form.is_valid(), form.errors

    @pytest.mark.parametrize('campo', ['first_name', 'last_name', 'phone'])
    def test_campos_obrigatorios(self, campo):
        form = CustomSignupForm(data=dados_cadastro(**{campo: ''}))
        assert not form.is_valid()
        assert campo in form.errors

    def test_campos_do_allauth_recebem_classe_e_placeholder(self):
        """O __init__ aplica o visual da Seravitta nos campos do allauth"""
        form = CustomSignupForm()
        assert form.fields['email'].widget.attrs['placeholder'] == 'seu@email.com'
        assert 'rounded-lg' in form.fields['password1'].widget.attrs['class']
        assert form.fields['password2'].widget.attrs['placeholder'] == 'Confirme sua senha'

    def test_nome_de_usuario_recebe_o_mesmo_visual_dos_demais_campos(self):
        """O campo username do allauth nao pode aparecer sem borda no celular"""
        form = CustomSignupForm()
        assert 'border-gray-300' in form.fields['username'].widget.attrs['class']
        assert form.fields['username'].widget.attrs['placeholder'] == 'Nome de usuário'


# ===============================================================
# FORMULÁRIO: TELEFONE
# ===============================================================

@pytest.mark.django_db
class TestCadastroTelefone:

    def test_celular_de_11_digitos_e_aceito_e_formatado(self):
        form = CustomSignupForm(data=dados_cadastro(phone='(21) 98765-4321'))
        assert form.is_valid(), form.errors
        assert form.cleaned_data['phone'] == '(21) 98765-4321'

    def test_fixo_de_10_digitos_e_aceito_e_formatado(self):
        form = CustomSignupForm(data=dados_cadastro(phone='(21) 2345-6789'))
        assert form.is_valid(), form.errors
        assert form.cleaned_data['phone'] == '(21) 2345-6789'

    def test_espaco_apos_o_ddd_e_opcional(self):
        form = CustomSignupForm(data=dados_cadastro(phone='(21)98765-4321'))
        assert form.is_valid(), form.errors
        assert form.cleaned_data['phone'] == '(21) 98765-4321'

    @pytest.mark.parametrize('telefone', [
        '21987654321',        # sem parênteses nem hífen
        '(21) 9876-543',      # faltam dígitos
        '(21) 987654-4321',   # dígitos demais antes do hífen
        'telefone',           # texto
    ])
    def test_formatos_invalidos_sao_rejeitados(self, telefone):
        form = CustomSignupForm(data=dados_cadastro(phone=telefone))
        assert not form.is_valid()
        assert 'phone' in form.errors

    def test_clean_phone_barra_quantidade_de_digitos_errada(self):
        """
        Defesa em profundidade: mesmo que o validador de formato seja
        trocado um dia, o clean_phone ainda exige 10 ou 11 dígitos.
        """
        form = CustomSignupForm(data=dados_cadastro())
        form.cleaned_data = {'phone': '12345'}
        with pytest.raises(forms.ValidationError):
            form.clean_phone()


# ===============================================================
# FORMULÁRIO: VOUCHER
# ===============================================================

@pytest.mark.django_db
class TestCadastroVoucher:

    def test_sem_voucher_o_campo_vira_none(self):
        form = CustomSignupForm(data=dados_cadastro(voucher_code=''))
        assert form.is_valid(), form.errors
        assert form.cleaned_data['voucher_code'] is None

    def test_voucher_valido_devolve_o_objeto(self):
        voucher = criar_voucher('BEMVINDO')
        form = CustomSignupForm(data=dados_cadastro(voucher_code='BEMVINDO'))
        assert form.is_valid(), form.errors
        assert form.cleaned_data['voucher_code'] == voucher

    def test_codigo_em_minusculo_com_espacos_e_normalizado(self):
        voucher = criar_voucher('BEMVINDO')
        form = CustomSignupForm(data=dados_cadastro(voucher_code='  bemvindo  '))
        assert form.is_valid(), form.errors
        assert form.cleaned_data['voucher_code'] == voucher

    def test_codigo_inexistente_e_rejeitado(self):
        form = CustomSignupForm(data=dados_cadastro(voucher_code='NAOEXISTE'))
        assert not form.is_valid()
        assert 'inválido' in form.errors['voucher_code'][0]

    def test_voucher_desativado_e_tratado_como_inexistente(self):
        criar_voucher('DESATIVADO', is_active=False)
        form = CustomSignupForm(data=dados_cadastro(voucher_code='DESATIVADO'))
        assert not form.is_valid()
        assert 'inválido' in form.errors['voucher_code'][0]

    def test_voucher_expirado_e_rejeitado(self):
        hoje = timezone.now().date()
        criar_voucher(
            'EXPIRADO',
            data_inicio=hoje - timedelta(days=30),
            data_expiracao=hoje - timedelta(days=1),
        )
        form = CustomSignupForm(data=dados_cadastro(voucher_code='EXPIRADO'))
        assert not form.is_valid()
        assert 'expirou' in form.errors['voucher_code'][0]

    def test_voucher_que_atingiu_o_limite_de_usos_e_rejeitado(self):
        voucher = criar_voucher('ESGOTADO', limite_usos=1)
        voucher.registrar_uso()
        form = CustomSignupForm(data=dados_cadastro(voucher_code='ESGOTADO'))
        assert not form.is_valid()
        assert 'limite de usos' in form.errors['voucher_code'][0]


# ===============================================================
# ADAPTER
# ===============================================================

def _form_falso(**cleaned):
    """Formulário mínimo: só o que o adapter lê (cleaned_data)"""
    return SimpleNamespace(cleaned_data=cleaned)


def _request_com_sessao():
    """Request com uma sessão em memória, como no fluxo real"""
    request = RequestFactory().post('/accounts/signup/')
    request.session = {}
    return request


@pytest.mark.django_db
class TestCadastroAdapter:

    def _salvar(self, form, commit=True):
        request = _request_com_sessao()
        adapter = CustomAccountAdapter()
        user = adapter.new_user(request)
        # username e e-mail vêm do formulário real; aqui o falso só tem os extras
        user.username = 'usuario_adapter'
        user.email = 'adapter@exemplo.com'
        form.cleaned_data.setdefault('username', 'usuario_adapter')
        form.cleaned_data.setdefault('email', 'adapter@exemplo.com')
        form.cleaned_data.setdefault('password1', SENHA_FORTE)
        salvo = adapter.save_user(request, user, form, commit=commit)
        return request, salvo

    def test_salva_nome_e_sobrenome_no_usuario(self):
        form = _form_falso(first_name='Maria', last_name='Silva')
        _request, user = self._salvar(form)
        user.refresh_from_db()
        assert (user.first_name, user.last_name) == ('Maria', 'Silva')

    def test_guarda_telefone_e_tipo_de_perfil_na_sessao(self):
        form = _form_falso(
            first_name='Ana', last_name='Lima',
            phone='(21) 98765-4321', tipo_perfil='espaco',
        )
        request, _user = self._salvar(form)
        assert request.session['signup_data'] == {
            'phone': '(21) 98765-4321',
            'tipo_perfil': 'espaco',
        }

    def test_guarda_o_id_do_voucher_quando_ha_voucher(self):
        voucher = criar_voucher('SESSAO')
        form = _form_falso(
            first_name='Ana', last_name='Lima',
            phone='(21) 98765-4321', tipo_perfil='terapeuta',
            voucher_code=voucher,
        )
        request, _user = self._salvar(form)
        assert request.session['signup_data']['voucher_id'] == voucher.id

    def test_sem_dados_extras_nao_cria_signup_data(self):
        form = _form_falso(first_name='Ana', last_name='Lima')
        request, _user = self._salvar(form)
        assert 'signup_data' not in request.session

    def test_commit_false_nao_grava_usuario_nem_sessao(self):
        form = _form_falso(
            first_name='Ana', last_name='Lima',
            phone='(21) 98765-4321', tipo_perfil='terapeuta',
        )
        request, user = self._salvar(form, commit=False)
        assert user.pk is None
        assert 'signup_data' not in request.session

    def test_apos_confirmar_email_vai_para_o_onboarding(self):
        url = CustomAccountAdapter().get_email_confirmation_redirect_url(
            RequestFactory().get('/')
        )
        assert url == reverse('core:onboarding_welcome')


# ===============================================================
# FLUXO COMPLETO PELA TELA DE CADASTRO
# ===============================================================

@pytest.mark.django_db
class TestCadastroFluxoCompleto:

    def test_tela_de_cadastro_abre(self, client):
        response = client.get(reverse('account_signup'))
        assert response.status_code == 200
        assert isinstance(response.context['form'], CustomSignupForm)

    def test_cadastro_valido_cria_usuario_e_pede_confirmacao_de_email(self, client):
        response = client.post(reverse('account_signup'), dados_cadastro())

        assert response.status_code == 302
        assert response.url == reverse('account_email_verification_sent')

        user = User.objects.get(username='novo_usuario')
        assert (user.first_name, user.last_name) == ('Maria', 'Silva')
        assert user.email == 'novo@exemplo.com'
        # Com verificação obrigatória, ninguém entra antes de confirmar o e-mail
        assert '_auth_user_id' not in client.session

    def test_cadastro_guarda_dados_para_o_onboarding(self, client):
        client.post(reverse('account_signup'), dados_cadastro(tipo_perfil='ambos'))
        signup_data = client.session['signup_data']
        assert signup_data['phone'] == '(21) 98765-4321'
        assert signup_data['tipo_perfil'] == 'ambos'

    def test_voucher_do_cadastro_chega_ao_onboarding(self, client):
        """
        O onboarding lê signup_data['voucher_id']. Antes da correção o
        form regravava a sessão com a chave 'voucher' e o voucher se perdia.
        """
        voucher = criar_voucher('CHEGA')
        client.post(reverse('account_signup'), dados_cadastro(voucher_code='CHEGA'))
        assert client.session['signup_data']['voucher_id'] == voucher.id

    def test_cadastro_com_dados_invalidos_nao_cria_usuario(self, client):
        response = client.post(
            reverse('account_signup'), dados_cadastro(phone='123', aceite_termos='')
        )
        assert response.status_code == 200
        assert not User.objects.filter(username='novo_usuario').exists()
        assert 'phone' in response.context['form'].errors
        assert 'aceite_termos' in response.context['form'].errors
