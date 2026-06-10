# ===============================================================
# Título: Testes das Views do App Terapeutas
# Descrição: Testes unitários para TerapeutaListView, TerapeutaDetailView,
#             DashboardView, DashboardEditarPerfilView e contatar_terapeuta
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal

from terapeutas.models import Terapeuta
from core.models import Especialidade

User = get_user_model()


# ===============================================================
# HELPERS COMPARTILHADOS
# ===============================================================

class TerapeutaTestBase(TestCase):
    """
    Base compartilhada entre todos os testes do app terapeutas.
    Cria usuário, terapeuta e client configurados.
    """

    def setUp(self):
        """Cria usuário e terapeuta antes de cada teste"""
        self.client = Client()

        # Usuário sem perfil de terapeuta (visitante)
        self.visitante = User.objects.create_user(
            username='visitante',
            email='visitante@teste.com',
            password='senha123',
        )

        # Usuário com perfil de terapeuta
        self.user_terapeuta = User.objects.create_user(
            username='terapeuta_teste',
            email='terapeuta@teste.com',
            password='senha123',
            first_name='Ana',
        )

        # Criar especialidade para uso nos testes
        self.especialidade, _ = Especialidade.objects.get_or_create(
            nome='Reiki',
            defaults={
                'descricao_curta': 'Terapia energética',
                'is_active': True,
            }
        )

        # Criar terapeuta ativo
        self.terapeuta = Terapeuta.objects.create(
            user=self.user_terapeuta,
            nome_completo='Ana Silva Terapeuta',
            nome_exibicao='Ana Silva',
            slug='ana-silva-terapeuta',
            email_profissional='ana@teste.com',
            bio_curta='Terapeuta holística com 5 anos de experiência.',
            bio_completa='<p>Descrição completa da Ana.</p>',
            formacao='Curso de Reiki',
            experiencia_anos=5,
            is_active=True,
        )

    def _login_terapeuta(self):
        """Utilitário: faz login com o usuário terapeuta"""
        self.client.login(username='terapeuta_teste', password='senha123')

    def _login_visitante(self):
        """Utilitário: faz login com usuário sem perfil de terapeuta"""
        self.client.login(username='visitante', password='senha123')


# ===============================================================
# TESTES DA TERAPEUTA LIST VIEW (busca/listagem)
# ===============================================================

class TerapeutaListViewTest(TerapeutaTestBase):
    """
    Testa a TerapeutaListView: listagem pública de terapeutas com filtros.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:listagem_resultados')

    # --- Acesso básico ---

    def test_listagem_acessivel_sem_login(self):
        """Página de listagem deve ser pública"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de listagem"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'terapeutas/listagem_resultados.html')

    def test_exibe_terapeutas_ativos(self):
        """Apenas terapeutas com is_active=True devem aparecer"""
        response = self.client.get(self.url)
        terapeutas = list(response.context['terapeutas'])
        for t in terapeutas:
            self.assertTrue(t.is_active)

    def test_nao_exibe_terapeutas_inativos(self):
        """Terapeuta inativo não deve aparecer na listagem"""
        # Criar terapeuta inativo
        user_inativo = User.objects.create_user(
            username='inativo', password='senha123'
        )
        Terapeuta.objects.create(
            user=user_inativo,
            nome_completo='Inativo Teste',
            nome_exibicao='Inativo',
            slug='inativo-teste',
            bio_curta='Bio.',
            bio_completa='<p>Bio.</p>',
            formacao='Formação',
            is_active=False,
        )
        response = self.client.get(self.url)
        slugs_exibidos = [t.slug for t in response.context['terapeutas']]
        self.assertNotIn('inativo-teste', slugs_exibidos)

    # --- Filtros ---

    def test_filtro_por_estado_invalido_nao_quebra(self):
        """Filtro com estado inválido não deve causar erro 500"""
        response = self.client.get(self.url, {'estado': 'abc'})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_cidade_invalida_nao_quebra(self):
        """Filtro com cidade inválida não deve causar erro 500"""
        response = self.client.get(self.url, {'cidade': 'xyz'})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_pais_invalido_nao_quebra(self):
        """Filtro com pais não inteiro não deve causar erro 500"""
        response = self.client.get(self.url, {'pais': 'nao-inteiro'})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_especialidade_invalida_nao_quebra(self):
        """Filtro com especialidade inválida não deve causar erro 500"""
        response = self.client.get(self.url, {'especialidades': ['abc', '999']})
        self.assertEqual(response.status_code, 200)

    def test_filtro_por_especialidade_valida(self):
        """Filtro por especialidade válida deve funcionar sem erro"""
        self.terapeuta.especialidades.add(self.especialidade)
        response = self.client.get(self.url, {'especialidades': [self.especialidade.id]})
        self.assertEqual(response.status_code, 200)

    def test_filtro_tipo_sessao(self):
        """Filtro por tipo de sessão deve funcionar"""
        response = self.client.get(self.url, {'tipos_sessao': ['presencial']})
        self.assertEqual(response.status_code, 200)

    def test_contexto_tem_filtros_atuais(self):
        """Contexto deve ter os filtros atuais para manter selecionado"""
        response = self.client.get(self.url, {'q': 'reiki'})
        self.assertIn('filtros_atuais', response.context)

    def test_busca_por_texto(self):
        """Parâmetro 'q' deve funcionar sem erro"""
        response = self.client.get(self.url, {'q': 'Ana'})
        self.assertEqual(response.status_code, 200)

    def test_paginacao_funciona(self):
        """Segunda página deve retornar 200 ou redirecionar"""
        response = self.client.get(self.url, {'page': 2})
        self.assertIn(response.status_code, [200, 404])

    def test_ordenacao_por_relevancia(self):
        """Parâmetro de ordenação deve ser aceito"""
        response = self.client.get(self.url, {'ordenacao': 'relevancia'})
        self.assertEqual(response.status_code, 200)


