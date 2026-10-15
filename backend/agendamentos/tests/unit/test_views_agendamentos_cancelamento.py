# ===============================================================
# Título: Testes de Cancelamento de Agendamento com Multa
# Descrição: Garante a regra de cancelamento: PENDENTE cancela sempre
#            sem multa; CONFIRMADO paga a multa fixa da sala quando
#            cancela com menos antecedência que o prazo da sala (ou
#            depois do início); CONCLUIDO e CANCELADO são bloqueados;
#            cancelar duas vezes não cria duas multas; a multa e o
#            cancelamento são atômicos; o motivo é truncado; o aviso
#            do detalhe e da lista mostra a multa; só o dono cancela.
#            O "agora" é fixado com mock de timezone.now para que as
#            fronteiras (exatamente no prazo) sejam determinísticas.
# Autor: Will
# Data: 13/10/2026
# ===============================================================

from datetime import time, timedelta
from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from agendamentos.models import Agendamento, Multa, Sala
from espacos.models import Espaco
from terapeutas.models import Terapeuta

User = get_user_model()

# Módulo onde o "agora" é lido pela regra de cancelamento
NOW = 'django.utils.timezone.now'


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class CancelamentoBase(TestCase):
    """
    Base compartilhada: terapeuta logado e uma sala com prazo de
    cancelamento sem multa de 60 minutos e multa fixa de R$ 25,00.
    O "agora" é fixo (self.agora, sem segundos) e cada agendamento é
    criado a N minutos dele, para fronteiras exatas.
    """

    def setUp(self):
        """Cria os dados base antes de cada teste"""
        self.client = Client()

        # "Agora" fixo, sem segundos, para contar minutos exatos
        self.agora = timezone.now().replace(second=0, microsecond=0)

        # Terapeuta logado nos testes
        self.user_terapeuta = User.objects.create_user(
            username='terapeuta_cancelamento', password='senha123'
        )
        self.terapeuta = self._criar_terapeuta(self.user_terapeuta, 'cancel')

        # Espaço e sala: prazo de 60 min, multa fixa de R$ 25,00
        dono = User.objects.create_user(
            username='dono_cancelamento', password='senha123'
        )
        self.espaco = Espaco.objects.create(
            nome='Espaço Cancelamento',
            slug='espaco-cancelamento',
            descricao_breve='Teste.',
            descricao_completa='<p>Teste.</p>',
            endereco='Rua Y, 1',
            cep='20000-000',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=dono,
            is_active=True,
        )
        self.sala = Sala.objects.create(
            espaco=self.espaco,
            nome='Sala Cancelamento',
            capacidade=4,
            valor_sessao=Decimal('90.00'),
            duracao_sessao=60,
            horario_abertura='00:00:00',
            horario_fechamento='23:59:00',
            prazo_cancelamento_sem_multa=60,
            valor_multa_cancelamento=Decimal('25.00'),
            is_active=True,
        )

        self.url_dashboard = reverse('terapeutas:dashboard_agendamentos')
        self.client.login(username='terapeuta_cancelamento', password='senha123')

    # -----------------------------------------------------------
    # Utilitários de criação de dados
    # -----------------------------------------------------------

    def _criar_terapeuta(self, user, sufixo):
        """Cria o perfil de terapeuta de um usuário"""
        return Terapeuta.objects.create(
            user=user,
            nome_completo=f'Terapeuta {sufixo}',
            nome_exibicao=f'Terapeuta {sufixo}',
            slug=f'terapeuta-{sufixo}',
            bio_curta='Bio.',
            bio_completa='<p>Bio.</p>',
            formacao='Formação',
            is_active=True,
        )

    def _novo(self, minutos, status='CONFIRMADO', **extra):
        """
        Cria um agendamento que começa a `minutos` do "agora" fixo
        (negativo = já começou), no fuso local do projeto.
        """
        inicio = timezone.localtime(self.agora + timedelta(minutes=minutos))
        fim = inicio + timedelta(hours=1)
        dados = dict(
            terapeuta=self.terapeuta,
            sala=self.sala,
            espaco=self.espaco,
            data=inicio.date(),
            hora_inicio=inicio.time(),
            hora_fim=fim.time(),
            valor_cobrado=Decimal('90.00'),
            status=status,
        )
        dados.update(extra)
        return Agendamento.objects.create(**dados)

    def _url_cancelar(self, agendamento):
        """URL do cancelamento da view do app agendamentos"""
        return reverse(
            'agendamentos:agendamento_cancelar', kwargs={'pk': agendamento.pk}
        )

    def _url_detalhe(self, agendamento):
        """URL do detalhe do agendamento"""
        return reverse(
            'agendamentos:agendamento_detail', kwargs={'pk': agendamento.pk}
        )

    # -----------------------------------------------------------
    # Utilitários de ação e verificação
    # -----------------------------------------------------------

    def _cancelar(self, agendamento, multa_prevista='auto', **dados):
        """
        POST de cancelamento com o "agora" fixo. Por padrão envia em
        multa_prevista o valor que o aviso da tela mostraria; passe um
        valor para forçar outro, ou None para omitir o campo.
        """
        with mock.patch(NOW, return_value=self.agora):
            if multa_prevista == 'auto':
                atual = Agendamento.objects.get(pk=agendamento.pk)
                multa_prevista = atual.previsao_multa()['valor']
            if multa_prevista is not None:
                dados['multa_prevista'] = str(multa_prevista)
            return self.client.post(self._url_cancelar(agendamento), dados)

    def _mensagens(self, response):
        """Devolve os textos das mensagens da resposta"""
        return [str(m) for m in get_messages(response.wsgi_request)]

    def _assert_cancelado_com(self, response, agendamento, total_multas):
        """Redirect para a lista, status CANCELADO e o total de multas"""
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, 'CANCELADO')
        self.assertEqual(Multa.objects.count(), total_multas)

    def _assert_nada_mudou(self, agendamento, status):
        """Status continua o mesmo e nenhuma multa existe"""
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, status)
        self.assertEqual(Multa.objects.count(), 0)


