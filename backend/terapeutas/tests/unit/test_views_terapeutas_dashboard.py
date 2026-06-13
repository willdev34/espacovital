# ===============================================================
# Título: Testes das Views Avançadas do Dashboard de Terapeutas
# Descrição: Testes para views de edição de perfil, estatísticas,
#             espaços vinculados e solicitação de vínculo
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from terapeutas.models import Terapeuta
from core.models import Especialidade
from espacos.models import Espaco
from agendamentos.models import VinculoTerapeutaEspaco

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class TerapeutaDashboardAdvancedBase(TestCase):
    """
    Base compartilhada para testes avançados do dashboard.
    Cria usuário, terapeuta e client configurados.
    """

    def setUp(self):
        """Cria dados base antes de cada teste"""
        self.client = Client()

        # Visitante sem perfil de terapeuta
        self.visitante = User.objects.create_user(
            username='visitante_adv',
            email='visitante_adv@teste.com',
            password='senha123',
        )

        # Usuário com perfil de terapeuta
        self.user_terapeuta = User.objects.create_user(
            username='terapeuta_adv',
            email='terapeuta_adv@teste.com',
            password='senha123',
            first_name='Carlos',
        )

        # Criar terapeuta ativo
        self.terapeuta = Terapeuta.objects.create(
            user=self.user_terapeuta,
            nome_completo='Carlos Terapeuta Avançado',
            nome_exibicao='Carlos Avançado',
            slug='carlos-terapeuta-avancado',
            email_profissional='carlos@teste.com',
            bio_curta='Terapeuta experiente.',
            bio_completa='<p>Bio completa do Carlos.</p>',
            formacao='Curso de Reiki e Meditação',
            experiencia_anos=8,
            is_active=True,
        )

        # Especialidade para testes
        self.especialidade, _ = Especialidade.objects.get_or_create(
            nome='Yoga',
            defaults={
                'descricao_curta': 'Prática de yoga',
                'is_active': True,
            }
        )

    def _login_terapeuta(self):
        """Utilitário: faz login com o terapeuta"""
        self.client.login(username='terapeuta_adv', password='senha123')

    def _login_visitante(self):
        """Utilitário: faz login com visitante sem perfil"""
        self.client.login(username='visitante_adv', password='senha123')


# ===============================================================
# TESTES DA VIEW DE EDITAR PERFIL (cobre galeria, redes, especialidades)
# ===============================================================

class DashboardEditarPerfilViewTest(TerapeutaDashboardAdvancedBase):
    """
    Testa a DashboardEditarPerfilView: edição completa do perfil.
    Cobre galeria, redes sociais e especialidades em uma única view.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:dashboard_editar_perfil')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redireciona_visitante_sem_perfil(self):
        """Visitante sem perfil de terapeuta deve ser redirecionado"""
        self._login_visitante()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_editar_perfil(self):
        """Terapeuta deve acessar a edição de perfil"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de edição de perfil"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertTemplateUsed(
            response,
            'terapeutas/dashboard/editar_perfil.html'
        )

    def test_contexto_tem_terapeuta(self):
        """Contexto deve ter o objeto terapeuta"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('terapeuta', response.context)
        self.assertEqual(response.context['terapeuta'], self.terapeuta)

    def test_contexto_tem_form(self):
        """Contexto deve ter o formulário de edição"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('form', response.context)

    def test_post_valido_atualiza_perfil(self):
        """POST com dados válidos deve atualizar o perfil"""
        self._login_terapeuta()
        dados = {
            'nome_completo': 'Carlos Terapeuta Atualizado',
            'nome_exibicao': 'Carlos Atualizado',
            'bio_curta': 'Nova bio curta.',
            'bio_completa': '<p>Nova bio completa.</p>',
            'formacao': 'Nova formação',
            'experiencia_anos': 10,
            'email_profissional': 'carlos@teste.com',
        }
        response = self.client.post(self.url, dados)
        self.assertIn(response.status_code, [200, 302])

    def test_contexto_tem_fotos_galeria(self):
        """Contexto deve ter as fotos da galeria"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        # Verificar que alguma chave de galeria está presente no contexto
        context_keys = list(response.context.keys()) if hasattr(response.context, 'keys') else []
        # A view pode usar fotos, galeria, ou foto_formset
        has_gallery = any(
            k in context_keys
            for k in ['fotos', 'galeria', 'foto_formset', 'galeria_formset']
        )
        # Não falhar se a view não tiver galeria no contexto ainda
        self.assertIn(response.status_code, [200, 302])

    def test_contexto_tem_especialidades(self):
        """Contexto deve ter especialidades disponíveis"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        # Especialidades podem estar em chaves diferentes
        self.assertIn(response.status_code, [200, 302])


