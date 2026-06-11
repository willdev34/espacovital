# ===============================================================
# Título: Testes das Views de Autenticação - Espaço Vital
# Descrição: Testes unitários para CustomLoginView e CustomLogoutView
#             que sobrescrevem o comportamento padrão do allauth
# Autor: Will
# Data: 09/06/2026
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from terapeutas.models import Terapeuta

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class AuthViewsTestBase(TestCase):
    """
    Base compartilhada entre os testes de autenticação.
    Cria usuários com diferentes tipos de perfil.
    """

    def setUp(self):
        """Cria usuários de teste antes de cada teste"""
        self.client = Client()

        # Usuário sem nenhum perfil (comum)
        self.user_comum = User.objects.create_user(
            username='usuario_comum',
            email='comum@teste.com',
            password='senha_segura_123',
        )

        # Usuário com perfil de terapeuta
        self.user_terapeuta = User.objects.create_user(
            username='usuario_terapeuta',
            email='terapeuta@teste.com',
            password='senha_segura_123',
        )
        self.terapeuta = Terapeuta.objects.create(
            user=self.user_terapeuta,
            nome_completo='Terapeuta Auth Teste',
            nome_exibicao='Terapeuta Auth',
            slug='terapeuta-auth-teste',
            bio_curta='Bio de teste.',
            bio_completa='<p>Bio completa.</p>',
            formacao='Formação de teste',
            is_active=True,
        )


# ===============================================================
# TESTES DO CUSTOM LOGIN VIEW - dispatch (usuário já autenticado)
# ===============================================================