# ===============================================================
# REGRA DA MULTA
# ===============================================================

class CancelamentoMultaTest(CancelamentoBase):
    """
    Multa só para CONFIRMADO, com o valor fixo da sala.
    """

    # ----- PENDENTE: nunca gera multa -----

    def test_pendente_dentro_do_prazo_cancela_sem_multa(self):
        """PENDENTE a 3 horas do início: cancela, sem multa"""
        agendamento = self._novo(180, status='PENDENTE')
        response = self._cancelar(agendamento)
        self._assert_cancelado_com(response, agendamento, 0)

    def test_pendente_fora_do_prazo_cancela_sem_multa(self):
        """PENDENTE a 30 min do início (fora do prazo): sem multa"""
        agendamento = self._novo(30, status='PENDENTE')
        response = self._cancelar(agendamento)
        self._assert_cancelado_com(response, agendamento, 0)

    def test_pendente_depois_do_inicio_cancela_sem_multa(self):
        """PENDENTE que já passou da hora: cancela, sem multa"""
        agendamento = self._novo(-30, status='PENDENTE')
        response = self._cancelar(agendamento)
        self._assert_cancelado_com(response, agendamento, 0)

    # ----- CONFIRMADO: multa conforme o prazo -----

    def test_confirmado_dentro_do_prazo_cancela_sem_multa(self):
        """CONFIRMADO a 2 horas do início: sem multa"""
        agendamento = self._novo(120)
        response = self._cancelar(agendamento)
        self._assert_cancelado_com(response, agendamento, 0)

    def test_confirmado_exatamente_no_prazo_cancela_sem_multa(self):
        """CONFIRMADO a exatamente 60 min do início: sem multa"""
        agendamento = self._novo(60)
        response = self._cancelar(agendamento)
        self._assert_cancelado_com(response, agendamento, 0)

    def test_confirmado_fora_do_prazo_cria_multa_com_valor_da_sala(self):
        """CONFIRMADO a 59 min do início: multa de R$ 25,00 pendente"""
        agendamento = self._novo(59)
        response = self._cancelar(agendamento)
        self._assert_cancelado_com(response, agendamento, 1)

        multa = Multa.objects.get()
        self.assertEqual(multa.valor, Decimal('25.00'))
        self.assertEqual(multa.terapeuta, self.terapeuta)
        self.assertEqual(multa.espaco, self.espaco)
        self.assertEqual(multa.agendamento, agendamento)
        self.assertFalse(multa.pago)

    def test_confirmado_depois_do_inicio_cria_multa(self):
        """CONFIRMADO já iniciado (30 min atrás): multa de R$ 25,00"""
        agendamento = self._novo(-30)
        response = self._cancelar(agendamento)
        self._assert_cancelado_com(response, agendamento, 1)
        self.assertEqual(Multa.objects.get().valor, Decimal('25.00'))

    def test_sala_sem_valor_de_multa_cancela_sem_multa(self):
        """Sala com multa 0,00: CONFIRMADO fora do prazo cancela sem multa"""
        self.sala.valor_multa_cancelamento = Decimal('0.00')
        self.sala.save()

        agendamento = self._novo(30)
        response = self._cancelar(agendamento)
        self._assert_cancelado_com(response, agendamento, 0)

    def test_cancelamento_nao_mexe_nos_outros_campos(self):
        """Só o status muda: data, horário, valor e pago ficam iguais"""
        agendamento = self._novo(59, pago=True, observacoes='Original.')
        antes = (
            agendamento.data, agendamento.hora_inicio, agendamento.hora_fim,
            agendamento.valor_cobrado, agendamento.pago,
            agendamento.observacoes,
        )
        self._cancelar(agendamento)

        agendamento.refresh_from_db()
        depois = (
            agendamento.data, agendamento.hora_inicio, agendamento.hora_fim,
            agendamento.valor_cobrado, agendamento.pago,
            agendamento.observacoes,
        )
        self.assertEqual(antes, depois)


