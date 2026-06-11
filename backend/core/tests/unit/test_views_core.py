# ===============================================================
# Título: Testes das Views do App Core
# Descrição: Testes unitários para HomeView, views institucionais,
#             ContatoView, IndiqueTerapiaView e SelecionarPerfilView
# Autor: Will
# Data: 09/06/2026
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Contact, SugestaoTerapia

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class CoreViewsTestBase(TestCase):
    """
    Base compartilhada entre todos os testes do app core.
    """

    def setUp(self):
        """Cria usuário e client antes de cada teste"""
        self.client = Client()

        # Usuário simples sem perfil
        self.user = User.objects.create_user(
            username='usuario_core',
            email='core@teste.com',
            password='senha123',
            first_name='João',
        )


# ===============================================================
# TESTES DA HOME VIEW
# ===============================================================

class HomeViewTest(CoreViewsTestBase):
    """
    Testa a HomeView: página inicial pública do Espaço Vital.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('core:home')

    def test_home_acessivel_sem_login(self):
        """Página inicial deve ser pública"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_usa_template_correto(self):
        """Deve usar o template da home"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_home_acessivel_com_login(self):
        """Página inicial deve funcionar com usuário logado"""
        self.client.login(username='usuario_core', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# ===============================================================
# TESTES DAS PÁGINAS INSTITUCIONAIS
# ===============================================================

class PaginasInstitucionaisTest(CoreViewsTestBase):
    """
    Testa as views de páginas institucionais: todas devem ser
    públicas, retornar 200 e usar o template correto.
    """

    def test_todas_paginas_institucionais_retornam_200(self):
        """Todas as páginas institucionais devem ser acessíveis"""
        urls_e_templates = [
            ('core:sobre',        'core/sobre.html'),
            ('core:termos',       'core/termos.html'),
            ('core:privacidade',  'core/privacidade.html'),
            ('core:cookies',      'core/cookies.html'),
            ('core:parceiro',     'core/parceiro.html'),
            ('core:faq',          'core/faq.html'),
        ]
        for nome_url, template in urls_e_templates:
            with self.subTest(url=nome_url):
                url = reverse(nome_url)
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 200,
                    f'{nome_url} deve retornar 200'
                )
                self.assertTemplateUsed(
                    response, template,
                    f'{nome_url} deve usar {template}'
                )

    def test_todas_paginas_tem_page_title_no_contexto(self):
        """Cada página institucional deve ter page_title no contexto"""
        urls = [
            'core:sobre',
            'core:termos',
            'core:privacidade',
            'core:cookies',
            'core:parceiro',
            'core:faq',
        ]
        for nome_url in urls:
            with self.subTest(url=nome_url):
                url = reverse(nome_url)
                response = self.client.get(url)
                self.assertIn(
                    'page_title', response.context,
                    f'{nome_url} deve ter page_title no contexto'
                )

    def test_paginas_acessiveis_sem_login(self):
        """Todas as páginas institucionais devem funcionar sem login"""
        urls = [
            'core:sobre', 'core:termos', 'core:privacidade',
            'core:cookies', 'core:parceiro', 'core:faq',
        ]
        for nome_url in urls:
            with self.subTest(url=nome_url):
                response = self.client.get(reverse(nome_url))
                self.assertNotEqual(response.status_code, 302)


# ===============================================================
# TESTES DA CONTATO VIEW
# ===============================================================

class ContatoViewTest(CoreViewsTestBase):
    """
    Testa a ContatoView: formulário de contato do site.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('core:contato')

    def test_get_exibe_formulario(self):
        """GET deve exibir o formulário de contato"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contato.html')

    def test_get_tem_page_title(self):
        """Contexto deve ter page_title"""
        response = self.client.get(self.url)
        self.assertIn('page_title', response.context)

    def test_post_valido_cria_contato(self):
        """POST com dados válidos deve criar registro de contato"""
        contatos_antes = Contact.objects.count()
        dados = {
            'name': 'Maria Teste',
            'email': 'maria@teste.com',
            'phone': '21987654321',
            'subject': 'general',  # choice válido
            'message': 'Gostaria de saber mais sobre como funciona o cadastro.',
        }
        response = self.client.post(self.url, dados)
        # Deve redirecionar após sucesso (success_url aponta para a mesma página)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Contact.objects.count(), contatos_antes + 1)

    def test_post_valido_exibe_mensagem_sucesso(self):
        """POST válido deve exibir mensagem de sucesso"""
        dados = {
            'name': 'Maria Teste',
            'email': 'maria@teste.com',
            'phone': '21987654321',
            'subject': 'support',  # choice válido
            'message': 'Mensagem de teste.',
        }
        response = self.client.post(self.url, dados, follow=True)
        mensagens = [str(m) for m in response.context['messages']]
        self.assertTrue(
            any('sucesso' in m.lower() or 'enviada' in m.lower() for m in mensagens)
        )

    def test_post_invalido_sem_email_nao_salva(self):
        """POST sem email não deve criar registro"""
        contatos_antes = Contact.objects.count()
        dados = {
            'name': 'Maria Teste',
            'email': '',  # campo obrigatório vazio
            'subject': 'Dúvida',
            'message': 'Mensagem.',
        }
        self.client.post(self.url, dados)
        self.assertEqual(Contact.objects.count(), contatos_antes)

    def test_post_invalido_rerenderiza_formulario(self):
        """POST inválido deve reexibir o formulário (200, não 302)"""
        dados = {
            'name': '',
            'email': '',
            'subject': '',
            'message': '',
        }
        response = self.client.post(self.url, dados)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contato.html')


# ===============================================================
# TESTES DA INDIQUE TERAPIA VIEW
# ===============================================================

class IndiqueTerapiaViewTest(CoreViewsTestBase):
    """
    Testa a IndiqueTerapiaView: formulário de sugestão de terapias.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('core:indique_terapia')

    def test_get_exibe_formulario(self):
        """GET deve exibir o formulário"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/indique_terapia.html')

    def test_get_tem_page_title(self):
        """Contexto deve ter page_title"""
        response = self.client.get(self.url)
        self.assertIn('page_title', response.context)

    def test_post_valido_cria_sugestao(self):
        """POST com dados válidos deve criar sugestão"""
        sugestoes_antes = SugestaoTerapia.objects.count()
        dados = {
            'nome': 'Carlos Sugestor',
            'email': 'carlos@teste.com',
            'nome_terapia': 'Aromaterapia Quântica',
            'descricao': 'Terapia que combina aromas com princípios quânticos.',
        }
        response = self.client.post(self.url, dados)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SugestaoTerapia.objects.count(), sugestoes_antes + 1)

    def test_post_valido_exibe_mensagem_sucesso(self):
        """POST válido deve exibir mensagem de agradecimento"""
        dados = {
            'nome': 'Carlos Sugestor',
            'email': 'carlos@teste.com',
            'nome_terapia': 'Aromaterapia',
            'descricao': 'Descrição da terapia.',
        }
        response = self.client.post(self.url, dados, follow=True)
        mensagens = [str(m) for m in response.context['messages']]
        self.assertTrue(
            any('sugestão' in m.lower() or 'obrigado' in m.lower() for m in mensagens)
        )

    def test_post_invalido_sem_nome_terapia_nao_salva(self):
        """POST sem nome da terapia não deve criar sugestão"""
        sugestoes_antes = SugestaoTerapia.objects.count()
        dados = {
            'nome': 'Carlos',
            'email': 'carlos@teste.com',
            'nome_terapia': '',  # obrigatório vazio
            'descricao': 'Descrição.',
        }
        self.client.post(self.url, dados)
        self.assertEqual(SugestaoTerapia.objects.count(), sugestoes_antes)

    def test_acessivel_sem_login(self):
        """Formulário deve ser público"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# ===============================================================
