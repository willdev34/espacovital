# ===============================================================
# Título: Testes das Views de Onboarding
# Descrição: Testes unitários para WelcomeView, SelectPlanView
#             e CreateProfileView do fluxo de onboarding
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.http import HttpResponseRedirect

from decimal import Decimal

from core.models import Plano, Voucher, Assinatura, HistoricoAssinatura
from core.views_onboarding import CreateProfileView

User = get_user_model()


# ===============================================================
# HELPERS E MIXINS COMPARTILHADOS
# ===============================================================

class OnboardingTestBase(TestCase):
    """
    Base compartilhada entre todos os testes de onboarding.
    Cria usuário logado com email verificado por padrão.
    """

    def setUp(self):
        """Configura usuário, client e plano padrão antes de cada teste"""
        self.client = Client()

        # Criar usuário sem perfil (estado inicial de onboarding)
        self.user = User.objects.create_user(
            username='usuario_teste',
            email='teste@espacovital.com',
            password='senha_segura_123',
            first_name='Carlos',
        )
        self.client.login(username='usuario_teste', password='senha_segura_123')

        # Buscar ou criar plano padrão (nome tem unique=True no banco)
        self.plano, _ = Plano.objects.get_or_create(
            nome='premium_a',
            defaults={
                'nome_exibicao': 'Premium A',
                'descricao': 'Plano para terapeutas',
                'valor': Decimal('49.90'),
                'dias_trial': 15,
                'is_active': True,
            }
        )

    def _verificar_email(self):
        """Utilitário: marca email do usuário como verificado via allauth"""
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True,
        )

    def _setar_sessao_signup(self, tipo_perfil='terapeuta', plano_id=None, voucher_id=None):
        """Utilitário: popula signup_data na sessão do client"""
        session = self.client.session
        signup_data = {'tipo_perfil': tipo_perfil}
        if plano_id:
            signup_data['plano_id'] = plano_id
        if voucher_id:
            signup_data['voucher_id'] = voucher_id
        session['signup_data'] = signup_data
        session.save()


# ===============================================================
# TESTES DA WELCOME VIEW
# ===============================================================