# ===============================================================
# IDEMPOTÊNCIA, ATOMICIDADE, MOTIVO E MENSAGEM
# ===============================================================

class CancelamentoRobustezTest(CancelamentoBase):
    """
    Cancelar duas vezes, falha na multa, motivo longo e mensagem.
    """

    def test_cancelar_duas_vezes_pela_tela_cria_uma_unica_multa(self):
        """Segundo POST (duplo clique) é bloqueado e não cria outra multa"""
        agendamento = self._novo(30)
        self._cancelar(agendamento)
        segunda = self._cancelar(agendamento)

        self.assertRedirects(
            segunda, self._url_detalhe(agendamento),
            fetch_redirect_response=False,
        )
        self.assertEqual(Multa.objects.count(), 1)

    def test_cancelar_com_copia_velha_em_memoria_cria_uma_unica_multa(self):
        """
        Duas abas ao mesmo tempo: as duas instâncias foram lidas como
        CONFIRMADO. A segunda precisa reler o banco (com lock) e parar.
        """
        copia_a = Agendamento.objects.get(pk=self._novo(30).pk)
        copia_b = Agendamento.objects.get(pk=copia_a.pk)
        self.assertEqual(copia_b.status, 'CONFIRMADO')

        with mock.patch(NOW, return_value=self.agora):
            sucesso_a, _, multa_a = copia_a.cancelar(usuario=self.user_terapeuta)
            sucesso_b, _, multa_b = copia_b.cancelar(usuario=self.user_terapeuta)

        self.assertTrue(sucesso_a)
        self.assertEqual(multa_a, Decimal('25.00'))
        self.assertFalse(sucesso_b)
        self.assertEqual(multa_b, Decimal('0.00'))
        self.assertEqual(Multa.objects.count(), 1)

    def test_falha_ao_criar_a_multa_nao_cancela(self):
        """Se a multa falhar, o status volta a ser o que era (atômico)"""
        agendamento = self._novo(30)

        with mock.patch(NOW, return_value=self.agora):
            with mock.patch(
                'agendamentos.models.Multa.objects.create',
                side_effect=RuntimeError('falha simulada'),
            ):
                with self.assertRaises(RuntimeError):
                    agendamento.cancelar(usuario=self.user_terapeuta)

        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, 'CONFIRMADO')
        self.assertEqual(Multa.objects.count(), 0)

    def test_motivo_longo_pela_tela_e_truncado_sem_erro(self):
        """POST com 500 caracteres de motivo cancela sem erro"""
        agendamento = self._novo(30)
        response = self._cancelar(agendamento, motivo='x' * 500)

        self._assert_cancelado_com(response, agendamento, 1)
        # O texto composto nunca passa do limite do campo (255)
        self.assertLessEqual(len(Multa.objects.get().motivo), 255)

    def test_motivo_gigante_no_model_e_cortado_em_255(self):
        """cancelar() com motivo de 1000 caracteres: motivo da multa = 255"""
        agendamento = self._novo(30)
        with mock.patch(NOW, return_value=self.agora):
            agendamento.cancelar(usuario=self.user_terapeuta, motivo='y' * 1000)
        self.assertEqual(len(Multa.objects.get().motivo), 255)

    def test_motivo_informado_aparece_na_multa(self):
        """O motivo digitado entra no texto da multa"""
        agendamento = self._novo(30)
        self._cancelar(agendamento, motivo='Imprevisto de saúde')
        self.assertIn('Imprevisto de saúde', Multa.objects.get().motivo)

    def test_mensagem_usa_o_prazo_real_da_sala(self):
        """Com prazo de 90 min a mensagem fala 90 minutos, não 1 hora"""
        self.sala.prazo_cancelamento_sem_multa = 90
        self.sala.save()

        agendamento = self._novo(80)
        with mock.patch(NOW, return_value=self.agora):
            sucesso, mensagem, valor = agendamento.cancelar(
                usuario=self.user_terapeuta
            )

        self.assertTrue(sucesso)
        self.assertEqual(valor, Decimal('25.00'))
        self.assertIn('90 minutos', mensagem)
        self.assertIn('25,00', mensagem)
        self.assertNotIn('1 hora', mensagem)

    def test_previsao_multa_e_a_fonte_unica_da_regra(self):
        """previsao_multa() devolve o mesmo que cancelar() vai aplicar"""
        with mock.patch(NOW, return_value=self.agora):
            confirmado_tarde = self._novo(30).previsao_multa()
            confirmado_cedo = self._novo(180).previsao_multa()
            pendente_tarde = self._novo(30, status='PENDENTE').previsao_multa()

        self.assertTrue(confirmado_tarde['havera_multa'])
        self.assertEqual(confirmado_tarde['valor'], Decimal('25.00'))
        self.assertEqual(confirmado_tarde['prazo'], 60)
        self.assertFalse(confirmado_cedo['havera_multa'])
        self.assertEqual(confirmado_cedo['valor'], Decimal('0.00'))
        self.assertFalse(pendente_tarde['havera_multa'])
        self.assertEqual(pendente_tarde['valor'], Decimal('0.00'))


