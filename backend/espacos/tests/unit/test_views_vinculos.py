# ===============================================================
# Título: Testes das Views de Vínculos e Pagamentos - Espaço Vital
# Descrição: Testes unitários para DashboardTerapeutasVinculadosView,
#             DashboardDisponibilidadeView, DashboardPagamentosEspacoView,
#             AprovarVinculoTerapeutaView, RecusarVinculoTerapeutaView
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date

from espacos.models import Espaco
from terapeutas.models import Terapeuta
from agendamentos.models import VinculoTerapeutaEspaco

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class EspacoVinculosTestBase(TestCase):
    """
    Base compartilhada entre todos os testes de vínculos.
    Cria usuário gestor, espaço, terapeuta e vínculo.
    """

    def setUp(self):
        """Configura dados necessários antes de cada teste"""
        self.client = Client()

        # Usuário gestor do espaço
        self.user_gestor = User.objects.create_user(
            username='gestor_vinculos',
            email='gestor@vinculos.com',
            password='senha123',
            first_name='Pedro',
        )

        # Usuário visitante sem espaço
        self.visitante = User.objects.create_user(
            username='visitante_vinculos',
            email='visitante@vinculos.com',
            password='senha123',
        )

        # Usuário terapeuta para vincular
        self.user_terapeuta = User.objects.create_user(
            username='terapeuta_vinculo',
            email='terapeuta@vinculo.com',
            password='senha123',
            first_name='Ana',
        )

        # Espaço do gestor
        self.espaco = Espaco.objects.create(
            nome='Espaço Vínculos Teste',
            slug='espaco-vinculos-teste',
            descricao_breve='Espaço para testes de vínculos.',
            descricao_completa='<p>Descrição.</p>',
            endereco='Rua dos Vínculos, 10',
            cep='20000-001',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=self.user_gestor,
            is_active=True,
        )

        # Terapeuta para vincular ao espaço
        self.terapeuta = Terapeuta.objects.create(
            user=self.user_terapeuta,
            nome_completo='Ana Terapeuta Vínculo',
            nome_exibicao='Ana Vínculo',
            slug='ana-terapeuta-vinculo',
            bio_curta='Bio de teste.',
            bio_completa='<p>Bio.</p>',
            formacao='Formação',
            is_active=True,
        )

        # Vínculo pendente entre terapeuta e espaço
        self.vinculo = VinculoTerapeutaEspaco.objects.create(
            terapeuta=self.terapeuta,
            espaco=self.espaco,
            status='PENDENTE',
            tipo='SOLICITACAO',
            is_active=True,
        )

    def _login_gestor(self):
        """Utilitário: faz login com o gestor do espaço"""
        self.client.login(username='gestor_vinculos', password='senha123')

    def _login_visitante(self):
        """Utilitário: faz login com visitante sem espaço"""
        self.client.login(username='visitante_vinculos', password='senha123')


# ===============================================================
# TESTES DA DASHBOARD TERAPEUTAS VINCULADOS VIEW
# ===============================================================

class DashboardTerapeutasVinculadosViewTest(EspacoVinculosTestBase):
    """
    Testa a DashboardTerapeutasVinculadosView: gerenciar terapeutas.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_terapeutas')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redireciona_visitante_sem_espaco(self):
        """Visitante sem espaço deve ser redirecionado"""
        self._login_visitante()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_acessa_terapeutas_vinculados(self):
        """Gestor deve acessar a página de terapeutas vinculados"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de terapeutas vinculados"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTemplateUsed(
            response,
            'espacos/dashboard/terapeutas_vinculados.html'
        )

    def test_contexto_tem_espaco(self):
        """Contexto deve ter o espaço do gestor"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.context['espaco'], self.espaco)

    def test_contexto_tem_solicitacoes_pendentes(self):
        """Contexto deve ter as solicitações pendentes"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('solicitacoes_pendentes', response.context)

    def test_contexto_tem_terapeutas_vinculados(self):
        """Contexto deve ter a lista de terapeutas aprovados"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('terapeutas_vinculados', response.context)

    def test_contexto_tem_total_pendentes(self):
        """Contexto deve ter o total de solicitações pendentes"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('total_pendentes', response.context)
        self.assertEqual(response.context['total_pendentes'], 1)