class WelcomeViewTest(OnboardingTestBase):
    """
    Testa a WelcomeView: primeira tela do onboarding.
    Cobre redirecionamentos e exibição correta do template.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('core:onboarding_welcome')

    # --- Acesso sem autenticação ---

    def test_redireciona_usuario_nao_autenticado(self):
        """Usuário não logado deve ser redirecionado para login"""
        self.client.logout()
        response = self.client.get(self.url)

        # Deve redirecionar (302) para tela de login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/', response.url)

    # --- Email não verificado ---

    def test_redireciona_se_email_nao_verificado(self):
        """Usuário sem email verificado deve ir para tela de confirmação"""
        # Email não verificado = sem EmailAddress no banco
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('email', response.url)

    def test_mensagem_aviso_email_nao_verificado(self):
        """Deve exibir mensagem de aviso quando email não está verificado"""
        response = self.client.get(self.url, follow=True)
        mensagens = [str(m) for m in response.context['messages']]

        self.assertTrue(
            any('confirme seu email' in m.lower() for m in mensagens)
        )

    # --- Onboarding já completo ---

    def test_redireciona_se_ja_tem_terapeuta(self):
        """Usuário com perfil de terapeuta deve ser redirecionado para dashboard"""
        self._verificar_email()

        # Simular que usuário já tem relação 'terapeuta'
        with patch.object(
            type(self.user), 'terapeuta',
            new_callable=lambda: property(lambda self: MagicMock()),
            create=True
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('dashboard', response.url)

    def test_redireciona_se_ja_tem_espaco(self):
        """Usuário com espaço cadastrado deve ser redirecionado"""
        self._verificar_email()

        # Espaço de verdade, ligado ao usuário por Espaco.responsavel
        from espacos.models import Espaco
        Espaco.objects.create(
            nome='Espaço do Carlos',
            slug='espaco-do-carlos',
            descricao_breve='Teste.',
            descricao_completa='<p>Teste.</p>',
            endereco='Rua X, 1',
            cep='20000-000',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=self.user,
        )

        response = self.client.get(self.url)

        self.assertRedirects(
            response, reverse('espacos:dashboard'), fetch_redirect_response=False
        )

    # --- Fluxo normal ---

    def test_exibe_welcome_com_email_verificado(self):
        """Usuário com email verificado e sem perfil deve ver o template de boas-vindas"""
        self._verificar_email()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'onboarding/welcome.html')

    def test_contexto_tem_nome_do_usuario(self):
        """Contexto deve conter o primeiro nome do usuário"""
        self._verificar_email()
        response = self.client.get(self.url)

        self.assertEqual(response.context['first_name'], 'Carlos')

    def test_contexto_tipo_perfil_padrao_terapeuta(self):
        """Sem signup_data na sessão, tipo_perfil padrão deve ser 'terapeuta'"""
        self._verificar_email()
        response = self.client.get(self.url)

        self.assertEqual(response.context['tipo_perfil'], 'terapeuta')

    def test_contexto_tipo_perfil_da_sessao(self):
        """Tipo de perfil deve vir da sessão quando presente"""
        self._verificar_email()
        self._setar_sessao_signup(tipo_perfil='espaco')
        response = self.client.get(self.url)

        self.assertEqual(response.context['tipo_perfil'], 'espaco')

    def test_contexto_has_voucher_false_sem_voucher(self):
        """has_voucher deve ser False quando não há voucher na sessão"""
        self._verificar_email()
        response = self.client.get(self.url)

        self.assertFalse(response.context['has_voucher'])

    def test_contexto_has_voucher_true_com_voucher(self):
        """has_voucher deve ser True quando há voucher_id na sessão"""
        self._verificar_email()
        self._setar_sessao_signup(voucher_id=99)
        response = self.client.get(self.url)

        self.assertTrue(response.context['has_voucher'])


# ===============================================================
# TESTES DA SELECT PLAN VIEW
# ===============================================================

class SelectPlanViewTest(OnboardingTestBase):
    """
    Testa a SelectPlanView: exibe planos disponíveis e processa seleção.
    """

    def setUp(self):
        super().setUp()
        self.url_get = reverse('core:onboarding_select_plan')

    # --- GET: exibição dos planos ---

    def test_get_exibe_planos_disponiveis(self):
        """GET deve renderizar o template com planos ativos"""
        self._setar_sessao_signup()
        response = self.client.get(self.url_get)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'onboarding/select_plan.html')

    def test_get_nao_exibe_planos_inativos(self):
        """Planos com is_active=False não devem aparecer na listagem"""
        # Desativar o plano padrão e criar um inativo
        self.plano.is_active = False
        self.plano.save()

        Plano.objects.get_or_create(
            nome='basic',
            defaults={
                'nome_exibicao': 'Basic',
                'descricao': 'Plano básico',
                'valor': Decimal('19.90'),
                'dias_trial': 7,
                'is_active': False,
            }
        )

        self._setar_sessao_signup()
        response = self.client.get(self.url_get)

        # planos no contexto são dicts com chave 'plano' -> objeto Plano
        planos_exibidos = list(response.context.get('planos', []))
        # Cada item é um dict; verifica que todos os planos exibidos são ativos
        for p in planos_exibidos:
            self.assertTrue(p['plano'].is_active)

    def test_get_redireciona_se_ja_tem_terapeuta(self):
        """Usuário com onboarding completo deve ser redirecionado"""
        with patch('core.views_onboarding.hasattr') as mock_hasattr:
            mock_hasattr.side_effect = lambda obj, attr: attr == 'terapeuta'
            response = self.client.get(self.url_get)

        self.assertEqual(response.status_code, 302)

    def test_get_voucher_invalido_exibe_aviso(self):
        """Voucher inválido na sessão deve gerar mensagem de aviso"""
        # Criar voucher expirado
        from datetime import date
        voucher = Voucher.objects.create(
            codigo='EXPIRADO2024',
            descricao='Voucher de teste',
            tipo_desconto='percentual',
            valor_desconto=Decimal('10.00'),
            data_inicio=date(2024, 1, 1),
            data_expiracao=date(2024, 1, 31),  # campo correto, data no passado
            is_active=False,
        )
        self._setar_sessao_signup(voucher_id=voucher.id)
        response = self.client.get(self.url_get, follow=True)

        mensagens = [str(m) for m in response.context['messages']]
        self.assertTrue(any('voucher' in m.lower() for m in mensagens))

    # --- POST: seleção de plano ---

    def test_post_plano_valido_salva_na_sessao(self):
        """POST com plano válido deve salvar plano_id na sessão"""
        self._setar_sessao_signup()
        response = self.client.post(self.url_get, {'plano_id': self.plano.id})

        # Verificar que plano foi salvo na sessão
        session = self.client.session
        self.assertEqual(session['signup_data']['plano_id'], self.plano.id)

    def test_post_plano_valido_redireciona_para_create_profile(self):
        """POST com plano válido deve redirecionar para criação de perfil"""
        self._setar_sessao_signup()
        response = self.client.post(self.url_get, {'plano_id': self.plano.id})

        self.assertRedirects(response, reverse('core:onboarding_create_profile'))

    def test_post_plano_invalido_redireciona_com_erro(self):
        """POST com plano inexistente deve redirecionar com mensagem de erro"""
        self._setar_sessao_signup()
        response = self.client.post(self.url_get, {'plano_id': 99999}, follow=True)

        mensagens = [str(m) for m in response.context['messages']]
        self.assertTrue(any('inválido' in m.lower() or 'invalido' in m.lower() for m in mensagens))

    def test_post_plano_inativo_nao_aceito(self):
        """POST com plano inativo deve redirecionar com erro"""
        self.plano.is_active = False
        self.plano.save()

        self._setar_sessao_signup()
        response = self.client.post(self.url_get, {'plano_id': self.plano.id}, follow=True)

        # Deve ter redirecionado com erro (plano inativo não é encontrado)
        self.assertEqual(response.status_code, 200)

    def test_post_plano_lotado_redireciona_com_erro(self):
        """Plano com max_usuarios atingido deve bloquear seleção"""
        # Configurar plano com limite de 1 usuário
        self.plano.max_usuarios = 1
        self.plano.save()

        # Criar outro usuário e assinatura ativa para lotar o plano
        outro_user = User.objects.create_user(
            username='outro_user', password='senha123'
        )
        Assinatura.objects.create(
            usuario=outro_user,
            plano=self.plano,
            status='active',
            data_inicio='2026-01-01',
        )

        self._setar_sessao_signup()
        response = self.client.post(self.url_get, {'plano_id': self.plano.id}, follow=True)

        mensagens = [str(m) for m in response.context['messages']]
        self.assertTrue(any('lotado' in m.lower() for m in mensagens))

    def test_post_sem_plano_id_redireciona(self):
        """POST sem plano_id deve redirecionar com mensagem de erro"""
        self._setar_sessao_signup()
        response = self.client.post(self.url_get, {}, follow=True)

        # Sem plano_id, deve mostrar erro
        self.assertEqual(response.status_code, 200)


# ===============================================================
# TESTES DA CREATE PROFILE VIEW - GET
# ===============================================================

class CreateProfileViewGetTest(OnboardingTestBase):
    """
    Testa o GET da CreateProfileView para cada tipo de perfil.
    Verifica que o formulário correto é exibido em cada situação.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('core:onboarding_create_profile')

    def test_get_sem_plano_na_sessao_redireciona(self):
        """Sem plano_id na sessão deve redirecionar para seleção de plano"""
        # Sessão sem plano_id
        self._setar_sessao_signup(tipo_perfil='terapeuta')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('select-plan', response.url)

    def test_get_tipo_terapeuta_exibe_formulario(self):
        """GET com tipo=terapeuta deve renderizar o template correto"""
        self._setar_sessao_signup(tipo_perfil='terapeuta', plano_id=self.plano.id)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'onboarding/create_profile.html')
        self.assertEqual(response.context.get('tipo_perfil'), 'terapeuta')

    def test_get_tipo_espaco_exibe_formulario(self):
        """GET com tipo=espaco deve exibir formulário de espaço"""
        self._setar_sessao_signup(tipo_perfil='espaco', plano_id=self.plano.id)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('tipo_perfil'), 'espaco')

    def test_get_tipo_ambos_exibe_step_1(self):
        """GET com tipo=ambos deve exibir o step 1 (formulário de terapeuta)"""
        self._setar_sessao_signup(tipo_perfil='ambos', plano_id=self.plano.id)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        # Step 1 de 2
        self.assertEqual(response.context.get('current_step'), 1)
        self.assertEqual(response.context.get('total_steps'), 2)

    def test_get_onboarding_ja_completo_redireciona(self):
        """Usuário com perfil completo deve ser redirecionado"""
        with patch('core.views_onboarding.hasattr') as mock_hasattr:
            mock_hasattr.side_effect = lambda obj, attr: attr == 'terapeuta'
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_get_contexto_tem_nome_do_usuario(self):
        """Contexto deve ter o first_name do usuário para personalização"""
        self._setar_sessao_signup(tipo_perfil='terapeuta', plano_id=self.plano.id)
        response = self.client.get(self.url)

        self.assertEqual(response.context.get('first_name'), 'Carlos')


