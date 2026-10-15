# ===============================================================
# Título: Testes de Fluxo do Onboarding (sem mocks)
# Descrição: Percorre o onboarding de ponta a ponta: filtro de
#            planos por tipo de perfil, desconto de voucher,
#            criação de terapeuta, de espaço e do fluxo "ambos"
#            (2 etapas), com assinatura, histórico, uso do voucher,
#            limpeza da sessão e convite externo.
# Autor: Will
# Data: 15/10/2026
# ===============================================================

from datetime import date, timedelta
from decimal import Decimal

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from agendamentos.models import ConviteExterno, VinculoTerapeutaEspaco
from core.models import (
    Assinatura, Especialidade, HistoricoAssinatura, Pais, Plano, Voucher,
)
from espacos.models import Espaco
from terapeutas.models import Terapeuta, TerapeutaEspecialidade

User = get_user_model()

URL_PLANOS = 'core:onboarding_select_plan'
URL_PERFIL = 'core:onboarding_create_profile'


# ===============================================================
# HELPERS
# ===============================================================

def criar_usuario(client, username='onb_user', first_name='Carlos'):
    """Usuário sem perfil, com e-mail verificado e logado"""
    user = User.objects.create_user(
        username=username, email=f'{username}@exemplo.com',
        password='senha_segura_123', first_name=first_name, last_name='Souza',
    )
    EmailAddress.objects.create(
        user=user, email=user.email, verified=True, primary=True
    )
    client.force_login(user)
    return user


def garantir_plano(nome, valor='100.00', dias_trial=15):
    """Plano ativo com valores conhecidos (a migration já pode ter criado)"""
    plano, _ = Plano.objects.update_or_create(
        nome=nome,
        defaults={
            'nome_exibicao': nome.replace('_', ' ').title(),
            'descricao': 'Plano de teste',
            'valor': Decimal(valor),
            'dias_trial': dias_trial,
            'is_active': True,
            'max_usuarios': None,
        },
    )
    return plano


def criar_voucher(codigo='PROMO', planos=(), **extra):
    """Voucher válido hoje, aplicável aos planos informados"""
    hoje = timezone.now().date()
    campos = {
        'codigo': codigo,
        'descricao': 'Voucher de teste',
        'tipo_desconto': 'percentual',
        'valor_desconto': Decimal('10.00'),
        'data_inicio': hoje - timedelta(days=1),
        'data_expiracao': hoje + timedelta(days=30),
    }
    campos.update(extra)
    voucher = Voucher.objects.create(**campos)
    voucher.planos_aplicaveis.set(planos)
    return voucher


def preparar_sessao(client, tipo_perfil='terapeuta', plano=None, voucher=None, **extra):
    """Grava signup_data na sessão do client"""
    dados = {'tipo_perfil': tipo_perfil, 'phone': '(21) 98765-4321'}
    if plano:
        dados['plano_id'] = plano.id
    if voucher:
        dados['voucher_id'] = voucher.id
    session = client.session
    session['signup_data'] = dados
    for chave, valor in extra.items():
        session[chave] = valor
    session.save()


@pytest.fixture
def especialidade(db):
    return Especialidade.objects.create(nome='Reiki')


@pytest.fixture
def pais(db):
    return Pais.objects.create(nome='Brasil', codigo='BR')


def dados_terapeuta(especialidade, **extra):
    dados = {
        'nome_completo': 'Maria da Silva',
        'nome_exibicao': 'Maria Silva',
        'email_profissional': 'maria@exemplo.com',
        'bio_curta': 'Terapeuta holística.',
        'tipos_sessao': ['presencial', 'online'],
        'para_quem': ['adultos'],
        'especialidades': [especialidade.id],
    }
    dados.update(extra)
    return dados


def dados_espaco(**extra):
    dados = {
        'nome': 'Espaço Lótus',
        'descricao_breve': 'Espaço acolhedor.',
        'email': 'lotus@exemplo.com',
        'bairro': 'Centro',
        'cep': '20000-000',
    }
    dados.update(extra)
    return dados


