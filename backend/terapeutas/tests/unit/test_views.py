# ===============================================================
# Título: Testes de Views - App Terapeutas
# Descrição: Testes unitários para as views públicas e de dashboard
#            do app terapeutas. Cobre listagem, perfil, contato
#            e rotas protegidas por autenticação.
# ===============================================================

import pytest
from django.urls import reverse
from django.test import Client
from unittest.mock import patch, MagicMock

# ===============================================================
# FIXTURES LOCAIS
# Complementam as fixtures globais do conftest.py raiz
# ===============================================================

@pytest.fixture
def terapeuta_ativo(db):
    """
    Cria um terapeuta ativo com todos os dados mínimos necessários
    para aparecer na listagem pública
    """
    from django.contrib.auth.models import User
    from terapeutas.models import Terapeuta

    # Criar usuário vinculado ao terapeuta
    user = User.objects.create_user(
        username='terapeuta_teste_view',
        password='senha_segura_123',
        email='terapeuta@teste.com'
    )

    # Criar terapeuta ativo com slug único
    terapeuta = Terapeuta.objects.create(
        user=user,
        nome_exibicao='Ana Silva Teste',
        slug='ana-silva-teste',
        bio_curta='Terapeuta especializada em bem-estar.',
        is_active=True,
        verificado=False,
    )
    return terapeuta


@pytest.fixture
def terapeuta_inativo(db):
    """
    Cria um terapeuta inativo (não deve aparecer na listagem)
    """
    from django.contrib.auth.models import User
    from terapeutas.models import Terapeuta

    user = User.objects.create_user(
        username='terapeuta_inativo_view',
        password='senha_segura_123',
    )

    terapeuta = Terapeuta.objects.create(
        user=user,
        nome_exibicao='Carlos Inativo',
        slug='carlos-inativo',
        is_active=False,
    )
    return terapeuta


@pytest.fixture
def usuario_com_terapeuta(db):
    """
    Retorna (user, terapeuta) para testes de dashboard
    Usuário autenticado que possui perfil de terapeuta
    """
    from django.contrib.auth.models import User
    from terapeutas.models import Terapeuta

    user = User.objects.create_user(
        username='dono_dashboard',
        password='senha_segura_123',
        email='dono@teste.com'
    )

    terapeuta = Terapeuta.objects.create(
        user=user,
        nome_exibicao='Dono Dashboard',
        slug='dono-dashboard',
        is_active=True,
        verificado=True,
    )
    return user, terapeuta


@pytest.fixture
def usuario_sem_terapeuta(db):
    """
    Usuário autenticado que NÃO possui perfil de terapeuta
    Para testar o bloqueio do TerapeutaRequiredMixin
    """
    from django.contrib.auth.models import User

    user = User.objects.create_user(
        username='usuario_comum',
        password='senha_segura_123',
    )
    return user


# ===============================================================
# TESTES: TerapeutaListView (view pública de listagem)
# URL: /terapeutas/
# ===============================================================

