# ===============================================================
# Título: Testes das Mensagens do Sistema
# Descrição: Garante que django.contrib.messages aparece nas telas
#            (base.html e dashboard), que o logout descarta
#            mensagens pendentes e que o form_invalid de
#            agendamento não duplica os erros por campo.
# Autor: Will
# Data: 2026-10-14
# ===============================================================

import re

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.cookie import CookieStorage
from django.http import HttpRequest, HttpResponse
from django.test import TestCase, Client
from django.urls import reverse

from espacos.models import Espaco
from terapeutas.models import Terapeuta

User = get_user_model()


# ---------------------------------------------------------------
# Base: cria terapeuta e dono de espaço e permite deixar mensagens
# pendentes no cookie do cliente, sem passar por uma view.
# ---------------------------------------------------------------
class MensagensTestBase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_terapeuta = User.objects.create_user(
            username='terapeuta_msg', email='terapeuta_msg@teste.com',
            password='senha123',
        )
        Terapeuta.objects.create(
            user=self.user_terapeuta,
            nome_completo='Terapeuta Mensagens',
            nome_exibicao='Terapeuta Msg',
            slug='terapeuta-mensagens',
            bio_curta='Bio.',
            bio_completa='<p>Bio.</p>',
            formacao='Formação',
            is_active=True,
        )
        self.user_espaco = User.objects.create_user(
            username='dono_msg', password='senha123'
        )
        Espaco.objects.create(
            nome='Espaço Mensagens', slug='espaco-mensagens',
            descricao_breve='Teste.', descricao_completa='<p>Teste.</p>',
            endereco='Rua Z, 1', cep='20000-000', bairro='Centro',
            tipo_espaco='clinica', responsavel=self.user_espaco,
            is_active=True,
        )

    def deixar_mensagem_pendente(self, nivel, texto):
        """Grava uma mensagem no cookie do cliente, como se uma view a tivesse criado"""
        request = HttpRequest()
        request.COOKIES = {}
        if 'messages' in self.client.cookies:
            request.COOKIES['messages'] = self.client.cookies['messages'].value
        storage = CookieStorage(request)
        storage.add(nivel, texto)
        resposta = HttpResponse()
        storage.update(resposta)
        self.client.cookies['messages'] = resposta.cookies['messages'].value


# ---------------------------------------------------------------
# (a) A mensagem aparece no HTML das telas com base.html e dashboard
# ---------------------------------------------------------------
class MensagemApareceNaTelaTest(MensagensTestBase):

    def test_mensagem_aparece_em_tela_com_base_html(self):
        """Tela pública (base.html): mensagem renderizada com role=status"""
        self.deixar_mensagem_pendente(messages.SUCCESS, 'Tudo certo na tela base')
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Tudo certo na tela base', count=1)
        self.assertContains(response, 'role="status"')

    def test_mensagem_de_erro_usa_role_alert_e_botao_fechar(self):
        """Erro usa role=alert, fica até fechar e tem botão acessível"""
        self.deixar_mensagem_pendente(messages.ERROR, 'Algo deu errado')
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'aria-label="Fechar mensagem"')
        # O script cita o nome do atributo; o que não pode existir é o atributo com valor
        self.assertNotContains(response, 'data-autoclose="5000"')

    def test_mensagem_aparece_no_dashboard_do_terapeuta_uma_vez(self):
        """Dashboard do terapeuta: mensagem aparece e não é duplicada"""
        self.client.login(username='terapeuta_msg', password='senha123')
        self.deixar_mensagem_pendente(messages.SUCCESS, 'Salvo no dashboard')
        response = self.client.get(reverse('terapeutas:dashboard'))
        self.assertContains(response, 'Salvo no dashboard', count=1)

    def test_mensagem_aparece_no_dashboard_do_espaco_uma_vez(self):
        """Dashboard do espaço: mensagem aparece e não é duplicada"""
        self.client.login(username='dono_msg', password='senha123')
        self.deixar_mensagem_pendente(messages.SUCCESS, 'Salvo no espaço')
        response = self.client.get(reverse('espacos:dashboard'))
        self.assertContains(response, 'Salvo no espaço', count=1)


# ---------------------------------------------------------------
# Regressão: comentário {# #} de várias linhas não é comentário no
# Django e vazava como texto na tela. Nenhum resquício de comentário
# ou de cabeçalho pode aparecer no HTML renderizado.
# ---------------------------------------------------------------
class MensagemSemVazamentoDeComentarioTest(MensagensTestBase):

    TEXTOS_PROIBIDOS = ['{#', '#}', '{% comment', 'Autor: Will']

    def _assert_sem_vazamento(self, response):
        # Só interessa o que aparece na tela: comentários HTML <!-- --> e
        # blocos <script> já têm cabeçalhos de autor e são invisíveis
        html = re.sub(
            r'<!--.*?-->|<script.*?</script>', '',
            response.content.decode(), flags=re.DOTALL,
        )
        for texto in self.TEXTOS_PROIBIDOS:
            self.assertNotIn(texto, html)

    def test_home_com_mensagem_nao_vaza_comentario(self):
        self.deixar_mensagem_pendente(messages.SUCCESS, 'Mensagem na home')
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Mensagem na home')
        self._assert_sem_vazamento(response)

    def test_login_com_mensagem_nao_vaza_comentario(self):
        self.deixar_mensagem_pendente(messages.SUCCESS, 'Mensagem no login')
        response = self.client.get(reverse('account_login'))
        self.assertContains(response, 'Mensagem no login')
        self._assert_sem_vazamento(response)


# ---------------------------------------------------------------
# (b) Logout descarta pendentes: o login mostra só "Você saiu do sistema"
# ---------------------------------------------------------------
class LogoutDescartaMensagensTest(MensagensTestBase):

    def test_login_mostra_so_a_mensagem_de_logout(self):
        self.client.login(username='terapeuta_msg', password='senha123')
        self.deixar_mensagem_pendente(messages.SUCCESS, 'Mensagem antiga A')
        self.deixar_mensagem_pendente(messages.WARNING, 'Mensagem antiga B')

        response = self.client.post(reverse('account_logout'), follow=True)

        self.assertContains(response, 'Você saiu do sistema', count=1)
        self.assertNotContains(response, 'Mensagem antiga A')
        self.assertNotContains(response, 'Mensagem antiga B')
        textos = [str(m) for m in response.context['messages']]
        self.assertEqual(textos, ['Você saiu do sistema'])


# ---------------------------------------------------------------
# (c) form_invalid de agendamento não gera mensagem duplicada
# ---------------------------------------------------------------
class FormInvalidAgendamentoSemDuplicataTest(MensagensTestBase):

    def test_post_invalido_nao_cria_mensagem_extra(self):
        self.client.login(username='terapeuta_msg', password='senha123')
        response = self.client.post(reverse('agendamentos:agendamento_create'), {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(list(response.context['messages']), [])