# ===============================================================
# SELEÇÃO DE PLANO: FILTRO POR TIPO DE PERFIL
# ===============================================================

@pytest.mark.django_db
class TestSelecaoDePlanoPorPerfil:

    TODOS = ['gratuito_filiado', 'basic', 'premium_a', 'premium_s',
             'premium_s_plus', 'combo_a_s', 'combo_a_s_plus']

    def _nomes_exibidos(self, client, tipo):
        for nome in self.TODOS:
            garantir_plano(nome)
        criar_usuario(client)
        preparar_sessao(client, tipo_perfil=tipo)
        response = client.get(reverse(URL_PLANOS))
        assert response.status_code == 200
        return {item['plano'].nome for item in response.context['planos']}

    def test_terapeuta_ve_so_planos_de_terapeuta(self, client):
        assert self._nomes_exibidos(client, 'terapeuta') == {
            'gratuito_filiado', 'basic', 'premium_a', 'combo_a_s', 'combo_a_s_plus',
        }

    def test_espaco_ve_so_planos_de_espaco(self, client):
        assert self._nomes_exibidos(client, 'espaco') == {
            'premium_s', 'premium_s_plus', 'combo_a_s', 'combo_a_s_plus',
        }

    def test_ambos_veem_todos_menos_o_gratuito_filiado(self, client):
        assert self._nomes_exibidos(client, 'ambos') == set(self.TODOS) - {'gratuito_filiado'}


# ===============================================================
# SELEÇÃO DE PLANO: DESCONTO DE VOUCHER
# ===============================================================

@pytest.mark.django_db
class TestSelecaoDePlanoComVoucher:

    def _planos(self, client, voucher):
        criar_usuario(client)
        preparar_sessao(client, voucher=voucher)
        response = client.get(reverse(URL_PLANOS))
        assert response.status_code == 200
        return {item['plano'].nome: item for item in response.context['planos']}

    def test_voucher_percentual_desconta_so_dos_planos_aplicaveis(self, client):
        premium = garantir_plano('premium_a', valor='100.00')
        basic = garantir_plano('basic', valor='50.00')
        voucher = criar_voucher(planos=[premium], valor_desconto=Decimal('10.00'))

        planos = self._planos(client, voucher)

        com_desconto = planos['premium_a']
        assert com_desconto['tem_desconto'] is True
        assert com_desconto['valor_desconto'] == Decimal('10.00')
        assert com_desconto['valor_final'] == Decimal('90.00')

        sem_desconto = planos['basic']
        assert sem_desconto['tem_desconto'] is False
        assert sem_desconto['valor_final'] == basic.valor

    def test_voucher_de_valor_fixo_nunca_passa_do_valor_do_plano(self, client):
        plano = garantir_plano('basic', valor='30.00')
        voucher = criar_voucher(
            planos=[plano], tipo_desconto='valor_fixo', valor_desconto=Decimal('50.00')
        )
        item = self._planos(client, voucher)['basic']
        assert item['valor_desconto'] == Decimal('30.00')
        assert item['valor_final'] == Decimal('0.00')

    def test_voucher_de_gratuidade_zera_o_valor_e_informa_os_dias(self, client):
        plano = garantir_plano('premium_a', valor='100.00')
        voucher = criar_voucher(
            planos=[plano], tipo_desconto='gratuidade',
            valor_desconto=None, dias_gratuidade=30,
        )
        item = self._planos(client, voucher)['premium_a']
        assert item['valor_final'] == Decimal('0.00')
        assert item['dias_gratuidade'] == 30

    def test_voucher_sem_valor_de_desconto_nao_quebra_a_tela(self, client):
        """Antes dava TypeError; agora o desconto vale zero"""
        plano = garantir_plano('basic', valor='50.00')
        voucher = criar_voucher(planos=[plano], valor_desconto=None)
        item = self._planos(client, voucher)['basic']
        assert item['valor_desconto'] == Decimal('0')
        assert item['valor_final'] == Decimal('50.00')

    def test_voucher_inexistente_na_sessao_e_ignorado(self, client):
        garantir_plano('basic')
        criar_usuario(client)
        session = client.session
        session['signup_data'] = {'tipo_perfil': 'terapeuta', 'voucher_id': 999999}
        session.save()
        response = client.get(reverse(URL_PLANOS))
        assert response.status_code == 200
        assert response.context['voucher'] is None


