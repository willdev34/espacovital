# ===============================================================
# Título: Testes das Views do App Espacos
# Descrição: Testes unitários para EspacoListView, EspacoDetailView,
#             DashboardEspacoView, ContatoEspacoView e APIs AJAX
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Especialidade
from espacos.models import Espaco, Comodidade

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class EspacoViewsTestBase(TestCase):
    """
    Base compartilhada entre todos os testes do app espacos.
    Cria usuário, espaço e client configurados.
    """

    def setUp(self):
        """Cria usuário, espaço e client antes de cada teste"""
        self.client = Client()

        # Usuário visitante sem espaço
        self.visitante = User.objects.create_user(
            username='visitante_espaco',
            email='visitante@espaco.com',
            password='senha123',
        )

        # Usuário responsável pelo espaço
        self.user_espaco = User.objects.create_user(
            username='gestor_espaco',
            email='gestor@espaco.com',
            password='senha123',
            first_name='Pedro',
        )

        # Criar espaço ativo
        self.espaco = Espaco.objects.create(
            nome='Centro Holístico Teste',
            slug='centro-holistico-teste',
            descricao_breve='Espaço de terapias holísticas no centro da cidade.',
            descricao_completa='<p>Descrição completa do espaço.</p>',
            endereco='Rua das Terapias, 123',
            cep='20040-020',
            bairro='Centro',
            tipo_espaco='centro_holistico',
            responsavel=self.user_espaco,
            is_active=True,
        )

        # Criar especialidade para uso nos testes
        self.especialidade, _ = Especialidade.objects.get_or_create(
            nome='Meditação',
            defaults={
                'descricao_curta': 'Prática de meditação',
                'is_active': True,
            }
        )

    def _login_gestor(self):
        """Utilitário: faz login com o usuário gestor do espaço"""
        self.client.login(username='gestor_espaco', password='senha123')

    def _login_visitante(self):
        """Utilitário: faz login com usuário sem espaço"""
        self.client.login(username='visitante_espaco', password='senha123')


# ===============================================================
# TESTES DA ESPACO LIST VIEW
# ===============================================================

class EspacoListViewTest(EspacoViewsTestBase):
    """
    Testa a EspacoListView: busca avançada pública de espaços.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:busca_avancada')

    def test_listagem_acessivel_sem_login(self):
        """Busca de espaços deve ser pública"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de busca avançada"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'espacos/busca_avancada.html')

    def test_exibe_apenas_espacos_ativos(self):
        """Apenas espaços com is_active=True devem aparecer"""
        response = self.client.get(self.url)
        for espaco in response.context['espacos']:
            self.assertTrue(espaco.is_active)

    def test_nao_exibe_espacos_inativos(self):
        """Espaço inativo não deve aparecer"""
        # Criar espaço inativo
        user_inativo = User.objects.create_user(
            username='inativo_espaco', password='senha123'
        )
        Espaco.objects.create(
            nome='Espaço Inativo',
            slug='espaco-inativo-teste',
            descricao_breve='Inativo.',
            descricao_completa='<p>Inativo.</p>',
            endereco='Rua X',
            cep='20000-000',
            bairro='Bairro',
            tipo_espaco='clinica',
            responsavel=user_inativo,
            is_active=False,
        )
        response = self.client.get(self.url)
        slugs = [e.slug for e in response.context['espacos']]
        self.assertNotIn('espaco-inativo-teste', slugs)

    def test_contexto_tem_filtros_aplicados(self):
        """Contexto deve ter os filtros aplicados"""
        response = self.client.get(self.url)
        self.assertIn('filtros_aplicados', response.context)

    def test_contexto_tem_tipos_espaco(self):
        """Contexto deve ter os tipos de espaço para o filtro"""
        response = self.client.get(self.url)
        self.assertIn('tipos_espaco', response.context)

    def test_filtro_por_tipo_espaco(self):
        """Filtro por tipo de espaço deve funcionar sem erro"""
        response = self.client.get(self.url, {'tipo_espaco': 'clinica'})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_busca_texto(self):
        """Filtro por texto deve funcionar sem erro"""
        response = self.client.get(self.url, {'busca': 'holístico'})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_acessibilidade(self):
        """Filtro por acessibilidade deve funcionar"""
        response = self.client.get(self.url, {'acessibilidade': '1'})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_locacao(self):
        """Filtro por aceita locação deve funcionar"""
        response = self.client.get(self.url, {'locacao': '1'})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_especialidade_invalida_nao_quebra(self):
        """Filtro com especialidade inválida não deve causar erro 500"""
        response = self.client.get(self.url, {'terapias': ['abc', '999']})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_comodidade_invalida_nao_quebra(self):
        """Filtro com comodidade inválida não deve causar erro 500"""
        response = self.client.get(self.url, {'comodidades': ['abc', '999']})
        self.assertEqual(response.status_code, 200)

    def test_ordenacao_por_nome(self):
        """Parâmetro de ordenação deve ser aceito"""
        response = self.client.get(self.url, {'ordem': 'nome'})
        self.assertEqual(response.status_code, 200)

    def test_paginacao_funciona(self):
        """Segunda página deve retornar 200 ou 404"""
        response = self.client.get(self.url, {'page': 2})
        self.assertIn(response.status_code, [200, 404])