# ===============================================================
# STATUS BLOQUEADOS E ACESSO
# ===============================================================

class CancelamentoBloqueioEAcessoTest(CancelamentoBase):
    """
    CONCLUIDO e CANCELADO bloqueados; só o dono cancela; GET não cancela.
    """

    def test_concluido_e_bloqueado(self):
        """CONCLUIDO vai para o detalhe, nada muda, sem multa"""
        agendamento = self._novo(30, status='CONCLUIDO')
        response = self._cancelar(agendamento)

        self.assertRedirects(
            response, self._url_detalhe(agendamento),
            fetch_redirect_response=False,
        )
        self.assertTrue(self._mensagens(response))
        self._assert_nada_mudou(agendamento, 'CONCLUIDO')

    def test_cancelado_e_bloqueado_e_nao_cria_outra_multa(self):
        """CANCELADO vai para o detalhe, nada muda, sem multa nova"""
        agendamento = self._novo(30, status='CANCELADO')
        response = self._cancelar(agendamento)

        self.assertRedirects(
            response, self._url_detalhe(agendamento),
            fetch_redirect_response=False,
        )
        self.assertTrue(self._mensagens(response))
        self._assert_nada_mudou(agendamento, 'CANCELADO')

    def test_agendamento_de_outro_terapeuta_da_404(self):
        """POST de outro terapeuta: 404, nada muda"""
        agendamento = self._novo(30)
        outro_user = User.objects.create_user(
            username='outro_cancelamento', password='senha123'
        )
        self._criar_terapeuta(outro_user, 'outro-cancel')
        self.client.login(username='outro_cancelamento', password='senha123')

        response = self._cancelar(agendamento)
        self.assertEqual(response.status_code, 404)
        self._assert_nada_mudou(agendamento, 'CONFIRMADO')

    def test_anonimo_vai_para_o_login_e_nao_cancela(self):
        """POST sem login redireciona para o login"""
        agendamento = self._novo(30)
        self.client.logout()

        response = self._cancelar(agendamento)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))
        self._assert_nada_mudou(agendamento, 'CONFIRMADO')

    def test_usuario_sem_perfil_vai_para_a_home_e_nao_cancela(self):
        """POST sem perfil de terapeuta redireciona para a home"""
        agendamento = self._novo(30)
        User.objects.create_user(username='sem_perfil_cancel', password='senha123')
        self.client.login(username='sem_perfil_cancel', password='senha123')

        response = self._cancelar(agendamento)
        self.assertRedirects(
            response, reverse('core:home'), fetch_redirect_response=False
        )
        self._assert_nada_mudou(agendamento, 'CONFIRMADO')

    def test_get_nao_cancela(self):
        """GET na URL de cancelar devolve 405 e não cancela"""
        agendamento = self._novo(30)
        response = self.client.get(self._url_cancelar(agendamento))
        self.assertEqual(response.status_code, 405)
        self._assert_nada_mudou(agendamento, 'CONFIRMADO')