@pytest.mark.django_db
class TestVoucherCalcularDesconto:

    def test_percentual(self):
        voucher = criar_voucher(valor_desconto=Decimal('25.00'))
        assert voucher.calcular_desconto(Decimal('80.00')) == Decimal('20.00')

    def test_valor_fixo_limitado_ao_plano(self):
        voucher = criar_voucher(tipo_desconto='valor_fixo', valor_desconto=Decimal('15.00'))
        assert voucher.calcular_desconto(Decimal('10.00')) == Decimal('10.00')
        assert voucher.calcular_desconto(Decimal('40.00')) == Decimal('15.00')

    def test_gratuidade_desconta_o_plano_inteiro(self):
        voucher = criar_voucher(tipo_desconto='gratuidade', valor_desconto=None)
        assert voucher.calcular_desconto(Decimal('70.00')) == Decimal('70.00')


# ===============================================================
# ONBOARDING COMPLETO: QUEM JÁ TEM ESPAÇO
# ===============================================================

@pytest.mark.django_db
class TestOnboardingJaCompleto:

    def _dono_de_espaco(self, client):
        user = criar_usuario(client, 'dono_onb')
        Espaco.objects.create(
            nome='Espaço Pronto', slug='espaco-pronto', descricao_breve='Teste.',
            descricao_completa='<p>Teste.</p>', endereco='Rua A, 1', cep='20000-000',
            bairro='Centro', tipo_espaco='clinica', responsavel=user,
        )
        return user

    @pytest.mark.parametrize('rota', [
        'core:onboarding_welcome', URL_PLANOS, URL_PERFIL,
    ])
    def test_dono_de_espaco_vai_para_o_dashboard_de_espacos(self, client, rota):
        """O espaço liga ao usuário por 'espacos_gerenciados', não 'espacos'"""
        garantir_plano('premium_s')
        self._dono_de_espaco(client)
        preparar_sessao(client, tipo_perfil='espaco', plano=Plano.objects.get(nome='premium_s'))
        response = client.get(reverse(rota))
        assert response.status_code == 302
        assert response.url == reverse('espacos:dashboard')


# ===============================================================
# CRIAÇÃO DO PERFIL DE TERAPEUTA
# ===============================================================

