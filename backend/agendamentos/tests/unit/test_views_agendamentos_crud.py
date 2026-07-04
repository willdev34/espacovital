# ===============================================================
# Título: Testes das Views do App Agendamentos
# Descrição: Testes unitários para GetComodidadesEspacoView,
#             AgendamentoCriarView, AgendamentoDetalheView,
#             AgendamentoEditarView e AgendamentoCancelarView
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, time

from terapeutas.models import Terapeuta
from espacos.models import Espaco, Comodidade
from agendamentos.models import Sala, Agendamento

User = get_user_model()


class AgendamentosViewsTestBase(TestCase):
    def setUp(self):
        self.client = Client()
        self.visitante = User.objects.create_user(username='visitante_agend', password='senha123')
        self.user_terapeuta = User.objects.create_user(username='terapeuta_agend', email='terapeuta_agend@teste.com', password='senha123')
        self.terapeuta = Terapeuta.objects.create(user=self.user_terapeuta, nome_completo='Terapeuta Agendamento Teste', nome_exibicao='Terapeuta Agend', slug='terapeuta-agendamento-teste', bio_curta='Bio.', bio_completa='<p>Bio.</p>', formacao='Formação', is_active=True)
        self.user_espaco = User.objects.create_user(username='dono_espaco_agend', password='senha123')
        self.espaco = Espaco.objects.create(nome='Espaço Agendamento View Teste', slug='espaco-agendamento-view-teste', descricao_breve='Teste.', descricao_completa='<p>Teste.</p>', endereco='Rua Y, 1', cep='20000-000', bairro='Centro', tipo_espaco='clinica', responsavel=self.user_espaco, is_active=True)
        self.comodidade = Comodidade.objects.create(nome='Wi-Fi', is_active=True)
        self.espaco.comodidades.add(self.comodidade)
        self.sala = Sala.objects.create(espaco=self.espaco, nome='Sala Agendamento View', capacidade=4, valor_sessao=Decimal('90.00'), duracao_sessao=60, horario_abertura='08:00:00', horario_fechamento='18:00:00', is_active=True)
        self.agendamento = Agendamento.objects.create(terapeuta=self.terapeuta, sala=self.sala, espaco=self.espaco, data=date.today(), hora_inicio=time(10, 0), hora_fim=time(11, 0), valor_cobrado=Decimal('90.00'), status='PENDENTE')

    def _login_terapeuta(self):
        self.client.login(username='terapeuta_agend', password='senha123')

    def _login_visitante(self):
        self.client.login(username='visitante_agend', password='senha123')


class GetComodidadesEspacoViewTest(AgendamentosViewsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('agendamentos:get_comodidades_espaco')

    def test_retorna_json_com_espaco_valido(self):
        response = self.client.get(self.url, {'espaco_id': self.espaco.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_retorna_comodidade_correta(self):
        response = self.client.get(self.url, {'espaco_id': self.espaco.pk})
        data = response.json()
        nomes = [c['nome'] for c in data['comodidades']]
        self.assertIn('Wi-Fi', nomes)

    def test_sem_espaco_id_retorna_lista_vazia(self):
        response = self.client.get(self.url)
        self.assertEqual(response.json()['comodidades'], [])

    def test_espaco_inexistente_retorna_lista_vazia(self):
        response = self.client.get(self.url, {'espaco_id': 99999})
        self.assertEqual(response.json()['comodidades'], [])


class AgendamentoCriarViewTest(AgendamentosViewsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('agendamentos:agendamento_create')

    def test_redireciona_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_criar_agendamento(self):
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_valido_cria_agendamento(self):
        self._login_terapeuta()
        total_antes = Agendamento.objects.count()
        dados = {'sala': self.sala.pk, 'data': date.today(), 'hora_inicio': '14:00', 'hora_fim': '15:00', 'observacoes': 'Sessão de teste.'}
        response = self.client.post(self.url, dados)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Agendamento.objects.count(), total_antes + 1)

    def test_post_valido_associa_terapeuta_e_espaco(self):
        self._login_terapeuta()
        dados = {'sala': self.sala.pk, 'data': date.today(), 'hora_inicio': '16:00', 'hora_fim': '17:00', 'observacoes': ''}
        self.client.post(self.url, dados)
        novo = Agendamento.objects.latest('id')
        self.assertEqual(novo.terapeuta, self.terapeuta)
        self.assertEqual(novo.espaco, self.espaco)
        self.assertEqual(novo.valor_cobrado, self.sala.valor_sessao)

    def test_post_invalido_nao_cria_agendamento(self):
        self._login_terapeuta()
        total_antes = Agendamento.objects.count()
        self.client.post(self.url, {})
        self.assertEqual(Agendamento.objects.count(), total_antes)


class AgendamentoDetalheViewTest(AgendamentosViewsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('agendamentos:agendamento_detail', kwargs={'pk': self.agendamento.pk})

    def test_redireciona_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_proprio_agendamento(self):
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_tem_agendamento(self):
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.context['agendamento'], self.agendamento)

    def test_terapeuta_nao_acessa_agendamento_de_outro(self):
        outro_user = User.objects.create_user(username='outro_terapeuta_agend', password='senha123')
        Terapeuta.objects.create(user=outro_user, nome_completo='Outro', nome_exibicao='Outro', slug='outro-terapeuta-agend', bio_curta='Bio.', bio_completa='<p>Bio.</p>', formacao='Formação', is_active=True)
        self.client.login(username='outro_terapeuta_agend', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class AgendamentoEditarViewTest(AgendamentosViewsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('agendamentos:agendamento_update', kwargs={'pk': self.agendamento.pk})

    def test_redireciona_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_acessa_editar_agendamento_pendente(self):
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_nao_permite_editar_agendamento_cancelado(self):
        self.agendamento.status = 'CANCELADO'
        self.agendamento.save()
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_nao_permite_editar_agendamento_de_outro_terapeuta(self):
        outro_user = User.objects.create_user(username='outro_editor_agend', password='senha123')
        Terapeuta.objects.create(user=outro_user, nome_completo='Outro Editor', nome_exibicao='Outro Editor', slug='outro-editor-agend', bio_curta='Bio.', bio_completa='<p>Bio.</p>', formacao='Formação', is_active=True)
        self.client.login(username='outro_editor_agend', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class AgendamentoCancelarViewTest(AgendamentosViewsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('agendamentos:agendamento_cancelar', kwargs={'pk': self.agendamento.pk})

    def test_redireciona_nao_autenticado(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_terapeuta_cancela_proprio_agendamento(self):
        self._login_terapeuta()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_cancelamento_muda_status(self):
        self._login_terapeuta()
        self.client.post(self.url)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, 'CANCELADO')

    def test_nao_permite_cancelar_agendamento_ja_cancelado(self):
        self.agendamento.status = 'CANCELADO'
        self.agendamento.save()
        self._login_terapeuta()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_nao_permite_cancelar_agendamento_de_outro(self):
        outro_user = User.objects.create_user(username='outro_cancelador_agend', password='senha123')
        Terapeuta.objects.create(user=outro_user, nome_completo='Outro Cancelador', nome_exibicao='Outro Cancelador', slug='outro-cancelador-agend', bio_curta='Bio.', bio_completa='<p>Bio.</p>', formacao='Formação', is_active=True)
        self.client.login(username='outro_cancelador_agend', password='senha123')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