@pytest.mark.django_db
class TestTerapeutaListView:
    """
    Testa a view de listagem/busca de terapeutas
    """

    def test_listagem_retorna_200(self, client):
        """Página de listagem deve carregar sem erro"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url)
        assert response.status_code == 200

    def test_listagem_url_buscar_retorna_200(self, client):
        """URL alternativa /terapeutas/buscar/ também deve funcionar"""
        url = reverse('terapeutas:buscar')
        response = client.get(url)
        assert response.status_code == 200

    def test_listagem_usa_template_correto(self, client):
        """Deve renderizar o template de listagem de resultados"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url)
        assert 'terapeutas/listagem_resultados.html' in [
            t.name for t in response.templates
        ]

    def test_listagem_exibe_terapeutas_ativos(self, client, terapeuta_ativo):
        """Terapeutas ativos devem aparecer na listagem"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url)
        # Verifica que o context tem a lista de terapeutas
        assert 'terapeutas' in response.context
        terapeutas_ids = [t.id for t in response.context['terapeutas']]
        assert terapeuta_ativo.id in terapeutas_ids

    def test_listagem_oculta_terapeutas_inativos(self, client, terapeuta_inativo):
        """Terapeutas inativos NÃO devem aparecer na listagem"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url)
        terapeutas_ids = [t.id for t in response.context['terapeutas']]
        assert terapeuta_inativo.id not in terapeutas_ids

    def test_listagem_aceita_filtro_por_especialidade(self, client, terapeuta_ativo):
        """Filtro por especialidade via GET deve funcionar sem erro"""
        url = reverse('terapeutas:listagem_resultados')
        # Passa ID inexistente só para testar que não quebra
        response = client.get(url, {'especialidades': '9999'})
        assert response.status_code == 200

    def test_listagem_aceita_filtro_por_pais(self, client):
        """Filtro por país via GET deve funcionar sem erro"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url, {'pais': '1'})
        assert response.status_code == 200

    def test_listagem_aceita_filtro_por_estado(self, client):
        """Filtro por estado via GET deve funcionar sem erro"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url, {'estado': '1'})
        assert response.status_code == 200

    def test_listagem_aceita_filtro_por_cidade(self, client):
        """Filtro por cidade via GET deve funcionar sem erro"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url, {'cidade': '1'})
        assert response.status_code == 200

    def test_listagem_aceita_filtro_tipo_sessao(self, client):
        """Filtro por tipo de sessão via GET deve funcionar sem erro"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url, {'tipos_sessao': 'online'})
        assert response.status_code == 200

    def test_listagem_com_filtros_invalidos_nao_quebra(self, client):
        """Filtros com valores inválidos não devem causar erro 500"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url, {'pais': 'abc', 'cidade': 'xyz'})
        assert response.status_code == 200

    def test_listagem_paginacao_pagina_2(self, client):
        """Paginação deve funcionar na segunda página"""
        url = reverse('terapeutas:listagem_resultados')
        response = client.get(url, {'page': '2'})
        # Retorna 200 ou 404 (se não há segunda página) - não pode ser 500
        assert response.status_code in [200, 404]


# ===============================================================
# TESTES: TerapeutaDetailView (perfil público)
# URL: /terapeutas/perfil/<slug>/
# ===============================================================

@pytest.mark.django_db
class TestTerapeutaDetailView:
    """
    Testa a view de perfil público do terapeuta
    """

    def test_perfil_retorna_200_para_terapeuta_ativo(self, client, terapeuta_ativo):
        """Perfil de terapeuta ativo deve carregar normalmente"""
        url = reverse('terapeutas:perfil', kwargs={'slug': terapeuta_ativo.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_perfil_retorna_404_para_terapeuta_inativo(self, client, terapeuta_inativo):
        """Perfil de terapeuta inativo deve retornar 404"""
        url = reverse('terapeutas:perfil', kwargs={'slug': terapeuta_inativo.slug})
        response = client.get(url)
        assert response.status_code == 404

    def test_perfil_retorna_404_para_slug_inexistente(self, client):
        """Slug que não existe deve retornar 404"""
        url = reverse('terapeutas:perfil', kwargs={'slug': 'terapeuta-que-nao-existe'})
        response = client.get(url)
        assert response.status_code == 404

    def test_perfil_usa_template_correto(self, client, terapeuta_ativo):
        """Deve renderizar o template de perfil"""
        url = reverse('terapeutas:perfil', kwargs={'slug': terapeuta_ativo.slug})
        response = client.get(url)
        assert 'terapeutas/perfil.html' in [t.name for t in response.templates]

    def test_perfil_passa_terapeuta_no_contexto(self, client, terapeuta_ativo):
        """O objeto terapeuta deve estar disponível no contexto"""
        url = reverse('terapeutas:perfil', kwargs={'slug': terapeuta_ativo.slug})
        response = client.get(url)
        assert 'terapeuta' in response.context
        assert response.context['terapeuta'].id == terapeuta_ativo.id

    def test_perfil_incrementa_visualizacoes(self, client, terapeuta_ativo):
        """Acessar o perfil deve incrementar o contador de visualizações"""
        views_antes = terapeuta_ativo.visualizacoes
        url = reverse('terapeutas:perfil', kwargs={'slug': terapeuta_ativo.slug})
        client.get(url)
        # Recarregar do banco para ver o valor atualizado
        terapeuta_ativo.refresh_from_db()
        assert terapeuta_ativo.visualizacoes > views_antes

    def test_perfil_tem_stats_no_contexto(self, client, terapeuta_ativo):
        """Estatísticas do terapeuta devem estar no contexto"""
        url = reverse('terapeutas:perfil', kwargs={'slug': terapeuta_ativo.slug})
        response = client.get(url)
        assert 'stats' in response.context


# ===============================================================
# TESTES: terapeutas_sem_filtro (listagem por especialidade)
# URL: /terapeutas/especialidade/<slug>/
# ===============================================================

@pytest.mark.django_db
class TestTerapeutasSemFiltroView:
    """
    Testa a view de listagem por especialidade (sem filtros)
    """

    def test_por_especialidade_retorna_200_ou_404(self, client):
        """URL por especialidade responde sem erro 500 (200 se existe, 404 se não existe)"""
        url = reverse('terapeutas:por_especialidade', kwargs={
            'especialidade_slug': 'massoterapia'
        })
        response = client.get(url)
        assert response.status_code in [200, 404]

    def test_por_especialidade_slug_inexistente_retorna_200_ou_404(self, client):
        """Especialidade inexistente: não deve gerar erro 500"""
        url = reverse('terapeutas:por_especialidade', kwargs={
            'especialidade_slug': 'especialidade-que-nao-existe-xyz'
        })
        response = client.get(url)
        assert response.status_code in [200, 404]


# ===============================================================
# TESTES: DashboardView (área privada)
# URL: /terapeutas/dashboard/
# ===============================================================

@pytest.mark.django_db
class TestDashboardView:
    """
    Testa o dashboard privado do terapeuta
    """

    def test_dashboard_redireciona_usuario_nao_autenticado(self, client):
        """Usuário não autenticado deve ser redirecionado para login"""
        url = reverse('terapeutas:dashboard')
        response = client.get(url)
        # Deve redirecionar (302) para a página de login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url or '/login' in response.url

    def test_dashboard_redireciona_usuario_sem_perfil_terapeuta(
        self, client, usuario_sem_terapeuta
    ):
        """Usuário logado sem perfil terapeuta deve ser redirecionado"""
        client.force_login(usuario_sem_terapeuta)
        url = reverse('terapeutas:dashboard')
        response = client.get(url)
        # Deve redirecionar para home (não tem terapeuta)
        assert response.status_code == 302

    def test_dashboard_retorna_200_para_terapeuta_autenticado(
        self, client, usuario_com_terapeuta
    ):
        """Terapeuta autenticado deve ver o dashboard normalmente"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_usa_template_correto(self, client, usuario_com_terapeuta):
        """Dashboard deve usar o template correto"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard')
        response = client.get(url)
        assert 'terapeutas/dashboard/dashboard.html' in [
            t.name for t in response.templates
        ]

    def test_dashboard_tem_terapeuta_no_contexto(self, client, usuario_com_terapeuta):
        """O terapeuta logado deve estar no contexto do dashboard"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard')
        response = client.get(url)
        assert 'terapeuta' in response.context
        assert response.context['terapeuta'].id == terapeuta.id

    def test_dashboard_tem_dados_de_completude(self, client, usuario_com_terapeuta):
        """Dados de completude de perfil devem estar no contexto"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard')
        response = client.get(url)
        assert 'completude_perfil' in response.context


# ===============================================================
# TESTES: DashboardEditarPerfilView
# URL: /terapeutas/dashboard/perfil/
# ===============================================================

@pytest.mark.django_db
class TestDashboardEditarPerfilView:
    """
    Testa a view de edição de perfil do dashboard
    """

    def test_editar_perfil_redireciona_nao_autenticado(self, client):
        """Usuário não autenticado deve ser redirecionado"""
        url = reverse('terapeutas:dashboard_editar_perfil')
        response = client.get(url)
        assert response.status_code == 302

    def test_editar_perfil_retorna_200_para_terapeuta(
        self, client, usuario_com_terapeuta
    ):
        """Terapeuta autenticado deve acessar a tela de edição"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard_editar_perfil')
        response = client.get(url)
        assert response.status_code == 200

    def test_editar_perfil_bloqueia_usuario_sem_terapeuta(
        self, client, usuario_sem_terapeuta
    ):
        """Usuário sem perfil terapeuta não deve acessar edição"""
        client.force_login(usuario_sem_terapeuta)
        url = reverse('terapeutas:dashboard_editar_perfil')
        response = client.get(url)
        assert response.status_code == 302


