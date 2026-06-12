# ===============================================================
# Título: Testes das Views de Salas do Dashboard de Espaços
# Descrição: Testes unitários para DashboardSalasView,
#             DashboardSalaCriarView, DashboardSalaEditarView
#             e DashboardSalaToggleView
# ===============================================================

import unittest
from decimal import Decimal
from datetime import date

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from espacos.models import Espaco
from agendamentos.models import Sala
from core.models import Assinatura, Plano

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class EspacoSalasTestBase(TestCase):
    """
    Base compartilhada entre todos os testes de salas.
    Cria usuário gestor, espaço, plano premium e sala de teste.
    """

    def setUp(self):
        """Configura dados necessários antes de cada teste"""
        self.client = Client()

        # Usuário gestor do espaço
        self.user_gestor = User.objects.create_user(
            username='gestor_salas',
            email='gestor@salas.com',
            password='senha123',
        )

        # Visitante sem espaço
        self.visitante = User.objects.create_user(
            username='visitante_salas',
            email='visitante@salas.com',
            password='senha123',
        )

        # Espaço vinculado ao gestor
        self.espaco = Espaco.objects.create(
            nome='Espaço Salas Teste',
            slug='espaco-salas-teste',
            descricao_breve='Espaço para testes de salas.',
            descricao_completa='<p>Descrição completa.</p>',
            endereco='Rua das Salas, 42',
            cep='20000-000',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=self.user_gestor,
            is_active=True,
        )

        # Plano Premium S+ (permite gerenciamento de salas)
        self.plano, _ = Plano.objects.get_or_create(
            nome='premium_s_plus',
            defaults={
                'nome_exibicao': 'Premium S+',
                'descricao': 'Plano premium com gerenciamento de salas',
                'valor': Decimal('99.90'),
                'dias_trial': 15,
                'is_active': True,
                'gerenciamento_salas': True,
            }
        )

        # Assinatura ativa do gestor
        self.assinatura = Assinatura.objects.create(
            usuario=self.user_gestor,
            plano=self.plano,
            status='active',
            data_inicio=date.today(),
        )

        # Sala ativa no espaço
        self.sala = Sala.objects.create(
            espaco=self.espaco,
            nome='Sala Zen',
            capacidade=5,
            valor_sessao=Decimal('80.00'),
            duracao_sessao=60,
            horario_abertura='08:00:00',
            horario_fechamento='18:00:00',
            is_active=True,
        )

    def _login_gestor(self):
        """Utilitário: faz login com o usuário gestor"""
        self.client.login(username='gestor_salas', password='senha123')

    def _login_visitante(self):
        """Utilitário: faz login com visitante sem espaço"""
        self.client.login(username='visitante_salas', password='senha123')


# ===============================================================
# TESTES DA DASHBOARD SALAS VIEW (listagem)
# ===============================================================

class DashboardSalasViewTest(EspacoSalasTestBase):
    """
    Testa a DashboardSalasView: listagem de salas do espaço.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_salas')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar para login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_redireciona_visitante_sem_espaco(self):
        """Visitante sem espaço deve ser redirecionado"""
        self._login_visitante()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_acessa_lista_salas(self):
        """Gestor com espaço deve acessar a listagem de salas"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de listagem de salas"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'espacos/dashboard/salas_lista.html')

    def test_contexto_tem_espaco(self):
        """Contexto deve ter o espaço do gestor"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.context['espaco'], self.espaco)

    def test_contexto_tem_total_salas(self):
        """Contexto deve ter o total de salas"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('total_salas', response.context)
        self.assertEqual(response.context['total_salas'], 1)

    def test_contexto_tem_permissao(self):
        """Contexto deve indicar se gestor tem permissão de salas"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('tem_permissao', response.context)

    def test_gestor_com_plano_premium_tem_permissao(self):
        """Gestor com plano premium_s_plus deve ter tem_permissao=True"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTrue(response.context['tem_permissao'])

    def test_gestor_sem_assinatura_nao_tem_permissao(self):
        """Gestor sem assinatura ativa não deve ter permissão"""
        # Cancelar assinatura
        self.assinatura.status = 'cancelled'
        self.assinatura.save()

        self._login_gestor()
        response = self.client.get(self.url)
        self.assertFalse(response.context['tem_permissao'])

    def test_contexto_tem_salas_ativas(self):
        """Contexto deve ter contagem de salas ativas"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('salas_ativas', response.context)


# ===============================================================
# TESTES DA DASHBOARD SALA CRIAR VIEW
# ===============================================================

class DashboardSalaCriarViewTest(EspacoSalasTestBase):
    """
    Testa a DashboardSalaCriarView: criação de nova sala.
    Disponível apenas para planos Premium S+.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_sala_criar')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_com_permissao_acessa_form(self):
        """Gestor com plano premium_s_plus deve acessar o formulário"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de formulário de sala"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'espacos/dashboard/sala_form.html')

    def test_contexto_tem_espaco(self):
        """Contexto deve ter o espaço do gestor"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('espaco', response.context)

    def test_gestor_sem_permissao_redireciona(self):
        """Gestor com plano básico deve ser redirecionado"""
        # Trocar para plano básico sem permissão de salas
        plano_basic, _ = Plano.objects.get_or_create(
            nome='basic',
            defaults={
                'nome_exibicao': 'Basic',
                'descricao': 'Plano básico',
                'valor': Decimal('19.90'),
                'dias_trial': 7,
                'is_active': True,
                'gerenciamento_salas': False,
            }
        )
        self.assinatura.plano = plano_basic
        self.assinatura.save()

        self._login_gestor()
        response = self.client.get(self.url)
        # Deve redirecionar para a listagem de salas com mensagem de erro
        self.assertEqual(response.status_code, 302)
        self.assertIn('salas', response.url)

    def test_post_cria_sala_com_dados_validos(self):
        """POST com dados válidos deve criar uma nova sala"""
        salas_antes = Sala.objects.filter(espaco=self.espaco).count()
        self._login_gestor()
        dados = {
            'nome': 'Sala Nova Teste',
            'capacidade': 3,
            'valor_sessao': '60.00',
            'duracao_sessao': 45,
            'horario_abertura': '09:00:00',
            'horario_fechamento': '17:00:00',
        }
        response = self.client.post(self.url, dados)
        # Deve redirecionar após criar com sucesso
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Sala.objects.filter(espaco=self.espaco).count(),
            salas_antes + 1
        )