# ===============================================================
# TESTES DA TERAPEUTA DETAIL VIEW (perfil público)
# ===============================================================

class TerapeutaDetailViewTest(TerapeutaTestBase):
    """
    Testa a TerapeutaDetailView: página pública do perfil do terapeuta.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:perfil', kwargs={'slug': self.terapeuta.slug})

    # --- Acesso básico ---

    def test_perfil_acessivel_sem_login(self):
        """Perfil público deve ser acessível sem login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de perfil"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'terapeutas/perfil.html')

    def test_retorna_404_para_terapeuta_inativo(self):
        """Terapeuta inativo deve retornar 404"""
        self.terapeuta.is_active = False
        self.terapeuta.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_retorna_404_para_slug_inexistente(self):
        """Slug que não existe deve retornar 404"""
        url = reverse('terapeutas:perfil', kwargs={'slug': 'nao-existe-nunca'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # --- Contexto ---

    def test_contexto_tem_terapeuta(self):
        """Contexto deve ter o objeto terapeuta"""
        response = self.client.get(self.url)
        self.assertEqual(response.context['terapeuta'], self.terapeuta)

    def test_contexto_tem_stats(self):
        """Contexto deve ter as estatísticas do terapeuta"""
        response = self.client.get(self.url)
        self.assertIn('stats', response.context)

    def test_contexto_tem_avaliacoes_recentes(self):
        """Contexto deve ter a lista de avaliações recentes"""
        response = self.client.get(self.url)
        self.assertIn('avaliacoes_recentes', response.context)

    def test_contexto_tem_especialidades_detalhadas(self):
        """Contexto deve ter especialidades detalhadas"""
        response = self.client.get(self.url)
        self.assertIn('especialidades_detalhadas', response.context)

    def test_visualizacoes_incrementadas(self):
        """Cada acesso ao perfil deve incrementar o contador de visualizações"""
        visualizacoes_antes = self.terapeuta.visualizacoes
        self.client.get(self.url)
        self.terapeuta.refresh_from_db()
        self.assertEqual(self.terapeuta.visualizacoes, visualizacoes_antes + 1)


# ===============================================================
# TESTES DO DASHBOARD VIEW (área privada do terapeuta)
# ===============================================================

class DashboardViewTest(TerapeutaTestBase):
    """
    Testa a DashboardView: painel privado do terapeuta.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:dashboard')

    # --- Controle de acesso ---

    def test_redireciona_usuario_nao_autenticado(self):
        """Dashboard deve bloquear usuário não logado"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_redireciona_usuario_sem_perfil_terapeuta(self):
        """Usuário logado sem perfil de terapeuta deve ser redirecionado"""
        self._login_visitante()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_dashboard(self):
        """Terapeuta autenticado deve acessar o dashboard"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Dashboard deve usar o template correto"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'terapeutas/dashboard/dashboard.html')

    # --- Contexto do dashboard ---

    def test_contexto_tem_terapeuta(self):
        """Contexto deve ter o objeto terapeuta"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.context['terapeuta'], self.terapeuta)

    def test_contexto_tem_completude_perfil(self):
        """Contexto deve ter o percentual de completude do perfil"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('completude_perfil', response.context)

    def test_contexto_tem_total_visualizacoes(self):
        """Contexto deve ter o contador de visualizações"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('total_visualizacoes', response.context)

    def test_contexto_tem_ultimas_avaliacoes(self):
        """Contexto deve ter as últimas avaliações"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('ultimas_avaliacoes', response.context)

    def test_contexto_tem_avaliacoes_mes(self):
        """Contexto deve ter contagem de avaliações do mês"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('avaliacoes_mes', response.context)

    def test_completude_perfil_e_numero(self):
        """Completude do perfil deve ser um número inteiro entre 0 e 100"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        completude = response.context['completude_perfil']
        self.assertIsInstance(completude, int)
        self.assertGreaterEqual(completude, 0)
        self.assertLessEqual(completude, 100)


# ===============================================================
# TESTES DO DASHBOARD EDITAR PERFIL VIEW
# ===============================================================

class DashboardEditarPerfilViewTest(TerapeutaTestBase):
    """
    Testa a DashboardEditarPerfilView: edição do perfil no dashboard.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:dashboard_editar_perfil')

    # --- Controle de acesso ---

    def test_redireciona_nao_autenticado(self):
        """Editar perfil deve bloquear usuário não logado"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_redireciona_sem_perfil_terapeuta(self):
        """Usuário sem perfil de terapeuta deve ser redirecionado"""
        self._login_visitante()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_editar_perfil(self):
        """Terapeuta deve acessar a página de edição"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar template de edição de perfil"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'terapeutas/dashboard/editar_perfil.html')

    def test_contexto_tem_form(self):
        """Contexto deve ter o formulário de edição"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('form', response.context)

    def test_contexto_tem_terapeuta(self):
        """Contexto deve ter o objeto terapeuta"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('terapeuta', response.context)


# ===============================================================
# TESTES DO DASHBOARD ASSINATURA VIEW
# ===============================================================

class DashboardAssinaturaViewTest(TerapeutaTestBase):
    """
    Testa a DashboardAssinaturaView: página de planos do terapeuta.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:dashboard_assinatura')

    def test_redireciona_nao_autenticado(self):
        """Deve bloquear acesso sem login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_assinatura(self):
        """Terapeuta deve acessar a página de assinatura"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# ===============================================================
# TESTES DO DASHBOARD ESTATÍSTICAS VIEW
# ===============================================================

class DashboardEstatisticasViewTest(TerapeutaTestBase):
    """
    Testa a DashboardEstatisticasView: métricas detalhadas.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:dashboard_estatisticas')

    def test_redireciona_nao_autenticado(self):
        """Deve bloquear acesso sem login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_estatisticas(self):
        """Terapeuta deve acessar a página de estatísticas"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_tem_total_visualizacoes(self):
        """Estatísticas deve ter total de visualizações"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('total_visualizacoes', response.context)

    def test_contexto_tem_avaliacoes_mes(self):
        """Estatísticas deve ter avaliações do mês"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('avaliacoes_mes', response.context)


# ===============================================================
# TESTES DA VIEW DE CONTATO COM TERAPEUTA
# ===============================================================

class ContatarTerapeutaViewTest(TerapeutaTestBase):
    """
    Testa a view de contato: envio de mensagem para terapeuta.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'terapeutas:contatar',
            kwargs={'terapeuta_slug': self.terapeuta.slug}
        )

    # --- GET ---

    def test_get_exibe_formulario(self):
        """GET deve exibir o formulário de contato"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_retorna_404_para_slug_inexistente(self):
        """GET com slug inválido deve retornar 404"""
        url = reverse('terapeutas:contatar', kwargs={'terapeuta_slug': 'nao-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_retorna_404_para_terapeuta_inativo(self):
        """GET com terapeuta inativo deve retornar 404"""
        self.terapeuta.is_active = False
        self.terapeuta.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    # --- POST válido ---

    def test_post_campos_completos_sucesso(self):
        """POST com todos os campos obrigatórios deve funcionar"""
        dados = {
            'nome': 'João Cliente',
            'email': 'joao@teste.com',
            'assunto': 'Quero agendar uma sessão',
            'mensagem': 'Tenho interesse em Reiki. Como funciona?',
            'telefone': '21998765432',
        }
        response = self.client.post(self.url, dados)
        # Deve redirecionar ou exibir confirmação (200 ou 302)
        self.assertIn(response.status_code, [200, 302])

    # --- POST inválido ---

    def test_post_sem_nome_exibe_erro(self):
        """POST sem nome deve exibir mensagem de erro"""
        dados = {
            'nome': '',
            'email': 'joao@teste.com',
            'assunto': 'Teste',
            'mensagem': 'Mensagem de teste',
        }
        response = self.client.post(self.url, dados, follow=True)
        mensagens = [str(m) for m in response.context['messages']]
        self.assertTrue(
            any('obrigatório' in m.lower() or 'preencha' in m.lower() for m in mensagens)
        )

    def test_post_sem_email_exibe_erro(self):
        """POST sem email deve exibir mensagem de erro"""
        dados = {
            'nome': 'João',
            'email': '',
            'assunto': 'Teste',
            'mensagem': 'Mensagem',
        }
        response = self.client.post(self.url, dados, follow=True)
        mensagens = [str(m) for m in response.context['messages']]
        self.assertTrue(
            any('obrigatório' in m.lower() or 'preencha' in m.lower() for m in mensagens)
        )

    def test_post_sem_mensagem_exibe_erro(self):
        """POST sem mensagem deve exibir mensagem de erro"""
        dados = {
            'nome': 'João',
            'email': 'joao@teste.com',
            'assunto': 'Teste',
            'mensagem': '',
        }
        response = self.client.post(self.url, dados, follow=True)
        mensagens = [str(m) for m in response.context['messages']]
        self.assertTrue(
            any('obrigatório' in m.lower() or 'preencha' in m.lower() for m in mensagens)
        )


# ===============================================================
# TESTES DA API AJAX (cidades por estado e busca)
# ===============================================================

class TerapeutaAjaxViewsTest(TerapeutaTestBase):
    """
    Testa as views AJAX: cidades por estado e busca de terapeutas.
    """

    def test_api_cidades_por_estado_retorna_json(self):
        """API de cidades por estado deve retornar JSON"""
        url = reverse('terapeutas:cidades_por_estado_ajax')
        response = self.client.get(url, {'estado_id': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_cidades_sem_estado_retorna_json(self):
        """API de cidades sem parâmetro deve retornar JSON sem erro"""
        url = reverse('terapeutas:cidades_por_estado_ajax')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_busca_ajax_retorna_json(self):
        """API de busca AJAX deve retornar JSON"""
        url = reverse('terapeutas:busca_ajax')
        response = self.client.get(url, {'q': 'Ana'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_busca_ajax_sem_parametro(self):
        """Busca AJAX sem parâmetro deve retornar JSON sem erro"""
        url = reverse('terapeutas:busca_ajax')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


# ===============================================================
# TESTES DA VIEW POR ESPECIALIDADE
# ===============================================================

class TerapeutasPorEspecialidadeTest(TerapeutaTestBase):
    """
    Testa a view de terapeutas por especialidade (URL com slug).
    """

    def setUp(self):
        super().setUp()
        # Garantir que especialidade tem slug
        self.especialidade.slug = 'reiki'
        self.especialidade.save()

    def test_listagem_por_especialidade_valida(self):
        """Listagem por especialidade existente deve retornar 200"""
        url = reverse(
            'terapeutas:por_especialidade',
            kwargs={'especialidade_slug': 'reiki'}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_listagem_por_especialidade_invalida_retorna_404(self):
        """Especialidade inexistente deve retornar 404"""
        url = reverse(
            'terapeutas:por_especialidade',
            kwargs={'especialidade_slug': 'especialidade-que-nao-existe'}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ===============================================================
# TESTES DO MIXIN DE ACESSO AO DASHBOARD
# ===============================================================

class TerapeutaRequiredMixinTest(TerapeutaTestBase):
    """
    Testa o TerapeutaRequiredMixin aplicado nas views do dashboard.
    Verifica que todas as URLs protegidas rejeitam acesso indevido.
    """

    def test_todas_urls_dashboard_bloqueiam_sem_login(self):
        """Todas as URLs do dashboard devem redirecionar sem login"""
        urls_protegidas = [
            reverse('terapeutas:dashboard'),
            reverse('terapeutas:dashboard_editar_perfil'),
            reverse('terapeutas:dashboard_estatisticas'),
            reverse('terapeutas:dashboard_assinatura'),
            reverse('terapeutas:dashboard_espacos'),
        ]
        for url in urls_protegidas:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 302,
                    f'URL {url} deveria bloquear usuário não autenticado'
                )

    def test_todas_urls_dashboard_bloqueiam_visitante(self):
        """Usuário logado sem perfil de terapeuta deve ser redirecionado"""
        self._login_visitante()
        urls_protegidas = [
            reverse('terapeutas:dashboard'),
            reverse('terapeutas:dashboard_editar_perfil'),
            reverse('terapeutas:dashboard_estatisticas'),
            reverse('terapeutas:dashboard_assinatura'),
        ]
        for url in urls_protegidas:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 302,
                    f'URL {url} deveria redirecionar usuário sem perfil de terapeuta'
                )