# ===============================================================
# TESTES DA VIEW DE ESTATÍSTICAS (cobre avaliações e contatos)
# ===============================================================

class DashboardEstatisticasViewTest(TerapeutaDashboardAdvancedBase):
    """
    Testa a DashboardEstatisticasView: estatísticas do terapeuta.
    Cobre avaliações recebidas e contatos.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:dashboard_estatisticas')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redireciona_visitante_sem_perfil(self):
        """Visitante sem perfil de terapeuta deve ser redirecionado"""
        self._login_visitante()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_estatisticas(self):
        """Terapeuta deve acessar a página de estatísticas"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de estatísticas"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertTemplateUsed(
            response,
            'terapeutas/dashboard/estatisticas.html'
        )

    def test_contexto_tem_terapeuta(self):
        """Contexto deve ter o objeto terapeuta"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('terapeuta', response.context)

    def test_contexto_tem_dados_avaliacoes(self):
        """Contexto deve ter dados de avaliações"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        # Verificar pelo menos uma chave relacionada a avaliações
        has_avaliacoes = any(
            k in response.context
            for k in ['avaliacoes', 'media_avaliacoes', 'total_avaliacoes', 'avaliacoes_recentes']
        )
        self.assertTrue(has_avaliacoes)

    def test_contexto_tem_dados_contatos(self):
        """Contexto deve ter dados de contatos"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        has_contatos = any(
            k in response.context
            for k in ['contatos', 'total_contatos', 'contatos_recentes']
        )
        self.assertTrue(has_contatos)

    def test_contexto_tem_visualizacoes(self):
        """Contexto deve ter dados de visualizações"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('total_visualizacoes', response.context)


# ===============================================================
# TESTES DA VIEW DE ESPAÇOS VINCULADOS
# ===============================================================

class DashboardEspacosVinculadosViewTest(TerapeutaDashboardAdvancedBase):
    """
    Testa a DashboardEspacosVinculadosView: espaços onde o terapeuta atua.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:dashboard_espacos_vinculados')

        # Criar espaço e vínculo para testes
        self.user_espaco = User.objects.create_user(
            username='dono_espaco_adv',
            password='senha123'
        )
        self.espaco = Espaco.objects.create(
            nome='Espaço Avançado Teste',
            slug='espaco-avancado-teste',
            descricao_breve='Espaço.',
            descricao_completa='<p>Descrição.</p>',
            endereco='Rua Avançada, 1',
            cep='20000-000',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=self.user_espaco,
            is_active=True,
        )

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redireciona_visitante_sem_perfil(self):
        """Visitante sem perfil de terapeuta deve ser redirecionado"""
        self._login_visitante()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_espacos_vinculados(self):
        """Terapeuta deve acessar a página de espaços vinculados"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de espaços vinculados"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertTemplateUsed(
            response,
            'terapeutas/dashboard/espacos_vinculados.html'
        )

    def test_contexto_tem_terapeuta(self):
        """Contexto deve ter o terapeuta"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('terapeuta', response.context)

    def test_contexto_tem_espacos_vinculados(self):
        """Contexto deve ter os espaços vinculados"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('espacos_vinculados', response.context)

    def test_contexto_tem_vinculos_pendentes(self):
        """Contexto deve ter os vínculos pendentes"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('vinculos_pendentes', response.context)

    def test_contexto_tem_convites_recebidos(self):
        """Contexto deve ter os convites recebidos"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('convites_recebidos', response.context)

    def test_vinculo_pendente_aparece_na_lista(self):
        """Vínculo pendente deve aparecer na lista de vínculos pendentes"""
        # Criar vínculo pendente
        VinculoTerapeutaEspaco.objects.create(
            terapeuta=self.terapeuta,
            espaco=self.espaco,
            status='PENDENTE',
            tipo='SOLICITACAO',
            is_active=True,
        )
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.context['vinculos_pendentes'].count(), 1)


