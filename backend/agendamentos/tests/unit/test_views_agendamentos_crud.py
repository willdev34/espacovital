# ===============================================================
# Título: Testes das Views do App Agendamentos
# Descrição: Testes unitários para GetComodidadesEspacoView,
#            AgendamentoCriarView, AgendamentoDetalheView,
#            AgendamentoEditarView e AgendamentoCancelarView.
#            Usa datas relativas (amanhã) dentro do horário de
#            funcionamento da sala (08:00 às 18:00).
# Autor: Will
# Data: 13/10/2026
# ===============================================================

from datetime import time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from agendamentos.models import Sala, Agendamento
from espacos.models import Espaco, Comodidade
from terapeutas.models import Terapeuta

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class AgendamentosViewsTestBase(TestCase):
    """
    Base compartilhada entre os testes do app agendamentos.
    Cria terapeuta, espaço, sala (08:00 às 18:00) e um agendamento
    pendente para amanhã às 10:00.
    """

    def setUp(self):
        """Cria dados base antes de cada teste"""
        self.client = Client()

        # Data de referência: amanhã no fuso do projeto
        self.amanha = timezone.localdate() + timedelta(days=1)

        # Usuário terapeuta
        self.user_terapeuta = User.objects.create_user(
            username='terapeuta_agend',
            email='terapeuta_agend@teste.com',
            password='senha123',
        )
        self.terapeuta = Terapeuta.objects.create(
            user=self.user_terapeuta,
            nome_completo='Terapeuta Agendamento Teste',
            nome_exibicao='Terapeuta Agend',
            slug='terapeuta-agendamento-teste',
            bio_curta='Bio.',
            bio_completa='<p>Bio.</p>',
            formacao='Formação',
            is_active=True,
        )

        # Espaço com uma comodidade
        self.user_espaco = User.objects.create_user(
            username='dono_espaco_agend', password='senha123'
        )
        self.espaco = Espaco.objects.create(
            nome='Espaço Agendamento View Teste',
            slug='espaco-agendamento-view-teste',
            descricao_breve='Teste.',
            descricao_completa='<p>Teste.</p>',
            endereco='Rua Y, 1',
            cep='20000-000',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=self.user_espaco,
            is_active=True,
        )
        self.comodidade = Comodidade.objects.create(
            nome='Wi-Fi',
            is_active=True,
        )
        self.espaco.comodidades.add(self.comodidade)

        # Sala ativa, funciona das 08:00 às 18:00
        self.sala = Sala.objects.create(
            espaco=self.espaco,
            nome='Sala Agendamento View',
            capacidade=4,
            valor_sessao=Decimal('90.00'),
            duracao_sessao=60,
            horario_abertura='08:00:00',
            horario_fechamento='18:00:00',
            is_active=True,
        )

        # Agendamento pendente do terapeuta, amanhã das 10:00 às 11:00
        self.agendamento = Agendamento.objects.create(
            terapeuta=self.terapeuta,
            sala=self.sala,
            espaco=self.espaco,
            data=self.amanha,
            hora_inicio=time(10, 0),
            hora_fim=time(11, 0),
            valor_cobrado=Decimal('90.00'),
            status='PENDENTE',
        )

    def _login_terapeuta(self):
        """Utilitário: faz login com o terapeuta"""
        self.client.login(username='terapeuta_agend', password='senha123')

    def _login_outro_terapeuta(self, username):
        """
        Utilitário: cria um segundo terapeuta e faz login com ele.
        Usado nos testes de acesso ao agendamento de outra pessoa.
        """
        outro_user = User.objects.create_user(
            username=username, password='senha123'
        )
        Terapeuta.objects.create(
            user=outro_user,
            nome_completo=f'Outro {username}',
            nome_exibicao=f'Outro {username}',
            slug=f'slug-{username}',
            bio_curta='Bio.',
            bio_completa='<p>Bio.</p>',
            formacao='Formação',
            is_active=True,
        )
        self.client.login(username=username, password='senha123')

    def _mensagens(self, response):
        """Utilitário: devolve os textos das mensagens da resposta"""
        return [str(m) for m in get_messages(response.wsgi_request)]

    def _assert_redireciona_para_login(self, response):
        """Utilitário: confere que o acesso anônimo foi mandado ao login"""
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))


# ===============================================================
# TESTES DA VIEW AJAX DE COMODIDADES
# ===============================================================