# ===============================================================
# TESTES DA ESPACO LISTAGEM SIMPLES VIEW
# ===============================================================

import unittest

class EspacoListagemSimplesViewTest(EspacoViewsTestBase):
    """
    Testa a EspacoListagemSimplesView: listagem sem filtros avançados.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:listagem_simples')

    def test_listagem_simples_acessivel(self):
        """Listagem simples deve ser pública e retornar 200"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de listagem simples"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'espacos/listagem_simples.html')

    def test_contexto_tem_espacos_por_regiao(self):
        """Contexto deve ter espaços agrupados por região"""
        response = self.client.get(self.url)
        self.assertIn('espacos_por_regiao', response.context)


# ===============================================================
# TESTES DA ESPACO DETAIL VIEW
# ===============================================================

class EspacoDetailViewTest(EspacoViewsTestBase):
    """
    Testa a EspacoDetailView: perfil público do espaço.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:detalhe', kwargs={'slug': self.espaco.slug})

    def test_perfil_acessivel_sem_login(self):
        """Perfil do espaço deve ser público"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de perfil do espaço"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'espacos/perfil_espaco.html')

    def test_retorna_404_para_espaco_inativo(self):
        """Espaço inativo deve retornar 404"""
        self.espaco.is_active = False
        self.espaco.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_retorna_404_para_slug_inexistente(self):
        """Slug inexistente deve retornar 404"""
        url = reverse('espacos:detalhe', kwargs={'slug': 'slug-que-nao-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_contexto_tem_espaco(self):
        """Contexto deve ter o objeto espaço"""
        response = self.client.get(self.url)
        self.assertEqual(response.context['espaco'], self.espaco)

    def test_contexto_tem_media_avaliacoes(self):
        """Contexto deve ter a média de avaliações"""
        response = self.client.get(self.url)
        self.assertIn('media_avaliacoes', response.context)

    def test_contexto_tem_avaliacoes_recentes(self):
        """Contexto deve ter avaliações recentes"""
        response = self.client.get(self.url)
        self.assertIn('avaliacoes_recentes', response.context)

    def test_contexto_tem_distribuicao_notas(self):
        """Contexto deve ter a distribuição de notas"""
        response = self.client.get(self.url)
        self.assertIn('distribuicao_notas', response.context)


# ===============================================================
# TESTES DO DASHBOARD DE ESPAÇO
# ===============================================================

class DashboardEspacoViewTest(EspacoViewsTestBase):
    """
    Testa a DashboardEspacoView: painel privado do gestor.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard')

    def test_redireciona_nao_autenticado(self):
        """Dashboard deve bloquear usuário não logado"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_redireciona_usuario_sem_espaco(self):
        """Usuário sem espaço deve ser redirecionado"""
        self._login_visitante()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_acessa_dashboard(self):
        """Gestor com espaço deve acessar o dashboard"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template do dashboard"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'espacos/dashboard/dashboard.html')

    def test_contexto_tem_espaco(self):
        """Contexto deve ter o espaço do gestor"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.context['espaco'], self.espaco)

    def test_contexto_tem_total_visualizacoes(self):
        """Contexto deve ter total de visualizações"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('total_visualizacoes', response.context)

    def test_contexto_tem_total_contatos(self):
        """Contexto deve ter total de contatos"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('total_contatos', response.context)


# ===============================================================
# TESTES DO DASHBOARD EDITAR ESPAÇO VIEW
# ===============================================================

class DashboardEditarEspacoViewTest(EspacoViewsTestBase):
    """
    Testa a DashboardEditarEspacoView: edição do espaço no dashboard.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_editar')

    def test_redireciona_nao_autenticado(self):
        """Deve bloquear acesso sem login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_acessa_editar(self):
        """Gestor deve acessar a edição do espaço"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de edição"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'espacos/dashboard/editar_espaco.html')

    def test_contexto_tem_form(self):
        """Contexto deve ter o formulário de edição"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('form', response.context)


# ===============================================================
# TESTES DO DASHBOARD ASSINATURA ESPAÇO VIEW
# ===============================================================

class DashboardAssinaturaEspacoViewTest(EspacoViewsTestBase):
    """
    Testa a DashboardAssinaturaEspacoView: plano do espaço.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_assinatura')

    def test_redireciona_nao_autenticado(self):
        """Deve bloquear acesso sem login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_acessa_assinatura(self):
        """Gestor deve acessar a página de assinatura"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# ===============================================================
# TESTES DA VIEW DE CONTATO COM ESPAÇO
# ===============================================================

class ContatoEspacoViewTest(EspacoViewsTestBase):
    """
    Testa a ContatoEspacoView: formulário de contato com espaço.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:contato', kwargs={'slug': self.espaco.slug})

    def test_get_exibe_formulario(self):
        """GET deve exibir o formulário de contato"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retorna_404_para_slug_inexistente(self):
        """Slug inválido deve retornar 404"""
        url = reverse('espacos:contato', kwargs={'slug': 'nao-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_retorna_404_para_espaco_inativo(self):
        """Espaço inativo deve retornar 404 no contato"""
        self.espaco.is_active = False
        self.espaco.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


# ===============================================================
# TESTES DAS APIS AJAX
# ===============================================================

class EspacoAjaxViewsTest(EspacoViewsTestBase):
    """
    Testa as APIs AJAX do app espacos.
    """

    def test_api_cidades_por_estado_retorna_json(self):
        """API de cidades por estado deve retornar JSON"""
        url = reverse('espacos:api_cidades', kwargs={'estado_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_comodidades_retorna_json(self):
        """API de comodidades deve retornar JSON"""
        url = reverse('espacos:api_comodidades')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_especialidades_retorna_json(self):
        """API de especialidades deve retornar JSON"""
        url = reverse('espacos:api_especialidades')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_busca_htmx_retorna_200(self):
        """API de busca HTMX deve retornar 200"""
        url = reverse('espacos:api_busca_htmx')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


# ===============================================================
# TESTES DO MIXIN DE ACESSO AO DASHBOARD
# ===============================================================

class EspacoRequiredMixinTest(EspacoViewsTestBase):
    """
    Testa que todas as URLs do dashboard de espaços
    bloqueiam acesso indevido.
    """

    def test_todas_urls_dashboard_bloqueiam_sem_login(self):
        """Todas as URLs do dashboard devem redirecionar sem login"""
        urls_protegidas = [
            reverse('espacos:dashboard'),
            reverse('espacos:dashboard_editar'),
            reverse('espacos:dashboard_assinatura'),
        ]
        for url in urls_protegidas:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 302,
                    f'URL {url} deveria bloquear sem login'
                )

    def test_todas_urls_dashboard_bloqueiam_visitante(self):
        """Usuário sem espaço deve ser redirecionado de todas as URLs do dashboard"""
        self._login_visitante()
        urls_protegidas = [
            reverse('espacos:dashboard'),
            reverse('espacos:dashboard_editar'),
            reverse('espacos:dashboard_assinatura'),
        ]
        for url in urls_protegidas:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 302,
                    f'URL {url} deveria redirecionar visitante sem espaço'
                )


# ===============================================================
# TESTES DE SANIDADE DAS URLs
# ===============================================================

class EspacoUrlsSanityTest(EspacoViewsTestBase):
    """
    Verifica que as principais URLs do app espacos existem e respondem.
    """

    def test_urls_publicas_existem(self):
        """URLs públicas devem existir e não retornar 404"""
        urls = [
            reverse('espacos:busca_avancada'),
            reverse('espacos:detalhe', kwargs={'slug': self.espaco.slug}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertNotEqual(
                    response.status_code, 404,
                    f'URL {url} não deveria retornar 404'
                )