# ===============================================================
# AVISO NO DETALHE E NA LISTA
# ===============================================================

class CancelamentoAvisoTest(CancelamentoBase):
    """
    O aviso antes de cancelar diz se haverá multa e o valor, e o
    botão Cancelar da lista só existe para PENDENTE e CONFIRMADO.
    """

    def _get(self, url):
        """GET com o "agora" fixo, para o aviso bater com a regra"""
        with mock.patch(NOW, return_value=self.agora):
            return self.client.get(url)

    def test_detalhe_confirmado_fora_do_prazo_avisa_a_multa(self):
        """Detalhe de CONFIRMADO a 30 min mostra a multa de R$ 25,00"""
        agendamento = self._novo(30)
        response = self._get(self._url_detalhe(agendamento))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'multa de R$ 25,00')

    def test_detalhe_confirmado_dentro_do_prazo_nao_avisa_multa(self):
        """Detalhe de CONFIRMADO a 3 horas não fala em multa de R$"""
        agendamento = self._novo(180)
        response = self._get(self._url_detalhe(agendamento))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'multa de R$')

    def test_detalhe_pendente_nunca_avisa_multa(self):
        """Detalhe de PENDENTE a 30 min não fala em multa de R$"""
        agendamento = self._novo(30, status='PENDENTE')
        response = self._get(self._url_detalhe(agendamento))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'multa de R$')

    def test_lista_avisa_a_multa_do_confirmado_fora_do_prazo(self):
        """A lista leva o aviso da multa de R$ 25,00 no botão"""
        self._novo(30)
        response = self._get(self.url_dashboard)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'multa de R$ 25,00')

    def test_lista_so_mostra_cancelar_para_pendente_e_confirmado(self):
        """Botão Cancelar (data-id) só para PENDENTE e CONFIRMADO"""
        pendente = self._novo(180, status='PENDENTE')
        confirmado = self._novo(240, status='CONFIRMADO')
        concluido = self._novo(300, status='CONCLUIDO')
        cancelado = self._novo(360, status='CANCELADO')

        response = self._get(self.url_dashboard)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, f'data-id="{pendente.pk}"')
        self.assertContains(response, f'data-id="{confirmado.pk}"')
        self.assertNotContains(response, f'data-id="{concluido.pk}"')
        self.assertNotContains(response, f'data-id="{cancelado.pk}"')

    def test_lista_tem_campo_de_motivo_limitado_a_200(self):
        """O modal da lista tem o campo motivo com maxlength 200"""
        self._novo(180)
        response = self._get(self.url_dashboard)
        self.assertContains(response, 'name="motivo"')
        self.assertContains(response, 'maxlength="200"')

    def test_detalhe_tem_campo_de_motivo_limitado_a_200(self):
        """O detalhe tem o campo motivo com maxlength 200"""
        agendamento = self._novo(180)
        response = self._get(self._url_detalhe(agendamento))
        self.assertContains(response, 'name="motivo"')
        self.assertContains(response, 'maxlength="200"')


# ===============================================================
# VIEW DE CANCELAR DO DASHBOARD DE TERAPEUTAS (TESTES MÍNIMOS)
# ===============================================================