@pytest.mark.django_db
class TestCriarTerapeuta:

    def test_cria_terapeuta_assinatura_trial_e_historico(self, client, especialidade):
        user = criar_usuario(client)
        plano = garantir_plano('premium_a', dias_trial=15)
        preparar_sessao(client, plano=plano)

        response = client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))

        assert response.status_code == 302
        assert response.url == reverse('terapeutas:dashboard')

        terapeuta = Terapeuta.objects.get(user=user)
        assert terapeuta.slug == 'maria-silva'
        assert terapeuta.plano == 'premium_a'
        assert TerapeutaEspecialidade.objects.filter(
            terapeuta=terapeuta, especialidade=especialidade
        ).exists()

        assinatura = Assinatura.objects.get(usuario=user)
        assert assinatura.plano == plano
        assert assinatura.status == 'trial'
        assert assinatura.data_fim_trial == date.today() + timedelta(days=15)
        assert HistoricoAssinatura.objects.filter(assinatura=assinatura).count() == 1

        # A sessão do onboarding é limpa no fim
        assert 'signup_data' not in client.session

    def test_plano_sem_trial_cria_assinatura_ativa(self, client, especialidade):
        user = criar_usuario(client)
        plano = garantir_plano('basic', dias_trial=0)
        preparar_sessao(client, plano=plano)

        client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))

        assinatura = Assinatura.objects.get(usuario=user)
        assert assinatura.status == 'active'
        assert assinatura.data_fim_trial is None

    def test_combo_vira_premium_a_no_perfil_do_terapeuta(self, client, especialidade):
        user = criar_usuario(client)
        plano = garantir_plano('combo_a_s')
        preparar_sessao(client, plano=plano)

        client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))

        assert Terapeuta.objects.get(user=user).plano == 'premium_a'

    def test_plano_sem_mapeamento_cai_em_basic(self, client, especialidade):
        user = criar_usuario(client)
        plano = garantir_plano('gratuito_filiado')
        preparar_sessao(client, plano=plano)

        client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))

        assert Terapeuta.objects.get(user=user).plano == 'basic'

    def test_slug_repetido_ganha_numero(self, client, especialidade):
        plano = garantir_plano('basic')
        for username in ('onb_a', 'onb_b', 'onb_c'):
            criar_usuario(client, username)
            preparar_sessao(client, plano=plano)
            client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))

        slugs = set(Terapeuta.objects.values_list('slug', flat=True))
        assert slugs == {'maria-silva', 'maria-silva-1', 'maria-silva-2'}

    def test_voucher_de_gratuidade_define_o_trial_e_conta_o_uso(self, client, especialidade):
        user = criar_usuario(client)
        plano = garantir_plano('premium_a', dias_trial=15)
        voucher = criar_voucher(
            planos=[plano], tipo_desconto='gratuidade',
            valor_desconto=None, dias_gratuidade=60,
        )
        preparar_sessao(client, plano=plano, voucher=voucher)

        client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))

        assinatura = Assinatura.objects.get(usuario=user)
        assert assinatura.voucher_utilizado == voucher
        assert assinatura.data_fim_trial == date.today() + timedelta(days=60)
        voucher.refresh_from_db()
        assert voucher.usos_realizados == 1

    def test_voucher_expirado_na_sessao_e_ignorado(self, client, especialidade):
        user = criar_usuario(client)
        plano = garantir_plano('premium_a', dias_trial=15)
        hoje = date.today()
        voucher = criar_voucher(
            planos=[plano], tipo_desconto='gratuidade', valor_desconto=None,
            dias_gratuidade=60,
            data_inicio=hoje - timedelta(days=30),
            data_expiracao=hoje - timedelta(days=1),
        )
        preparar_sessao(client, plano=plano, voucher=voucher)

        client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))

        assinatura = Assinatura.objects.get(usuario=user)
        assert assinatura.voucher_utilizado is None
        assert assinatura.data_fim_trial == date.today() + timedelta(days=15)

    def test_formulario_invalido_nao_cria_nada(self, client, especialidade):
        user = criar_usuario(client)
        plano = garantir_plano('basic')
        preparar_sessao(client, plano=plano)

        response = client.post(
            reverse(URL_PERFIL), dados_terapeuta(especialidade, bio_curta='')
        )

        assert response.status_code == 200
        assert 'bio_curta' in response.context['form_terapeuta'].errors
        assert not Terapeuta.objects.filter(user=user).exists()
        assert not Assinatura.objects.filter(usuario=user).exists()

    def test_plano_inativo_na_sessao_volta_para_a_escolha(self, client, especialidade):
        criar_usuario(client)
        plano = garantir_plano('basic')
        preparar_sessao(client, plano=plano)
        Plano.objects.filter(pk=plano.pk).update(is_active=False)

        response = client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))

        assert response.status_code == 302
        assert response.url == reverse(URL_PLANOS)


# ===============================================================
# CONVITE EXTERNO NO ONBOARDING DO TERAPEUTA
# ===============================================================