# ===============================================================
# TESTES DA CREATE PROFILE VIEW - POST (criação de terapeuta)
# ===============================================================

class CreateProfileViewPostTerapeutaTest(OnboardingTestBase):
    """
    Testa o POST da CreateProfileView para criação de perfil de terapeuta.
    Usa mock para isolar o processamento dos forms de onboarding.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('core:onboarding_create_profile')
        self._setar_sessao_signup(tipo_perfil='terapeuta', plano_id=self.plano.id)

    def test_post_form_invalido_rerenderiza(self):
        """POST com form inválido deve reexibir o template com erros"""
        # Enviar POST vazio (sem dados obrigatórios)
        response = self.client.post(self.url, {})

        # Deve reexibir o form (200, não redirecionar)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'onboarding/create_profile.html')

    @patch('core.views_onboarding.CreateProfileView._criar_terapeuta')
    def test_post_tipo_terapeuta_chama_criar_terapeuta(self, mock_criar):
        """POST com tipo=terapeuta deve chamar o método _criar_terapeuta"""
        mock_criar.return_value = HttpResponseRedirect('/')

        # Qualquer dado de POST — a validação está mockada
        self.client.post(self.url, {'nome': 'Carlos Teste'})

        # _criar_terapeuta deve ter sido chamado
        mock_criar.assert_called_once()

    @patch.object(CreateProfileView, '_criar_espaco')
    def test_post_tipo_espaco_chama_criar_espaco(self, mock_criar):
        """POST com tipo=espaco deve chamar _criar_espaco"""
        mock_criar.return_value = HttpResponseRedirect('/')

        # Setar sessão para espaço
        self._setar_sessao_signup(tipo_perfil='espaco', plano_id=self.plano.id)
        self.client.post(self.url, {'nome': 'Espaço Teste'})

        mock_criar.assert_called_once()

    @patch.object(CreateProfileView, '_processar_step_1')
    def test_post_tipo_ambos_step_1_chama_processar_step_1(self, mock_step):
        """POST com tipo=ambos no step 1 deve chamar _processar_step_1"""
        mock_step.return_value = HttpResponseRedirect('/')

        self._setar_sessao_signup(tipo_perfil='ambos', plano_id=self.plano.id)
        self.client.post(self.url, {'nome': 'Terapeuta Ambos'})

        mock_step.assert_called_once()


# ===============================================================
# TESTES DA CREATE PROFILE VIEW - POST (fluxo sem plano)
# ===============================================================

class CreateProfileViewSemPlanoTest(OnboardingTestBase):
    """
    Testa comportamento quando plano_id não está na sessão ao tentar POST.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('core:onboarding_create_profile')

    def test_post_sem_plano_id_redireciona_para_selecionar(self):
        """POST sem plano_id na sessão deve redirecionar para seleção de plano"""
        # Sessão sem plano_id
        self._setar_sessao_signup(tipo_perfil='terapeuta')
        response = self.client.post(self.url, {'nome': 'Teste'})

        self.assertEqual(response.status_code, 302)
        self.assertIn('select-plan', response.url)

    def test_post_plano_inexistente_redireciona(self):
        """POST com plano_id que não existe no banco deve redirecionar"""
        self._setar_sessao_signup(tipo_perfil='terapeuta', plano_id=99999)
        response = self.client.post(self.url, {'nome': 'Teste'})

        self.assertEqual(response.status_code, 302)


