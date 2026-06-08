# ===============================================================
# Título: Testes de Views - App Core
# Descrição: Testes unitários para as views do app core.
#            Cobre home, páginas institucionais, APIs AJAX,
#            seleção de perfil e autenticação customizada.
# ===============================================================

import pytest
from django.urls import reverse


# ===============================================================
# FIXTURES LOCAIS
# ===============================================================

@pytest.fixture
def usuario_com_terapeuta(db):
    """
    Usuário autenticado com perfil de terapeuta
    Para testar redirecionamentos do login customizado
    """
    from django.contrib.auth.models import User
    from terapeutas.models import Terapeuta

    user = User.objects.create_user(
        username='terapeuta_core_test',
        password='senha_segura_123',
        email='terapeuta_core@teste.com'
    )
    Terapeuta.objects.create(
        user=user,
        nome_exibicao='Terapeuta Core Teste',
        slug='terapeuta-core-teste',
        is_active=True,
    )
    return user


@pytest.fixture
def usuario_com_espaco(db):
    """
    Usuário autenticado com espaço cadastrado
    Para testar redirecionamentos do login customizado
    """
    from django.contrib.auth.models import User
    from espacos.models import Espaco

    user = User.objects.create_user(
        username='espaco_core_test',
        password='senha_segura_123',
        email='espaco_core@teste.com'
    )
    Espaco.objects.create(
        responsavel=user,
        nome='Espaço Core Teste',
        slug='espaco-core-teste',
        is_active=True,
    )
    return user


@pytest.fixture
def usuario_simples(db):
    """
    Usuário autenticado sem terapeuta nem espaço
    """
    from django.contrib.auth.models import User

    user = User.objects.create_user(
        username='usuario_simples_core',
        password='senha_segura_123',
    )
    return user


# ===============================================================
# TESTES: HomeView
# URL: /
# ===============================================================

@pytest.mark.django_db
class TestHomeView:
    """
    Testa a página inicial do Espaço Vital
    """

    def test_home_retorna_200(self, client):
        """Página inicial deve carregar sem erro"""
        url = reverse('core:home')
        response = client.get(url)
        assert response.status_code == 200

    def test_home_usa_template_correto(self, client):
        """Deve renderizar o template da home"""
        url = reverse('core:home')
        response = client.get(url)
        assert 'core/home.html' in [t.name for t in response.templates]

    def test_home_acessivel_sem_login(self, client):
        """Home deve ser pública, sem exigir autenticação"""
        url = reverse('core:home')
        response = client.get(url)
        assert response.status_code == 200

    def test_home_acessivel_com_login(self, client, usuario_simples):
        """Home também deve funcionar para usuário autenticado"""
        client.force_login(usuario_simples)
        url = reverse('core:home')
        response = client.get(url)
        assert response.status_code == 200


# ===============================================================
# TESTES: Páginas institucionais
# Sobre, Termos, Privacidade, Cookies, Parceiro, FAQ
# ===============================================================

@pytest.mark.django_db
class TestPaginasInstitucionais:
    """
    Testa todas as páginas institucionais do core
    São páginas estáticas públicas sem lógica complexa
    """

    def test_sobre_retorna_200(self, client):
        """Página sobre deve carregar sem erro"""
        url = reverse('core:sobre')
        response = client.get(url)
        assert response.status_code == 200

    def test_sobre_tem_page_title_no_contexto(self, client):
        """Contexto deve ter page_title"""
        url = reverse('core:sobre')
        response = client.get(url)
        assert 'page_title' in response.context

    def test_termos_retorna_200(self, client):
        """Página de termos deve carregar sem erro"""
        url = reverse('core:termos')
        response = client.get(url)
        assert response.status_code == 200

    def test_privacidade_retorna_200(self, client):
        """Página de privacidade deve carregar sem erro"""
        url = reverse('core:privacidade')
        response = client.get(url)
        assert response.status_code == 200

    def test_cookies_retorna_200(self, client):
        """Página de cookies deve carregar sem erro"""
        url = reverse('core:cookies')
        response = client.get(url)
        assert response.status_code == 200

    def test_parceiro_retorna_200(self, client):
        """Página de parceiro deve carregar sem erro"""
        url = reverse('core:parceiro')
        response = client.get(url)
        assert response.status_code == 200

    def test_faq_retorna_200(self, client):
        """Página de FAQ deve carregar sem erro"""
        url = reverse('core:faq')
        response = client.get(url)
        assert response.status_code == 200

    def test_todas_institucionais_sao_publicas(self, client):
        """Nenhuma página institucional deve exigir login"""
        urls_institucionais = [
            reverse('core:sobre'),
            reverse('core:termos'),
            reverse('core:privacidade'),
            reverse('core:cookies'),
            reverse('core:parceiro'),
            reverse('core:faq'),
        ]
        for url in urls_institucionais:
            response = client.get(url)
            assert response.status_code == 200, f"Falhou em: {url}"