@pytest.mark.django_db
class TestConviteExterno:

    def _espaco(self):
        dono = User.objects.create_user(username='dono_convite', password='x')
        return Espaco.objects.create(
            nome='Espaço Convidante', slug='espaco-convidante',
            descricao_breve='Teste.', descricao_completa='<p>Teste.</p>',
            endereco='Rua B, 2', cep='20000-000', bairro='Centro',
            tipo_espaco='clinica', responsavel=dono,
        )

    def _onboarding(self, client, especialidade, token, expira_em):
        espaco = self._espaco()
        convite = ConviteExterno.objects.create(
            espaco=espaco, email='convidada@exemplo.com', expira_em=expira_em,
        )
        user = criar_usuario(client)
        preparar_sessao(client, plano=garantir_plano('basic'), convite_token=str(convite.token))
        client.post(reverse(URL_PERFIL), dados_terapeuta(especialidade))
        convite.refresh_from_db()
        return user, espaco, convite

    def test_convite_valido_cria_vinculo_pendente_e_marca_como_usado(self, client, especialidade):
        user, espaco, convite = self._onboarding(
            client, especialidade, None, timezone.now() + timedelta(days=3)
        )
        vinculo = VinculoTerapeutaEspaco.objects.get(terapeuta__user=user)
        assert vinculo.espaco == espaco
        assert vinculo.status == 'PENDENTE'
        assert vinculo.tipo == 'CONVITE'
        assert convite.usado is True

    def test_convite_expirado_nao_cria_vinculo(self, client, especialidade):
        user, _espaco, convite = self._onboarding(
            client, especialidade, None, timezone.now() - timedelta(days=1)
        )
        assert Terapeuta.objects.filter(user=user).exists()  # o cadastro segue
        assert not VinculoTerapeutaEspaco.objects.filter(terapeuta__user=user).exists()
        assert convite.usado is False


# ===============================================================
# CRIAÇÃO DO PERFIL DE ESPAÇO
# ===============================================================

@pytest.mark.django_db
class TestCriarEspaco:

    def test_cria_espaco_e_assinatura_e_vai_para_o_dashboard(self, client):
        user = criar_usuario(client)
        plano = garantir_plano('premium_s', dias_trial=7)
        preparar_sessao(client, tipo_perfil='espaco', plano=plano)

        response = client.post(reverse(URL_PERFIL), dados_espaco())

        assert response.status_code == 302
        assert response.url == reverse('espacos:dashboard')

        espaco = Espaco.objects.get(responsavel=user)
        assert espaco.nome == 'Espaço Lótus'

        assinatura = Assinatura.objects.get(usuario=user)
        assert assinatura.status == 'trial'
        assert assinatura.data_fim_trial == date.today() + timedelta(days=7)
        assert HistoricoAssinatura.objects.filter(assinatura=assinatura).exists()
        assert 'signup_data' not in client.session

    def test_voucher_de_gratuidade_vale_para_espaco(self, client):
        user = criar_usuario(client)
        plano = garantir_plano('premium_s', dias_trial=7)
        voucher = criar_voucher(
            planos=[plano], tipo_desconto='gratuidade',
            valor_desconto=None, dias_gratuidade=45,
        )
        preparar_sessao(client, tipo_perfil='espaco', plano=plano, voucher=voucher)

        client.post(reverse(URL_PERFIL), dados_espaco())

        assinatura = Assinatura.objects.get(usuario=user)
        assert assinatura.data_fim_trial == date.today() + timedelta(days=45)
        voucher.refresh_from_db()
        assert voucher.usos_realizados == 1

    def test_formulario_invalido_nao_cria_nada(self, client):
        user = criar_usuario(client)
        preparar_sessao(client, tipo_perfil='espaco', plano=garantir_plano('premium_s'))

        response = client.post(reverse(URL_PERFIL), dados_espaco(nome=''))

        assert response.status_code == 200
        assert 'nome' in response.context['form_espaco'].errors
        assert not Espaco.objects.filter(responsavel=user).exists()
        assert not Assinatura.objects.filter(usuario=user).exists()


# ===============================================================
# FLUXO "AMBOS" (TERAPEUTA + ESPAÇO EM 2 ETAPAS)
# ===============================================================