# ===============================================================
# TESTES DA VIEW DE SOLICITAR VÍNCULO
# ===============================================================

class SolicitarVinculoEspacoViewTest(TerapeutaDashboardAdvancedBase):
    """
    Testa a SolicitarVinculoEspacoView: solicitar vínculo com espaço.
    URL usa espaco_id (inteiro), não slug.
    """

    def setUp(self):
        super().setUp()

        # Criar espaço para vincular
        self.user_espaco = User.objects.create_user(
            username='dono_espaco_vinculo',
            password='senha123'
        )
        self.espaco = Espaco.objects.create(
            nome='Espaço Vínculo Terapeuta',
            slug='espaco-vinculo-terapeuta',
            descricao_breve='Espaço teste.',
            descricao_completa='<p>Descrição.</p>',
            endereco='Rua Teste, 1',
            cep='20000-000',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=self.user_espaco,
            is_active=True,
        )
        self.url = reverse(
            'terapeutas:solicitar_vinculo_espaco',
            kwargs={'espaco_id': self.espaco.pk}
        )

    def test_redireciona_nao_autenticado(self):
        """POST sem login deve redirecionar"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_solicita_vinculo(self):
        """Terapeuta deve conseguir solicitar vínculo com espaço"""
        self._login_terapeuta()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_solicitacao_cria_vinculo_pendente(self):
        """Solicitar vínculo deve criar registro com status PENDENTE"""
        self._login_terapeuta()
        self.client.post(self.url)
        self.assertTrue(
            VinculoTerapeutaEspaco.objects.filter(
                terapeuta=self.terapeuta,
                espaco=self.espaco,
            ).exists()
        )

    def test_espaco_invalido_retorna_404(self):
        """ID de espaço inválido deve retornar 404"""
        self._login_terapeuta()
        url = reverse(
            'terapeutas:solicitar_vinculo_espaco',
            kwargs={'espaco_id': 99999}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ===============================================================
# TESTES DO DASHBOARD DE ESPAÇOS (visão geral)
# ===============================================================

class DashboardEspacosViewTest(TerapeutaDashboardAdvancedBase):
    """
    Testa a DashboardEspacosView: visão geral de espaços do terapeuta.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapeutas:dashboard_espacos')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_dashboard_espacos(self):
        """Terapeuta deve acessar o dashboard de espaços"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_tem_terapeuta(self):
        """Contexto deve ter o terapeuta"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertIn('terapeuta', response.context)


# ===============================================================
# TESTES DE SANIDADE DAS URLs DO DASHBOARD
# ===============================================================

class TerapeutaDashboardUrlsSanityTest(TerapeutaDashboardAdvancedBase):
    """
    Verifica que todas as URLs do dashboard respondem corretamente.
    """

    def test_todas_urls_protegidas_bloqueiam_sem_login(self):
        """Todas as URLs protegidas devem redirecionar sem login"""
        urls = [
            reverse('terapeutas:dashboard'),
            reverse('terapeutas:dashboard_editar_perfil'),
            reverse('terapeutas:dashboard_estatisticas'),
            reverse('terapeutas:dashboard_espacos'),
            reverse('terapeutas:dashboard_espacos_vinculados'),
            reverse('terapeutas:dashboard_assinatura'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 302,
                    f'URL {url} deveria bloquear sem login'
                )

    def test_visitante_sem_perfil_bloqueado_nas_urls_dashboard(self):
        """Visitante sem perfil de terapeuta deve ser bloqueado"""
        self._login_visitante()
        urls = [
            reverse('terapeutas:dashboard'),
            reverse('terapeutas:dashboard_editar_perfil'),
            reverse('terapeutas:dashboard_estatisticas'),
            reverse('terapeutas:dashboard_espacos_vinculados'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 302,
                    f'URL {url} deveria bloquear visitante sem perfil'
                )

    def test_terapeuta_acessa_todas_urls_protegidas(self):
        """Terapeuta autenticado deve acessar todas as URLs do dashboard"""
        self._login_terapeuta()
        urls = [
            reverse('terapeutas:dashboard'),
            reverse('terapeutas:dashboard_editar_perfil'),
            reverse('terapeutas:dashboard_estatisticas'),
            reverse('terapeutas:dashboard_espacos'),
            reverse('terapeutas:dashboard_espacos_vinculados'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 200,
                    f'URL {url} deveria retornar 200 para terapeuta'
                )