class DashboardCancelarTerapeutasTest(CancelamentoBase):
    """
    A view do dashboard de terapeutas usa a mesma regra do model.
    Quando não cancela, volta para o detalhe do app agendamentos.
    """

    def _url(self, agendamento):
        """URL de cancelar do dashboard de terapeutas"""
        return reverse(
            'terapeutas:dashboard_agendamento_cancelar',
            kwargs={'pk': agendamento.pk},
        )

    def _post(self, agendamento, multa_prevista='auto', **dados):
        """
        POST com o "agora" fixo. Por padrão envia o valor que o aviso
        mostraria; passe None para omitir o campo multa_prevista.
        """
        with mock.patch(NOW, return_value=self.agora):
            if multa_prevista == 'auto':
                atual = Agendamento.objects.get(pk=agendamento.pk)
                multa_prevista = atual.previsao_multa()['valor']
            if multa_prevista is not None:
                dados['multa_prevista'] = str(multa_prevista)
            return self.client.post(self._url(agendamento), dados)

    def test_confirmado_fora_do_prazo_cancela_com_multa(self):
        """CONFIRMADO a 30 min: cancela e cria multa de R$ 25,00"""
        agendamento = self._novo(30)
        response = self._post(agendamento)
        self._assert_cancelado_com(response, agendamento, 1)
        self.assertEqual(Multa.objects.get().valor, Decimal('25.00'))

    def test_pendente_cancela_sem_multa(self):
        """PENDENTE a 30 min: cancela, sem multa"""
        agendamento = self._novo(30, status='PENDENTE')
        response = self._post(agendamento)
        self._assert_cancelado_com(response, agendamento, 0)

    def test_agendamento_de_outro_terapeuta_da_404(self):
        """Outro terapeuta não cancela: 404 e nada muda"""
        agendamento = self._novo(30)
        outro_user = User.objects.create_user(
            username='outro_dash_cancel', password='senha123'
        )
        self._criar_terapeuta(outro_user, 'outro-dash')
        self.client.login(username='outro_dash_cancel', password='senha123')

        response = self._post(agendamento)
        self.assertEqual(response.status_code, 404)
        self._assert_nada_mudou(agendamento, 'CONFIRMADO')

    def test_campo_multa_prevista_ausente_nao_cancela(self):
        """Sem multa_prevista no POST, não cancela"""
        agendamento = self._novo(30)
        response = self._post(agendamento, multa_prevista=None)
        self.assertEqual(response.status_code, 302)
        self._assert_nada_mudou(agendamento, 'CONFIRMADO')

    def test_valor_do_aviso_diferente_do_atual_nao_cancela(self):
        """Valor do aviso diferente do atual: não cancela"""
        agendamento = self._novo(30)
        response = self._post(agendamento, multa_prevista='0.00')
        self.assertEqual(response.status_code, 302)
        self._assert_nada_mudou(agendamento, 'CONFIRMADO')

    def test_aviso_desatualizado_volta_para_o_detalhe_do_app_agendamentos(self):
        """
        Sem cancelar, volta para o detalhe que existe (agendamentos), e
        não para a rota antiga do dashboard, que não tem template.
        """
        agendamento = self._novo(30)
        response = self._post(agendamento, multa_prevista='0.00')
        self.assertRedirects(
            response,
            reverse('agendamentos:agendamento_detail', kwargs={'pk': agendamento.pk}),
            fetch_redirect_response=False,
        )


# ===============================================================
# AVISO DESATUALIZADO: O VALOR MOSTRADO PRECISA CONFERIR
# ===============================================================