# ===============================================================
# TESTES DA DASHBOARD SALA EDITAR VIEW
# ===============================================================

class DashboardSalaEditarViewTest(EspacoSalasTestBase):
    """
    Testa a DashboardSalaEditarView: edição de sala existente.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_sala_editar', kwargs={'pk': self.sala.pk})

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_com_permissao_acessa_form(self):
        """Gestor com plano premium_s_plus deve acessar o formulário de edição"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de formulário de sala"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'espacos/dashboard/sala_form.html')

    def test_contexto_tem_espaco(self):
        """Contexto deve ter o espaço do gestor"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('espaco', response.context)

    def test_gestor_sem_permissao_redireciona(self):
        """Gestor com plano básico deve ser redirecionado"""
        plano_basic, _ = Plano.objects.get_or_create(
            nome='basic',
            defaults={
                'nome_exibicao': 'Basic',
                'descricao': 'Plano básico',
                'valor': Decimal('19.90'),
                'dias_trial': 7,
                'is_active': True,
            }
        )
        self.assinatura.plano = plano_basic
        self.assinatura.save()

        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_post_atualiza_sala(self):
        """POST com dados válidos deve atualizar a sala"""
        self._login_gestor()
        dados = {
            'nome': 'Sala Zen Atualizada',
            'capacidade': 8,
            'valor_sessao': '90.00',
            'duracao_sessao': 60,
            'horario_abertura': '08:00:00',
            'horario_fechamento': '20:00:00',
            'is_active': True,
        }
        response = self.client.post(self.url, dados)
        self.assertEqual(response.status_code, 302)

        # Verificar que o nome foi atualizado
        self.sala.refresh_from_db()
        self.assertEqual(self.sala.nome, 'Sala Zen Atualizada')


# ===============================================================
# TESTES DA DASHBOARD SALA TOGGLE VIEW
# ===============================================================

class DashboardSalaToggleViewTest(EspacoSalasTestBase):
    """
    Testa a DashboardSalaToggleView: ativar/desativar sala.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_sala_toggle', kwargs={'pk': self.sala.pk})

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_toggle_desativa_sala_ativa(self):
        """Toggle em sala ativa deve desativá-la"""
        self.sala.is_active = True
        self.sala.save()

        self._login_gestor()
        response = self.client.get(self.url)

        # Deve redirecionar após o toggle
        self.assertEqual(response.status_code, 302)

        # Sala deve estar inativa agora
        self.sala.refresh_from_db()
        self.assertFalse(self.sala.is_active)

    def test_toggle_ativa_sala_inativa(self):
        """Toggle em sala inativa deve ativá-la"""
        self.sala.is_active = False
        self.sala.save()

        self._login_gestor()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

        # Sala deve estar ativa agora
        self.sala.refresh_from_db()
        self.assertTrue(self.sala.is_active)

    def test_toggle_redireciona_para_lista_salas(self):
        """Após toggle deve redirecionar para lista de salas"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('salas', response.url)

    def test_sala_inexistente_retorna_404_ou_redireciona(self):
        """Toggle em sala inexistente deve retornar 404 ou redirecionar"""
        self._login_gestor()
        url = reverse('espacos:dashboard_sala_toggle', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 404])