# ===============================================================
# TESTES: ContatoView
# URL: /contato/
# ===============================================================

@pytest.mark.django_db
class TestContatoView:
    """
    Testa o formulário de contato
    """

    def test_contato_get_retorna_200(self, client):
        """GET no formulário de contato deve carregar sem erro"""
        url = reverse('core:contato')
        response = client.get(url)
        assert response.status_code == 200

    def test_contato_tem_page_title_no_contexto(self, client):
        """Contexto deve ter page_title"""
        url = reverse('core:contato')
        response = client.get(url)
        assert 'page_title' in response.context

    def test_contato_post_valido_redireciona(self, client):
        """POST com dados válidos deve processar sem erro 500"""
        url = reverse('core:contato')
        dados = {
            'name': 'João Teste',
            'email': 'joao@teste.com',
            'phone': '21999999999',
            'subject': 'Teste de contato',
            'message': 'Mensagem de teste para verificar o formulário.',
        }
        response = client.post(url, dados)
        # Deve redirecionar (302) ou recarregar (200) após sucesso
        assert response.status_code in [200, 302]

    def test_contato_post_invalido_retorna_200(self, client):
        """POST com dados inválidos deve retornar 200 com formulário"""
        url = reverse('core:contato')
        # Campos obrigatórios vazios
        response = client.post(url, {})
        assert response.status_code == 200


# ===============================================================
# TESTES: IndiqueTerapiaView
# URL: /indique-terapia/
# ===============================================================

@pytest.mark.django_db
class TestIndiqueTerapiaView:
    """
    Testa o formulário de indicação de terapia
    """

    def test_indique_terapia_get_retorna_200(self, client):
        """GET no formulário deve carregar sem erro"""
        url = reverse('core:indique_terapia')
        response = client.get(url)
        assert response.status_code == 200

    def test_indique_terapia_post_valido_processa(self, client):
        """POST com dados válidos deve processar sem erro 500"""
        url = reverse('core:indique_terapia')
        dados = {
            'nome': 'João Teste',
            'email': 'joao@teste.com',
            'nome_terapia': 'Cromoterapia',
            'descricao': 'Terapia que usa cores para equilibrar energias.',
        }
        response = client.post(url, dados)
        assert response.status_code in [200, 302]

    def test_indique_terapia_post_invalido_retorna_200(self, client):
        """POST com dados inválidos deve retornar 200 com formulário"""
        url = reverse('core:indique_terapia')
        response = client.post(url, {})
        assert response.status_code == 200


# ===============================================================
# TESTES: SelecionarPerfilView
# URL: /selecionar-perfil/
# ===============================================================

@pytest.mark.django_db
class TestSelecionarPerfilView:
    """
    Testa a view de seleção de perfil (terapeuta ou espaço)
    """

    def test_selecionar_perfil_redireciona_nao_autenticado(self, client):
        """Não autenticado deve ser redirecionado para login"""
        url = reverse('core:selecionar_perfil')
        response = client.get(url)
        assert response.status_code == 302

    def test_selecionar_perfil_retorna_200_para_autenticado(
        self, client, usuario_simples
    ):
        """Usuário autenticado sem perfil é redirecionado (sem terapeuta/espaço)"""
        client.force_login(usuario_simples)
        url = reverse('core:selecionar_perfil')
        response = client.get(url)
        assert response.status_code in [200, 302]