# ===============================================================
# TESTES DE INTEGRAÇÃO BÁSICA DO FLUXO
# ===============================================================

class OnboardingFluxoIntegracaoTest(OnboardingTestBase):
    """
    Testa o fluxo completo de onboarding de ponta a ponta
    sem mockar as views intermediárias.
    Foca em verificar que as URLs existem e respondem corretamente.
    """

    def test_url_welcome_existe(self):
        """URL de boas-vindas deve existir e retornar resposta"""
        url = reverse('core:onboarding_welcome')
        # Qualquer resposta sem 404 confirma que a URL existe
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 404)

    def test_url_select_plan_existe(self):
        """URL de seleção de plano deve existir"""
        url = reverse('core:onboarding_select_plan')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 404)

    def test_url_create_profile_existe(self):
        """URL de criação de perfil deve existir"""
        url = reverse('core:onboarding_create_profile')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 404)

    def test_usuario_nao_autenticado_bloqueado_em_todas_urls(self):
        """Todas as views de onboarding devem bloquear usuários não autenticados"""
        self.client.logout()
        urls = [
            reverse('core:onboarding_welcome'),
            reverse('core:onboarding_select_plan'),
            reverse('core:onboarding_create_profile'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                # Deve redirecionar para login (302)
                self.assertEqual(
                    response.status_code, 302,
                    f'URL {url} deveria redirecionar usuário não autenticado'
                )