class GetComodidadesEspacoViewTest(AgendamentosViewsTestBase):
    """
    Testa a GetComodidadesEspacoView: retorna comodidades de um espaço via AJAX.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('agendamentos:get_comodidades_espaco')

    def test_retorna_json_com_espaco_valido(self):
        """GET com espaco_id válido deve retornar JSON"""
        response = self.client.get(self.url, {'espaco_id': self.espaco.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_retorna_comodidade_correta(self):
        """Deve retornar exatamente a comodidade cadastrada no espaço"""
        response = self.client.get(self.url, {'espaco_id': self.espaco.pk})
        nomes = [c['nome'] for c in response.json()['comodidades']]
        self.assertEqual(nomes, ['Wi-Fi'])

    def test_sem_espaco_id_retorna_lista_vazia(self):
        """GET sem espaco_id deve retornar lista vazia"""
        response = self.client.get(self.url)
        self.assertEqual(response.json()['comodidades'], [])

    def test_espaco_inexistente_retorna_lista_vazia(self):
        """GET com espaco_id inexistente deve retornar lista vazia"""
        response = self.client.get(self.url, {'espaco_id': 99999})
        self.assertEqual(response.json()['comodidades'], [])


# ===============================================================
# TESTES DA VIEW DE CRIAR AGENDAMENTO
# ===============================================================

class AgendamentoCriarViewTest(AgendamentosViewsTestBase):
    """
    Testa a AgendamentoCriarView: criação de novo agendamento.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('agendamentos:agendamento_create')
        self.url_dashboard = reverse('terapeutas:dashboard_agendamentos')

    def _dados_validos(self, hora_inicio='14:00', hora_fim='15:00', **extra):
        """Utilitário: dados válidos para amanhã dentro do horário da sala"""
        dados = {
            'sala': self.sala.pk,
            'data': self.amanha,
            'hora_inicio': hora_inicio,
            'hora_fim': hora_fim,
            'observacoes': 'Sessão de teste.',
        }
        dados.update(extra)
        return dados

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve ir para a tela de login"""
        response = self.client.get(self.url)
        self._assert_redireciona_para_login(response)

    def test_terapeuta_acessa_criar_agendamento(self):
        """Terapeuta logado deve acessar o formulário"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_form_lista_apenas_salas_ativas(self):
        """Formulário lista a sala ativa e deixa de fora a inativa"""
        sala_inativa = Sala.objects.create(
            espaco=self.espaco,
            nome='Sala Inativa',
            capacidade=2,
            valor_sessao=Decimal('50.00'),
            duracao_sessao=60,
            horario_abertura='08:00:00',
            horario_fechamento='18:00:00',
            is_active=False,
        )
        self._login_terapeuta()
        response = self.client.get(self.url)
        salas = response.context['form'].fields['sala'].queryset
        self.assertIn(self.sala, salas)
        self.assertNotIn(sala_inativa, salas)

    def test_post_valido_cria_agendamento(self):
        """POST válido cria o agendamento, avisa e volta ao dashboard"""
        self._login_terapeuta()
        total_antes = Agendamento.objects.count()
        response = self.client.post(self.url, self._dados_validos())
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.assertEqual(Agendamento.objects.count(), total_antes + 1)
        self.assertIn(
            '✅ Agendamento criado com sucesso!', self._mensagens(response)
        )

    def test_post_valido_associa_terapeuta_espaco_e_valor(self):
        """Agendamento criado leva terapeuta, espaço e valor da sala"""
        self._login_terapeuta()
        self.client.post(
            self.url, self._dados_validos(hora_inicio='16:00', hora_fim='17:00')
        )
        novo = Agendamento.objects.latest('id')
        self.assertEqual(novo.terapeuta, self.terapeuta)
        self.assertEqual(novo.espaco, self.espaco)
        self.assertEqual(novo.sala, self.sala)
        self.assertEqual(novo.data, self.amanha)
        self.assertEqual(novo.hora_inicio, time(16, 0))
        self.assertEqual(novo.hora_fim, time(17, 0))
        self.assertEqual(novo.valor_cobrado, self.sala.valor_sessao)

    def test_post_invalido_reexibe_formulario_com_erros(self):
        """POST vazio não cria nada, volta 200 com erros e mensagem"""
        self._login_terapeuta()
        total_antes = Agendamento.objects.count()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Agendamento.objects.count(), total_antes)
        erros = response.context['form'].errors
        self.assertIn('sala', erros)
        self.assertIn('data', erros)
        self.assertIn(
            '❌ Erro ao criar agendamento. Verifique os dados e tente novamente.',
            self._mensagens(response),
        )


# ===============================================================
# TESTES DA VIEW DE DETALHE DO AGENDAMENTO
# ===============================================================