@pytest.mark.django_db
class TestFluxoAmbos:

    def _etapa_1(self, client, especialidade, pais, **extra):
        dados = dados_terapeuta(especialidade)
        dados.update({'whatsapp': '21987654321', 'pais': pais.id})
        dados.update(extra)
        return client.post(reverse(URL_PERFIL), dados)

    def test_etapa_1_cria_terapeuta_e_avanca_para_a_etapa_2(self, client, especialidade, pais):
        user = criar_usuario(client)
        preparar_sessao(client, tipo_perfil='ambos', plano=garantir_plano('combo_a_s'))

        response = self._etapa_1(client, especialidade, pais)

        assert response.status_code == 302
        assert response.url == reverse(URL_PERFIL)
        terapeuta = Terapeuta.objects.get(user=user)
        assert terapeuta.whatsapp == '21987654321'
        assert terapeuta.pais == pais
        assert client.session['onboarding_step'] == 2
        assert client.session['dados_compartilhados']['pais'] == pais.id
        # A assinatura só nasce no fim da etapa 2
        assert not Assinatura.objects.filter(usuario=user).exists()

    def test_etapa_1_invalida_nao_cria_terapeuta(self, client, especialidade, pais):
        user = criar_usuario(client)
        preparar_sessao(client, tipo_perfil='ambos', plano=garantir_plano('combo_a_s'))

        response = self._etapa_1(client, especialidade, pais, whatsapp='abc')

        assert response.status_code == 200
        assert 'whatsapp' in response.context['form_compartilhado'].errors
        assert not Terapeuta.objects.filter(user=user).exists()
        assert 'onboarding_step' not in client.session

    def test_tela_da_etapa_2_mostra_o_formulario_de_espaco(self, client, especialidade, pais):
        criar_usuario(client)
        preparar_sessao(client, tipo_perfil='ambos', plano=garantir_plano('combo_a_s'))
        self._etapa_1(client, especialidade, pais)

        response = client.get(reverse(URL_PERFIL))

        # Já existe terapeuta, mas o espaço falta: a etapa 2 precisa abrir.
        # Antes o usuário caía em "já completou o cadastro" e ia ao dashboard.
        assert response.status_code == 200
        assert response.context['current_step'] == 2
        assert response.context['show_espaco_form'] is True
        assert response.context['dados_compartilhados']['pais'] == pais.id

    def test_etapa_2_abre_com_o_whatsapp_da_etapa_1(self, client, especialidade, pais):
        criar_usuario(client)
        preparar_sessao(client, tipo_perfil='ambos', plano=garantir_plano('combo_a_s'))
        self._etapa_1(client, especialidade, pais)

        form = client.get(reverse(URL_PERFIL)).context['form_espaco']

        assert form.initial['whatsapp'] == '21987654321'
        assert form.initial['pais'] == pais.id

    def test_etapa_1_na_tela_mostra_terapeuta_e_dados_compartilhados(self, client):
        criar_usuario(client)
        preparar_sessao(client, tipo_perfil='ambos', plano=garantir_plano('combo_a_s'))

        response = client.get(reverse(URL_PERFIL))

        assert response.status_code == 200
        assert response.context['current_step'] == 1
        assert response.context['total_steps'] == 2
        assert response.context['show_terapeuta_form'] is True
        assert response.context['show_compartilhado_form'] is True

    def test_etapa_2_cria_espaco_assinatura_unica_e_limpa_a_sessao(self, client, especialidade, pais):
        user = criar_usuario(client)
        plano = garantir_plano('combo_a_s', dias_trial=10)
        preparar_sessao(client, tipo_perfil='ambos', plano=plano)
        self._etapa_1(client, especialidade, pais)

        response = client.post(reverse(URL_PERFIL), dados_espaco())

        assert response.status_code == 302
        assert response.url == reverse('terapeutas:dashboard')
        assert Espaco.objects.filter(responsavel=user).count() == 1
        assert Assinatura.objects.filter(usuario=user).count() == 1
        historico = HistoricoAssinatura.objects.get(assinatura__usuario=user)
        assert 'Terapeuta + Espaço' in historico.acao
        for chave in ('signup_data', 'dados_compartilhados', 'onboarding_step'):
            assert chave not in client.session

    def test_etapa_2_invalida_nao_cria_espaco(self, client, especialidade, pais):
        user = criar_usuario(client)
        preparar_sessao(client, tipo_perfil='ambos', plano=garantir_plano('combo_a_s'))
        self._etapa_1(client, especialidade, pais)

        response = client.post(reverse(URL_PERFIL), dados_espaco(cep=''))

        assert response.status_code == 200
        assert 'cep' in response.context['form_espaco'].errors
        assert not Espaco.objects.filter(responsavel=user).exists()