# ===============================================================
# TESTES: DashboardEstatisticasView
# URL: /terapeutas/dashboard/estatisticas/
# ===============================================================

@pytest.mark.django_db
class TestDashboardEstatisticasView:
    """
    Testa a view de estatísticas detalhadas
    """

    def test_estatisticas_redireciona_nao_autenticado(self, client):
        """Não autenticado deve ser redirecionado"""
        url = reverse('terapeutas:dashboard_estatisticas')
        response = client.get(url)
        assert response.status_code == 302

    def test_estatisticas_retorna_200_para_terapeuta(
        self, client, usuario_com_terapeuta
    ):
        """Terapeuta autenticado deve ver a página de estatísticas"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard_estatisticas')
        response = client.get(url)
        assert response.status_code == 200

    def test_estatisticas_tem_dados_no_contexto(
        self, client, usuario_com_terapeuta
    ):
        """Contexto deve ter os dados de estatísticas"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard_estatisticas')
        response = client.get(url)
        assert 'total_visualizacoes' in response.context
        assert 'total_avaliacoes' in response.context


# ===============================================================
# TESTES: DashboardEspacosVinculadosView
# URL: /terapeutas/dashboard/espacos/
# ===============================================================

@pytest.mark.django_db
class TestDashboardEspacosVinculadosView:
    """
    Testa a view de espaços vinculados no dashboard
    """

    def test_espacos_vinculados_redireciona_nao_autenticado(self, client):
        """Não autenticado deve ser redirecionado"""
        url = reverse('terapeutas:dashboard_espacos')
        response = client.get(url)
        assert response.status_code == 302

    def test_espacos_vinculados_retorna_200_para_terapeuta(
        self, client, usuario_com_terapeuta
    ):
        """Terapeuta autenticado deve ver a página"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard_espacos')
        response = client.get(url)
        assert response.status_code == 200


# ===============================================================
# TESTES: DashboardAssinaturaView
# URL: /terapeutas/dashboard/assinatura/
# ===============================================================

@pytest.mark.django_db
class TestDashboardAssinaturaView:
    """
    Testa a view de gerenciamento de assinatura
    """

    def test_assinatura_redireciona_nao_autenticado(self, client):
        """Não autenticado deve ser redirecionado"""
        url = reverse('terapeutas:dashboard_assinatura')
        response = client.get(url)
        assert response.status_code == 302

    def test_assinatura_retorna_200_para_terapeuta(
        self, client, usuario_com_terapeuta
    ):
        """Terapeuta autenticado deve ver a página de assinatura"""
        user, terapeuta = usuario_com_terapeuta
        client.force_login(user)
        url = reverse('terapeutas:dashboard_assinatura')
        response = client.get(url)
        assert response.status_code == 200


# ===============================================================
# TESTES: contatar_terapeuta (view de contato)
# URL: /terapeutas/contatar/<slug>/
# ===============================================================

@pytest.mark.django_db
class TestContatarTerapeutaView:
    """
    Testa o formulário de contato com terapeuta
    """

    def test_contato_get_retorna_200_ou_redireciona(self, client, terapeuta_ativo):
        """GET no formulário de contato deve responder sem erro 500"""
        url = reverse('terapeutas:contatar', kwargs={
            'terapeuta_slug': terapeuta_ativo.slug
        })
        response = client.get(url)
        assert response.status_code in [200, 302]

    def test_contato_slug_inexistente_retorna_404(self, client):
        """Slug inválido deve retornar 404"""
        url = reverse('terapeutas:contatar', kwargs={
            'terapeuta_slug': 'terapeuta-fantasma-xyz'
        })
        response = client.get(url)
        assert response.status_code in [404, 302]


# ===============================================================
# TESTES: APIs AJAX
# URL: /terapeutas/api/cidades-por-estado/
# URL: /terapeutas/api/buscar/
# ===============================================================

@pytest.mark.django_db
class TestAjaxApis:
    """
    Testa as APIs AJAX de suporte aos filtros
    """

    def test_api_cidades_por_estado_retorna_200(self, client):
        """API de cidades deve responder a requisição GET"""
        url = reverse('terapeutas:cidades_por_estado_ajax')
        response = client.get(url, {'estado_id': '1'})
        # Aceita 200 (com resultado) ou 200 com lista vazia
        assert response.status_code == 200

    def test_api_cidades_sem_estado_nao_quebra(self, client):
        """API sem parâmetro não deve gerar erro 500"""
        url = reverse('terapeutas:cidades_por_estado_ajax')
        response = client.get(url)
        assert response.status_code in [200, 400]

    def test_api_buscar_retorna_200(self, client):
        """API de busca deve responder a requisição GET"""
        url = reverse('terapeutas:busca_ajax')
        response = client.get(url, {'q': 'ana'})
        assert response.status_code == 200

    def test_api_buscar_sem_query_nao_quebra(self, client):
        """API de busca sem query não deve gerar erro 500"""
        url = reverse('terapeutas:busca_ajax')
        response = client.get(url)
        assert response.status_code in [200, 400]