# TESTES DA SELECIONAR PERFIL VIEW
# ===============================================================

class SelecionarPerfilViewTest(CoreViewsTestBase):
    """
    Testa a SelecionarPerfilView: seleção de dashboard quando
    o usuário tem perfil de terapeuta E de espaço.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('core:selecionar_perfil')

    def test_redireciona_usuario_nao_autenticado(self):
        """Usuário não logado deve ser redirecionado para login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redireciona_usuario_sem_perfil_para_home(self):
        """Usuário sem perfil de terapeuta nem espaço vai para home"""
        self.client.login(username='usuario_core', password='senha123')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('core:home'))

    def test_redireciona_apenas_terapeuta_para_dashboard_terapeuta(self):
        """Usuário só com terapeuta vai direto ao dashboard de terapeutas"""
        from terapeutas.models import Terapeuta

        # Criar perfil de terapeuta para o usuário
        Terapeuta.objects.create(
            user=self.user,
            nome_completo='João Core',
            nome_exibicao='João',
            slug='joao-core',
            bio_curta='Bio.',
            bio_completa='<p>Bio.</p>',
            formacao='Formação',
            is_active=True,
        )

        self.client.login(username='usuario_core', password='senha123')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('terapeutas:dashboard'))


# ===============================================================
# TESTES DE URLS DO CORE (sanidade geral)
# ===============================================================

class CoreUrlsSanityTest(CoreViewsTestBase):
    """
    Verifica que todas as URLs do app core existem e respondem.
    """

    def test_todas_urls_core_existem(self):
        """Todas as URLs do app core devem existir e não retornar 404"""
        urls = [
            reverse('core:home'),
            reverse('core:sobre'),
            reverse('core:termos'),
            reverse('core:privacidade'),
            reverse('core:cookies'),
            reverse('core:parceiro'),
            reverse('core:faq'),
            reverse('core:contato'),
            reverse('core:indique_terapia'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertNotEqual(
                    response.status_code, 404,
                    f'URL {url} não deveria retornar 404'
                )