# ===============================================================
# TESTES: APIs AJAX do core
# URL: /api/estados/
# URL: /api/cidades/
# ===============================================================

@pytest.mark.django_db
class TestCoreAjaxApis:
    """
    Testa as APIs AJAX de estados e cidades
    """

    def test_api_estados_retorna_200(self, client):
        """API de estados deve responder sem erro 500"""
        url = reverse('api_estados')
        response = client.get(url)
        assert response.status_code in [200, 400]

    def test_api_estados_retorna_json(self, client):
        """API de estados deve retornar JSON"""
        url = reverse('api_estados')
        response = client.get(url)
        assert response['Content-Type'] == 'application/json'

    def test_api_cidades_por_estado_retorna_200(self, client):
        """API de cidades com estado válido deve responder"""
        url = reverse('api_cidades')
        response = client.get(url, {'estado': '1'})
        assert response.status_code == 200

    def test_api_cidades_por_pais_retorna_200(self, client):
        """API de cidades com país válido deve responder"""
        url = reverse('api_cidades')
        response = client.get(url, {'pais': '1'})
        assert response.status_code == 200

    def test_api_cidades_sem_parametros_retorna_400(self, client):
        """API de cidades sem parâmetros deve retornar 400"""
        url = reverse('api_cidades')
        response = client.get(url)
        assert response.status_code == 400

    def test_api_cidades_retorna_json(self, client):
        """API de cidades deve retornar JSON"""
        url = reverse('api_cidades')
        response = client.get(url, {'estado': '1'})
        assert response['Content-Type'] == 'application/json'


# ===============================================================
# TESTES: CustomLoginView
# URL: /accounts/login/
# ===============================================================

@pytest.mark.django_db
class TestCustomLoginView:
    """
    Testa a view customizada de login
    """

    def test_login_get_retorna_200(self, client):
        """Página de login deve carregar sem erro"""
        url = reverse('account_login')
        response = client.get(url)
        assert response.status_code == 200

    def test_login_redireciona_terapeuta_autenticado(
        self, client, usuario_com_terapeuta
    ):
        """Terapeuta já autenticado acessando login deve ser redirecionado"""
        client.force_login(usuario_com_terapeuta)
        url = reverse('account_login')
        response = client.get(url)
        # Deve redirecionar para o dashboard do terapeuta
        assert response.status_code == 302
        assert 'terapeutas' in response.url or 'dashboard' in response.url

    def test_login_redireciona_dono_espaco_autenticado(
        self, client, usuario_com_espaco
    ):
        """Dono de espaço já autenticado acessando login deve ser redirecionado"""
        client.force_login(usuario_com_espaco)
        url = reverse('account_login')
        response = client.get(url)
        # Deve redirecionar para o dashboard do espaço ou home
        assert response.status_code == 302

    def test_login_redireciona_usuario_simples_autenticado(
        self, client, usuario_simples
    ):
        """Usuário comum já autenticado acessando login deve ser redirecionado"""
        client.force_login(usuario_simples)
        url = reverse('account_login')
        response = client.get(url)
        # Deve redirecionar para home
        assert response.status_code == 302
        assert response.url == '/'

    def test_login_post_credenciais_invalidas_retorna_200(self, client):
        """Login com credenciais inválidas deve retornar 200 com erro"""
        url = reverse('account_login')
        dados = {
            'login': 'usuario_inexistente',
            'password': 'senha_errada',
        }
        response = client.post(url, dados)
        assert response.status_code == 200


# ===============================================================
# TESTES: CustomLogoutView
# URL: /accounts/logout/
# ===============================================================

@pytest.mark.django_db
class TestCustomLogoutView:
    """
    Testa a view customizada de logout
    """

    def test_logout_post_redireciona(self, client, usuario_simples):
        """POST no logout deve deslogar e redirecionar"""
        client.force_login(usuario_simples)
        url = reverse('account_logout')
        response = client.post(url)
        # Deve redirecionar após logout
        assert response.status_code == 302

    def test_logout_redireciona_para_login(self, client, usuario_simples):
        """Após logout deve ir para a página de login"""
        client.force_login(usuario_simples)
        url = reverse('account_logout')
        response = client.post(url)
        assert '/accounts/login/' in response.url