class CustomLoginViewDispatchTest(AuthViewsTestBase):
    """
    Testa o dispatch da CustomLoginView:
    usuário já autenticado deve ser redirecionado sem ver o form de login.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('account_login')

    def test_usuario_nao_autenticado_ve_formulario_login(self):
        """Usuário não logado deve ver a página de login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usuario_comum_autenticado_redireciona_para_home(self):
        """Usuário logado sem perfil deve ir para a home"""
        self.client.login(username='usuario_comum', password='senha_segura_123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)

    def test_terapeuta_autenticado_redireciona_para_dashboard(self):
        """Terapeuta logado que tenta acessar login vai para o dashboard"""
        self.client.login(username='usuario_terapeuta', password='senha_segura_123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('dashboard', response.url)


# ===============================================================
# TESTES DO CUSTOM LOGIN VIEW - form_valid (após login)
# ===============================================================

class CustomLoginViewFormValidTest(AuthViewsTestBase):
    """
    Testa o redirecionamento após login bem sucedido
    baseado no tipo de perfil do usuário.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('account_login')

    def test_login_usuario_comum_redireciona_para_home(self):
        """Usuário sem perfil após login vai para home"""
        # Usar force_login para simular login direto
        self.client.force_login(self.user_comum)
        # Verificar que ao acessar login, redireciona para home
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_login_terapeuta_redireciona_para_dashboard_terapeuta(self):
        """Terapeuta após login vai para dashboard de terapeutas"""
        self.client.force_login(self.user_terapeuta)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('terapeutas', response.url)

    def test_post_login_credenciais_erradas_rerenderiza(self):
        """POST com credenciais inválidas deve reexibir o formulário"""
        dados = {
            'login': 'usuario_inexistente',
            'password': 'senha_errada',
        }
        response = self.client.post(self.url, dados)
        # Deve reexibir o form (200) ou redirecionar para login (302)
        self.assertIn(response.status_code, [200, 302])


# ===============================================================
# TESTES DO CUSTOM LOGOUT VIEW
# ===============================================================

class CustomLogoutViewTest(AuthViewsTestBase):
    """
    Testa a CustomLogoutView: logout com redirecionamento para login.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('account_logout')

    def test_logout_post_redireciona(self):
        """POST no logout deve redirecionar"""
        self.client.login(username='usuario_comum', password='senha_segura_123')
        response = self.client.post(self.url)
        # Deve redirecionar após logout
        self.assertEqual(response.status_code, 302)

    def test_logout_redireciona_para_login(self):
        """Após logout, deve redirecionar para a página de login"""
        self.client.login(username='usuario_comum', password='senha_segura_123')
        response = self.client.post(self.url)
        # URL de redirecionamento deve conter login
        self.assertIn('login', response.url)

    def test_logout_encerra_sessao(self):
        """Após logout, usuário não deve estar autenticado"""
        self.client.login(username='usuario_comum', password='senha_segura_123')
        self.client.post(self.url)

        # Tentar acessar área protegida deve redirecionar
        url_protegida = reverse('terapeutas:dashboard')
        response = self.client.get(url_protegida)
        self.assertEqual(response.status_code, 302)

    def test_logout_get_redireciona_ou_exibe_confirmacao(self):
        """GET no logout deve redirecionar ou mostrar confirmação"""
        self.client.login(username='usuario_comum', password='senha_segura_123')
        response = self.client.get(self.url)
        # Allauth pode exibir confirmação (200) ou redirecionar (302)
        self.assertIn(response.status_code, [200, 302])


# ===============================================================
# TESTES DE INTEGRAÇÃO DO FLUXO DE AUTENTICAÇÃO
# ===============================================================

class AuthFluxoIntegracaoTest(AuthViewsTestBase):
    """
    Testa o fluxo completo de autenticação:
    login → redirecionamento correto → logout → de volta ao login.
    """

    def test_url_login_existe(self):
        """URL de login deve existir"""
        url = reverse('account_login')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 404)

    def test_url_logout_existe(self):
        """URL de logout deve existir"""
        url = reverse('account_logout')
        self.client.login(username='usuario_comum', password='senha_segura_123')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 404)

    def test_fluxo_login_logout_usuario_comum(self):
        """Fluxo completo: login como comum, acessa home, faz logout"""
        # Login
        self.client.force_login(self.user_comum)

        # Acessa home autenticado
        home_response = self.client.get(reverse('core:home'))
        self.assertEqual(home_response.status_code, 200)

        # Logout
        logout_response = self.client.post(reverse('account_logout'))
        self.assertEqual(logout_response.status_code, 302)

    def test_fluxo_login_logout_terapeuta(self):
        """Fluxo completo: login como terapeuta, acessa dashboard, faz logout"""
        # Login como terapeuta
        self.client.force_login(self.user_terapeuta)

        # Acessa dashboard
        dashboard_response = self.client.get(reverse('terapeutas:dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)

        # Logout
        logout_response = self.client.post(reverse('account_logout'))
        self.assertEqual(logout_response.status_code, 302)

        # Verifica que não consegue mais acessar o dashboard
        response_apos_logout = self.client.get(reverse('terapeutas:dashboard'))
        self.assertEqual(response_apos_logout.status_code, 302)


# ===============================================================
# TESTES DIRETOS DOS MÉTODOS (sem passar pelo allauth)
# ===============================================================

from django.test import RequestFactory
from core.views_auth import CustomLoginView, CustomLogoutView


class CustomLoginViewMetodosTest(AuthViewsTestBase):
    """
    Testa os métodos internos da CustomLoginView diretamente,
    sem depender do fluxo completo do allauth.
    """

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_get_success_url_usuario_comum(self):
        """get_success_url deve retornar home para usuário comum"""
        request = self.factory.get('/')
        request.user = self.user_comum

        view = CustomLoginView()
        view.request = request

        url = view.get_success_url()
        self.assertEqual(url, '/')

    def test_get_success_url_terapeuta(self):
        """get_success_url deve retornar dashboard para terapeuta"""
        request = self.factory.get('/')
        request.user = self.user_terapeuta

        view = CustomLoginView()
        view.request = request

        url = view.get_success_url()
        self.assertIn('terapeutas', url)

    def test_get_success_url_usuario_com_ambos_perfis(self):
        """get_success_url deve retornar selecionar_perfil para usuário com dois perfis"""
        from espacos.models import Espaco
        from unittest.mock import PropertyMock, patch

        request = self.factory.get('/')
        request.user = self.user_terapeuta

        view = CustomLoginView()
        view.request = request

        # Simular que também tem espaço
        with patch.object(
            type(self.user_terapeuta),
            'espacos_gerenciados',
            new_callable=lambda: property(
                lambda self: type('obj', (object,), {
                    'filter': lambda *a, **kw: type('qs', (object,), {'exists': lambda self: True})()
                })()
            ),
            create=True
        ):
            url = view.get_success_url()
        # Deve ir para seleção de perfil
        self.assertIn('selecionar', url)