# ===============================================================
# TESTES DA APROVAR VÍNCULO VIEW
# ===============================================================

class AprovarVinculoTerapeutaViewTest(EspacoVinculosTestBase):
    """
    Testa a AprovarVinculoTerapeutaView: aprovar solicitação de vínculo.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'espacos:aprovar_vinculo_terapeuta',
            kwargs={'vinculo_id': self.vinculo.pk}
        )

    def test_redireciona_nao_autenticado(self):
        """POST sem login deve redirecionar"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_aprovar_vinculo_pendente(self):
        """POST deve aprovar o vínculo e redirecionar"""
        self._login_gestor()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

        # Verificar que o vínculo foi aprovado
        self.vinculo.refresh_from_db()
        self.assertEqual(self.vinculo.status, 'APROVADO')

    def test_aprovar_vinculo_define_data_aprovacao(self):
        """Aprovar vínculo deve registrar a data de aprovação"""
        self._login_gestor()
        self.client.post(self.url)

        self.vinculo.refresh_from_db()
        self.assertIsNotNone(self.vinculo.data_aprovacao)

    def test_aprovar_redireciona_para_terapeutas(self):
        """Após aprovar, deve redirecionar para lista de terapeutas"""
        self._login_gestor()
        response = self.client.post(self.url)
        self.assertIn('terapeutas', response.url)

    def test_nao_pode_aprovar_vinculo_de_outro_espaco(self):
        """Gestor não pode aprovar vínculo de espaço que não é seu"""
        # Criar outro usuário e tentar aprovar o vínculo do gestor
        outro_gestor = User.objects.create_user(
            username='outro_gestor',
            password='senha123'
        )
        Espaco.objects.create(
            nome='Outro Espaço',
            slug='outro-espaco-teste',
            descricao_breve='Outro.',
            descricao_completa='<p>Outro.</p>',
            endereco='Rua Y',
            cep='20000-002',
            bairro='Bairro',
            tipo_espaco='clinica',
            responsavel=outro_gestor,
            is_active=True,
        )
        self.client.login(username='outro_gestor', password='senha123')
        response = self.client.post(self.url)
        # Deve retornar 404 pois o vínculo não é deste espaço
        self.assertEqual(response.status_code, 404)


# ===============================================================
# TESTES DA RECUSAR VÍNCULO VIEW
# ===============================================================

class RecusarVinculoTerapeutaViewTest(EspacoVinculosTestBase):
    """
    Testa a RecusarVinculoTerapeutaView: recusar solicitação de vínculo.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'espacos:recusar_vinculo_terapeuta',
            kwargs={'vinculo_id': self.vinculo.pk}
        )

    def test_redireciona_nao_autenticado(self):
        """POST sem login deve redirecionar"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_recusar_vinculo_pendente(self):
        """POST deve recusar o vínculo"""
        self._login_gestor()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

        # Verificar que o vínculo foi recusado
        self.vinculo.refresh_from_db()
        self.assertEqual(self.vinculo.status, 'RECUSADO')

    def test_recusar_vinculo_desativa(self):
        """Recusar vínculo deve desativá-lo"""
        self._login_gestor()
        self.client.post(self.url)

        self.vinculo.refresh_from_db()
        self.assertFalse(self.vinculo.is_active)

    def test_recusar_redireciona_para_terapeutas(self):
        """Após recusar, deve redirecionar para lista de terapeutas"""
        self._login_gestor()
        response = self.client.post(self.url)
        self.assertIn('terapeutas', response.url)