class CancelamentoAvisoDesatualizadoTest(CancelamentoBase):
    """
    O formulário envia o valor da multa que o usuário viu. Se não
    conferir com o valor atual (ou vier ausente/inválido), não cancela
    e manda para o detalhe, que mostra o aviso recalculado.
    """

    def _assert_nao_cancelou(self, response, agendamento, status='CONFIRMADO'):
        """Redirect para o detalhe, aviso na mensagem e nada mudou"""
        self.assertRedirects(
            response, self._url_detalhe(agendamento),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            any('desatualizado' in m for m in self._mensagens(response))
        )
        self._assert_nada_mudou(agendamento, status)

    def test_valor_igual_cancela(self):
        """Valor enviado igual ao atual (25.00): cancela com a multa"""
        agendamento = self._novo(30)
        response = self._cancelar(agendamento, multa_prevista='25.00')
        self._assert_cancelado_com(response, agendamento, 1)

    def test_valor_com_virgula_tambem_confere(self):
        """O valor na formatação brasileira (25,00) também confere"""
        agendamento = self._novo(30)
        response = self._cancelar(agendamento, multa_prevista='25,00')
        self._assert_cancelado_com(response, agendamento, 1)

    def test_valor_diferente_nao_cancela_e_avisa_o_novo_valor(self):
        """Tela mostrava sem multa (0.00), agora é 25,00: não cancela"""
        agendamento = self._novo(30)
        response = self._cancelar(agendamento, multa_prevista='0.00')

        self._assert_nao_cancelou(response, agendamento)
        self.assertTrue(
            any('25,00' in m for m in self._mensagens(response)),
            'A mensagem deve trazer o novo valor da multa',
        )

    def test_aviso_de_multa_que_nao_existe_mais_nao_cancela(self):
        """Tela mostrava multa de 25.00, agora é sem multa: não cancela"""
        agendamento = self._novo(180)
        response = self._cancelar(agendamento, multa_prevista='25.00')
        self._assert_nao_cancelou(response, agendamento)

    def test_pendente_com_multa_forjada_nao_cancela(self):
        """PENDENTE nunca paga multa: valor 25.00 enviado não confere"""
        agendamento = self._novo(30, status='PENDENTE')
        response = self._cancelar(agendamento, multa_prevista='25.00')
        self._assert_nao_cancelou(response, agendamento, status='PENDENTE')

    def test_campo_ausente_nao_cancela(self):
        """Sem multa_prevista no POST, não cancela"""
        agendamento = self._novo(30)
        response = self._cancelar(agendamento, multa_prevista=None)
        self._assert_nao_cancelou(response, agendamento)

    def test_campo_invalido_nao_cancela(self):
        """multa_prevista com texto inválido: não cancela"""
        agendamento = self._novo(30)
        response = self._cancelar(agendamento, multa_prevista='abc')
        self._assert_nao_cancelou(response, agendamento)

    def test_campo_vazio_nao_cancela(self):
        """multa_prevista vazio: não cancela"""
        agendamento = self._novo(30)
        response = self._cancelar(agendamento, multa_prevista='')
        self._assert_nao_cancelou(response, agendamento)

    def test_detalhe_tem_o_campo_hidden_com_o_valor_do_aviso(self):
        """O formulário do detalhe leva o valor mostrado no aviso"""
        agendamento = self._novo(30)
        with mock.patch(NOW, return_value=self.agora):
            response = self.client.get(self._url_detalhe(agendamento))
        self.assertContains(response, 'name="multa_prevista"')
        self.assertContains(response, 'value="25.00"')

    def test_lista_leva_o_valor_do_aviso_no_botao(self):
        """O botão Cancelar da lista leva data-multa com o valor do aviso"""
        self._novo(30)
        with mock.patch(NOW, return_value=self.agora):
            response = self.client.get(self.url_dashboard)
        self.assertContains(response, 'data-multa="25.00"')
        self.assertContains(response, 'name="multa_prevista"')


# ===============================================================
# TEXTO DA MULTA
# ===============================================================

class CancelamentoTextoDaMultaTest(CancelamentoBase):
    """
    O motivo gravado na multa explica a situação sem número negativo.
    """

    def test_antes_do_inicio_diz_quantos_minutos_faltavam(self):
        """A 30 min do início: 'Faltavam 30 minutos'"""
        agendamento = self._novo(30)
        self._cancelar(agendamento)
        motivo = Multa.objects.get().motivo
        self.assertIn('Faltavam 30 minutos', motivo)

    def test_depois_do_inicio_diz_que_ja_havia_comecado(self):
        """Já iniciado: 'já havia começado', sem minutos negativos"""
        agendamento = self._novo(-30)
        self._cancelar(agendamento)
        motivo = Multa.objects.get().motivo
        self.assertIn('já havia começado', motivo)
        self.assertNotIn('-30', motivo)
        self.assertNotIn('Faltavam', motivo)