class AgendamentoDetalheViewTest(AgendamentosViewsTestBase):
    """
    Testa a AgendamentoDetalheView: exibição de detalhes do agendamento.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'agendamentos:agendamento_detail',
            kwargs={'pk': self.agendamento.pk}
        )

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve ir para a tela de login"""
        response = self.client.get(self.url)
        self._assert_redireciona_para_login(response)

    def test_terapeuta_acessa_proprio_agendamento(self):
        """Terapeuta deve acessar o próprio agendamento"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de detalhe"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'agendamentos/agendamento_detail.html')

    def test_contexto_tem_agendamento(self):
        """Contexto deve ter o objeto agendamento correto"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.context['agendamento'], self.agendamento)

    def test_terapeuta_nao_acessa_agendamento_de_outro(self):
        """Terapeuta não deve acessar agendamento de outro terapeuta"""
        self._login_outro_terapeuta('outro_terapeuta_agend')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


# ===============================================================
# TESTES DA VIEW DE EDITAR AGENDAMENTO
# ===============================================================

class AgendamentoEditarViewTest(AgendamentosViewsTestBase):
    """
    Testa a AgendamentoEditarView: edição de agendamento existente.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'agendamentos:agendamento_update',
            kwargs={'pk': self.agendamento.pk}
        )
        self.url_dashboard = reverse('terapeutas:dashboard_agendamentos')

    def test_redireciona_nao_autenticado(self):
        """GET sem login deve ir para a tela de login"""
        response = self.client.get(self.url)
        self._assert_redireciona_para_login(response)

    def test_terapeuta_acessa_editar_agendamento_pendente(self):
        """Terapeuta deve acessar a edição de agendamento pendente"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_valido_atualiza_horario_valor_e_observacoes(self):
        """POST válido atualiza horário, valor e observações"""
        self._login_terapeuta()
        dados = {
            'data': self.amanha,
            'hora_inicio': '11:00',
            'hora_fim': '12:00',
            'observacoes': 'Atualizado.',
            'valor_cobrado': '95.00',
        }
        response = self.client.post(self.url, dados)
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.hora_inicio, time(11, 0))
        self.assertEqual(self.agendamento.hora_fim, time(12, 0))
        self.assertEqual(self.agendamento.valor_cobrado, Decimal('95.00'))
        self.assertEqual(self.agendamento.observacoes, 'Atualizado.')
        self.assertIn(
            '✅ Agendamento atualizado com sucesso!', self._mensagens(response)
        )

    def test_nao_permite_editar_agendamento_cancelado(self):
        """Não deve permitir editar agendamento já cancelado"""
        self.agendamento.status = 'CANCELADO'
        self.agendamento.save()

        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_nao_permite_editar_agendamento_de_outro_terapeuta(self):
        """Terapeuta não deve editar agendamento de outro"""
        self._login_outro_terapeuta('outro_editor_agend')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


# ===============================================================
# TESTES DA VIEW DE CANCELAR AGENDAMENTO
# ===============================================================

class AgendamentoCancelarViewTest(AgendamentosViewsTestBase):
    """
    Testa a AgendamentoCancelarView: cancelamento de agendamento.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'agendamentos:agendamento_cancelar',
            kwargs={'pk': self.agendamento.pk}
        )
        self.url_dashboard = reverse('terapeutas:dashboard_agendamentos')

    def test_redireciona_nao_autenticado(self):
        """POST sem login deve ir para a tela de login"""
        response = self.client.post(self.url)
        self._assert_redireciona_para_login(response)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, 'PENDENTE')

    def test_terapeuta_cancela_proprio_agendamento(self):
        """Cancelar volta ao dashboard e mostra mensagem de sucesso"""
        self._login_terapeuta()
        response = self.client.post(self.url)
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.assertIn(
            '✅ Agendamento cancelado com sucesso!', self._mensagens(response)
        )

    def test_cancelamento_muda_status(self):
        """Cancelar deve mudar o status para CANCELADO"""
        self._login_terapeuta()
        self.client.post(self.url)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, 'CANCELADO')

    def test_get_nao_e_permitido(self):
        """A view só aceita POST: GET devolve 405 e não cancela"""
        self._login_terapeuta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, 'PENDENTE')

    def test_nao_permite_cancelar_agendamento_ja_cancelado(self):
        """Não deve permitir cancelar agendamento já cancelado"""
        self.agendamento.status = 'CANCELADO'
        self.agendamento.save()

        self._login_terapeuta()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_nao_permite_cancelar_agendamento_de_outro(self):
        """Terapeuta não deve cancelar agendamento de outro"""
        self._login_outro_terapeuta('outro_cancelador_agend')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, 'PENDENTE')