# ===============================================================
# TESTES DA CONVIDAR TERAPEUTA VIEW
# ===============================================================

class ConvidarTerapeutaViewTest(EspacoVinculosTestBase):
    """
    Testa a ConvidarTerapeutaView: enviar convite para terapeuta.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:convidar_terapeuta')

    def test_redireciona_nao_autenticado(self):
        """POST sem login deve redirecionar"""
        response = self.client.post(self.url, {'email_terapeuta': 'test@test.com'})
        self.assertEqual(response.status_code, 302)

    def test_convidar_terapeuta_cadastrado(self):
        """POST com email de terapeuta cadastrado deve criar vínculo"""
        self._login_gestor()

        # Remover vínculo existente para testar criação
        self.vinculo.delete()

        response = self.client.post(self.url, {
            'email_terapeuta': self.user_terapeuta.email,
            'mensagem': 'Venha fazer parte do nosso espaço!',
        })
        self.assertEqual(response.status_code, 302)

        # Verificar que vínculo foi criado
        self.assertTrue(
            VinculoTerapeutaEspaco.objects.filter(
                terapeuta=self.terapeuta,
                espaco=self.espaco,
                status='PENDENTE'
            ).exists()
        )

    def test_convidar_sem_email_redireciona_com_erro(self):
        """POST sem email deve redirecionar com mensagem de erro"""
        self._login_gestor()
        response = self.client.post(self.url, {'email_terapeuta': ''})
        self.assertEqual(response.status_code, 302)

    def test_convidar_terapeuta_ja_vinculado(self):
        """Convidar terapeuta já vinculado deve mostrar aviso"""
        # Aprovar vínculo existente
        self.vinculo.status = 'APROVADO'
        self.vinculo.save()

        self._login_gestor()
        response = self.client.post(self.url, {
            'email_terapeuta': self.user_terapeuta.email,
        })
        # Deve redirecionar com mensagem de aviso
        self.assertEqual(response.status_code, 302)


# ===============================================================
# TESTES DA DASHBOARD DISPONIBILIDADE VIEW
# ===============================================================

class DashboardDisponibilidadeViewTest(EspacoVinculosTestBase):
    """
    Testa a DashboardDisponibilidadeView: gerenciar disponibilidade.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_disponibilidade')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_acessa_disponibilidade(self):
        """Gestor deve acessar a página de disponibilidade"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de disponibilidade"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTemplateUsed(
            response,
            'espacos/dashboard/disponibilidade.html'
        )

    def test_contexto_tem_espaco(self):
        """Contexto deve ter o espaço"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.context['espaco'], self.espaco)

    def test_contexto_tem_horarios_semana(self):
        """Contexto deve ter horários da semana"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('horarios_semana', response.context)

    def test_contexto_tem_periodos_disponiveis(self):
        """Contexto deve ter lista de períodos disponíveis"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('periodos_disponiveis', response.context)


# ===============================================================
# TESTES DA DASHBOARD PAGAMENTOS VIEW
# ===============================================================

class DashboardPagamentosEspacoViewTest(EspacoVinculosTestBase):
    """
    Testa a DashboardPagamentosEspacoView: gerenciar pagamentos.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('espacos:dashboard_pagamentos')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve redirecionar"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_gestor_acessa_pagamentos(self):
        """Gestor deve acessar a página de pagamentos"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de pagamentos"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertTemplateUsed(
            response,
            'espacos/dashboard/pagamentos.html'
        )

    def test_contexto_tem_espaco(self):
        """Contexto deve ter o espaço"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertEqual(response.context['espaco'], self.espaco)

    def test_contexto_tem_receita_total(self):
        """Contexto deve ter receita total"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('receita_total', response.context)

    def test_contexto_tem_transacoes(self):
        """Contexto deve ter lista de transações"""
        self._login_gestor()
        response = self.client.get(self.url)
        self.assertIn('transacoes', response.context)