# ===============================================================
# Título: Testes de Edição Segura de Agendamento
# Descrição: Garante que a AgendamentoEditarView só edita agendamento
#            PENDENTE do próprio terapeuta, que só data, hora de início
#            e observações mudam (sala, espaço, terapeuta, status, pago
#            e valor nunca mudam pela tela), que hora_fim é recalculada
#            pela duração da sala e que valem as mesmas regras da
#            criação: passado, antecedência de 30 minutos, horário da
#            sala, meia-noite e conflito (sem conflitar consigo mesmo).
#            Cada regra que barra afirma status 200, os erros do
#            formulário e que NADA mudou no banco.
# Autor: Will
# Data: 13/10/2026
# ===============================================================

from datetime import datetime, time, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from agendamentos.models import Agendamento, Sala
from espacos.models import Espaco
from terapeutas.models import Terapeuta

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class EdicaoAgendamentoBase(TestCase):
    """
    Base compartilhada: terapeuta logado com um agendamento PENDENTE
    amanhã das 10:00 às 11:00, em uma sala aberta das 08:00 às 18:00
    (sessão de 60 min, R$ 90,00), com observações "Original.".
    """

    def setUp(self):
        """Cria os dados base antes de cada teste"""
        self.client = Client()

        # Referências de data no fuso do projeto
        self.hoje = timezone.localdate()
        self.amanha = self.hoje + timedelta(days=1)

        # Terapeuta logado nos testes
        self.user_terapeuta = User.objects.create_user(
            username='terapeuta_edicao', password='senha123'
        )
        self.terapeuta = self._criar_terapeuta(self.user_terapeuta, 'edicao')

        # Espaço com uma sala, funcionando das 08:00 às 18:00
        self.espaco, self.sala = self._criar_espaco_com_sala('principal')

        # Agendamento PENDENTE do terapeuta, amanhã das 10:00 às 11:00
        self.agendamento = Agendamento.objects.create(
            terapeuta=self.terapeuta,
            sala=self.sala,
            espaco=self.espaco,
            data=self.amanha,
            hora_inicio=time(10, 0),
            hora_fim=time(11, 0),
            valor_cobrado=Decimal('90.00'),
            observacoes='Original.',
            status='PENDENTE',
        )

        self.url = reverse(
            'agendamentos:agendamento_update',
            kwargs={'pk': self.agendamento.pk},
        )
        self.url_detalhe = reverse(
            'agendamentos:agendamento_detail',
            kwargs={'pk': self.agendamento.pk},
        )
        self.url_dashboard = reverse('terapeutas:dashboard_agendamentos')

        self.client.login(username='terapeuta_edicao', password='senha123')

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

    def _criar_espaco_com_sala(self, sufixo, fechamento='18:00:00', duracao=60):
        """Cria um espaço ativo com uma sala ativa"""
        dono = User.objects.create_user(
            username=f'dono_{sufixo}', password='senha123'
        )
        espaco = Espaco.objects.create(
            nome=f'Espaço {sufixo}',
            slug=f'espaco-{sufixo}',
            descricao_breve='Teste.',
            descricao_completa='<p>Teste.</p>',
            endereco='Rua Y, 1',
            cep='20000-000',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=dono,
            is_active=True,
        )
        sala = Sala.objects.create(
            espaco=espaco,
            nome=f'Sala {sufixo}',
            capacidade=4,
            valor_sessao=Decimal('90.00'),
            duracao_sessao=duracao,
            horario_abertura='08:00:00',
            horario_fechamento=fechamento,
            is_active=True,
        )
        return espaco, sala

    def _dados(self, **extra):
        """Dados de um POST válido: amanhã às 14:00, nova observação"""
        dados = {
            'data': self.amanha.isoformat(),
            'hora_inicio': '14:00',
            'observacoes': 'Nova observação.',
        }
        dados.update(extra)
        return dados

    # -----------------------------------------------------------
    # Utilitários de verificação
    # -----------------------------------------------------------

    def _mensagens(self, response):
        """Devolve os textos das mensagens da resposta"""
        return [str(m) for m in get_messages(response.wsgi_request)]

    def _erros_gerais(self, response):
        """Junta os erros gerais (non_field_errors) do formulário"""
        return ' '.join(response.context['form'].non_field_errors())

    def _assert_nada_mudou(self):
        """Confere que o agendamento continua exatamente como no setUp"""
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.data, self.amanha)
        self.assertEqual(self.agendamento.hora_inicio, time(10, 0))
        self.assertEqual(self.agendamento.hora_fim, time(11, 0))
        self.assertEqual(self.agendamento.observacoes, 'Original.')
        self.assertEqual(self.agendamento.valor_cobrado, Decimal('90.00'))
        self.assertEqual(self.agendamento.status, 'PENDENTE')
        self.assertFalse(self.agendamento.pago)
        self.assertEqual(self.agendamento.sala, self.sala)
        self.assertEqual(self.agendamento.espaco, self.espaco)
        self.assertEqual(self.agendamento.terapeuta, self.terapeuta)

    def _assert_barrado(self, response, trecho_erro):
        """
        Confere que a regra barrou: status 200, o erro esperado no
        formulário, o erro na tela e nada mudou no banco.
        """
        self.assertEqual(response.status_code, 200)
        self.assertIn(trecho_erro, self._erros_gerais(response))
        self.assertContains(response, trecho_erro)
        self._assert_nada_mudou()


# ===============================================================
# EDIÇÃO VÁLIDA E CAMPOS PROTEGIDOS
# ===============================================================

class EdicaoValidaTest(EdicaoAgendamentoBase):
    """
    O que muda e o que nunca muda na edição de um PENDENTE.
    """

    def test_post_valido_muda_data_hora_e_observacoes(self):
        """Muda data, início e observações; recalcula hora_fim"""
        nova_data = self.amanha + timedelta(days=1)
        response = self.client.post(self.url, self._dados(
            data=nova_data.isoformat(), hora_inicio='14:00'
        ))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.assertIn(
            '✅ Agendamento atualizado com sucesso!', self._mensagens(response)
        )

        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.data, nova_data)
        self.assertEqual(self.agendamento.hora_inicio, time(14, 0))
        self.assertEqual(self.agendamento.hora_fim, time(15, 0))
        self.assertEqual(self.agendamento.observacoes, 'Nova observação.')

        # O que não é editável pela tela continua igual
        self.assertEqual(self.agendamento.valor_cobrado, Decimal('90.00'))
        self.assertEqual(self.agendamento.status, 'PENDENTE')
        self.assertFalse(self.agendamento.pago)
        self.assertEqual(self.agendamento.sala, self.sala)
        self.assertEqual(self.agendamento.espaco, self.espaco)
        self.assertEqual(self.agendamento.terapeuta, self.terapeuta)

    def test_hora_fim_e_recalculada_pela_duracao_da_sala(self):
        """Com sessão de 90 min na sala, início 14:00 termina 15:30"""
        self.sala.duracao_sessao = 90
        self.sala.save()

        response = self.client.post(self.url, self._dados(hora_inicio='14:00'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.hora_fim, time(15, 30))

    def test_campos_forjados_no_post_sao_ignorados(self):
        """valor, status, pago, sala, espaço, terapeuta e hora_fim não valem"""
        outro_user = User.objects.create_user(
            username='outro_terapeuta_forjado', password='senha123'
        )
        outro = self._criar_terapeuta(outro_user, 'forjado')
        espaco_alheio, sala_alheia = self._criar_espaco_com_sala('alheio')

        response = self.client.post(self.url, self._dados(
            valor_cobrado='1.00',
            status='CONFIRMADO',
            pago='on',
            sala=sala_alheia.pk,
            espaco=espaco_alheio.pk,
            terapeuta=outro.pk,
            hora_fim='23:00',
        ))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )

        self.agendamento.refresh_from_db()
        # Só o que é editável mudou
        self.assertEqual(self.agendamento.hora_inicio, time(14, 0))
        self.assertEqual(self.agendamento.observacoes, 'Nova observação.')
        # O resto ficou como estava
        self.assertEqual(self.agendamento.hora_fim, time(15, 0))
        self.assertEqual(self.agendamento.valor_cobrado, Decimal('90.00'))
        self.assertEqual(self.agendamento.status, 'PENDENTE')
        self.assertFalse(self.agendamento.pago)
        self.assertEqual(self.agendamento.sala, self.sala)
        self.assertEqual(self.agendamento.espaco, self.espaco)
        self.assertEqual(self.agendamento.terapeuta, self.terapeuta)

    def test_editar_sem_mudar_o_horario_nao_conflita_consigo_mesmo(self):
        """Salvar o mesmo horário (10:00) só com nova observação é aceito"""
        response = self.client.post(self.url, self._dados(hora_inicio='10:00'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.hora_inicio, time(10, 0))
        self.assertEqual(self.agendamento.hora_fim, time(11, 0))
        self.assertEqual(self.agendamento.observacoes, 'Nova observação.')

    def test_get_nao_tem_campo_de_valor_nem_de_hora_fim(self):
        """A tela de edição não oferece input de preço nem de término"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="valor_cobrado"')
        self.assertNotContains(response, 'name="hora_fim"')
        # Sala, valor e duração aparecem só como texto
        self.assertContains(response, self.sala.nome)
        self.assertContains(response, '90')


# ===============================================================
# REGRAS DA CRIAÇÃO VALEM NA EDIÇÃO
# ===============================================================

class EdicaoRegrasDeHorarioTest(EdicaoAgendamentoBase):
    """
    Passado, antecedência, horário da sala, meia-noite e conflito.
    """

    def test_data_no_passado_e_rejeitada(self):
        """Mudar para ontem é barrado"""
        ontem = self.hoje - timedelta(days=1)
        response = self.client.post(
            self.url, self._dados(data=ontem.isoformat())
        )
        self._assert_barrado(response, 'não pode ser no passado')

    def test_menos_de_30_minutos_de_antecedencia_e_rejeitado(self):
        """Mudar o início para daqui a 25 minutos é barrado"""
        # Agora simulado: amanhã às 09:50 em Brasília (12:50 UTC)
        agora = datetime.combine(
            self.amanha, time(12, 50), tzinfo=dt_timezone.utc
        )
        # Muda o início de 10:00 para 10:15 (25 min depois de "agora")
        with mock.patch('agendamentos.forms.timezone.now', return_value=agora):
            response = self.client.post(
                self.url, self._dados(hora_inicio='10:15')
            )
        self._assert_barrado(response, '30 minutos de antecedência')

    def test_antes_da_abertura_da_sala_e_rejeitado(self):
        """Início às 07:00 com a sala abrindo às 08:00 é barrado"""
        response = self.client.post(self.url, self._dados(hora_inicio='07:00'))
        self._assert_barrado(response, 'só abre às 08:00')

    def test_no_horario_de_fechamento_e_rejeitado(self):
        """Início às 18:00 com a sala fechando às 18:00 é barrado"""
        response = self.client.post(self.url, self._dados(hora_inicio='18:00'))
        self._assert_barrado(response, 'fecha às 18:00')

    def test_sessao_que_termina_apos_o_fechamento_e_rejeitada(self):
        """Início 17:30 + 60 min termina 18:30: barrado"""
        response = self.client.post(self.url, self._dados(hora_inicio='17:30'))
        self._assert_barrado(response, 'após o horário de fechamento')

    def test_sessao_que_cruza_a_meia_noite_e_rejeitada(self):
        """Sala fecha 23:59: início 23:30 + 60 min vira 00:30, barrado"""
        self.sala.horario_fechamento = '23:59:00'
        self.sala.save()

        response = self.client.post(self.url, self._dados(hora_inicio='23:30'))
        self._assert_barrado(response, 'após o horário de fechamento')

    def test_horario_que_colide_com_outro_agendamento_e_rejeitado(self):
        """Mudar para 14:30 colide com outro agendamento das 14:00 às 15:00"""
        outro_user = User.objects.create_user(
            username='outro_terapeuta_conflito', password='senha123'
        )
        outro = self._criar_terapeuta(outro_user, 'conflito')
        Agendamento.objects.create(
            terapeuta=outro,
            sala=self.sala,
            espaco=self.espaco,
            data=self.amanha,
            hora_inicio=time(14, 0),
            hora_fim=time(15, 0),
            valor_cobrado=Decimal('90.00'),
            status='PENDENTE',
        )

        response = self.client.post(self.url, self._dados(hora_inicio='14:30'))
        self._assert_barrado(response, 'Conflito de horário')

    def test_horario_logo_apos_outro_agendamento_e_aceito(self):
        """Mudar para 15:00, quando o outro termina, não conflita"""
        outro_user = User.objects.create_user(
            username='outro_terapeuta_adjacente', password='senha123'
        )
        outro = self._criar_terapeuta(outro_user, 'adjacente')
        Agendamento.objects.create(
            terapeuta=outro,
            sala=self.sala,
            espaco=self.espaco,
            data=self.amanha,
            hora_inicio=time(14, 0),
            hora_fim=time(15, 0),
            valor_cobrado=Decimal('90.00'),
            status='PENDENTE',
        )

        response = self.client.post(self.url, self._dados(hora_inicio='15:00'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.hora_inicio, time(15, 0))
        self.assertEqual(self.agendamento.hora_fim, time(16, 0))


# ===============================================================
# STATUS: SÓ PENDENTE PODE SER EDITADO
# ===============================================================

class EdicaoStatusBloqueadoTest(EdicaoAgendamentoBase):
    """
    CONFIRMADO, CONCLUIDO e CANCELADO são bloqueados: redirect para
    o detalhe com mensagem de erro e nada gravado.
    """

    def _definir_status(self, status):
        """Muda o status direto no banco, sem passar pela tela"""
        Agendamento.objects.filter(pk=self.agendamento.pk).update(status=status)

    def _assert_bloqueado(self, response, status):
        """Redirect para o detalhe, com erro, e nada mudou além do status"""
        self.assertRedirects(
            response, self.url_detalhe, fetch_redirect_response=False
        )
        self.assertTrue(
            any('pendentes' in m for m in self._mensagens(response)),
            f'Sem mensagem de bloqueio para {status}',
        )
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, status)
        self.assertEqual(self.agendamento.hora_inicio, time(10, 0))
        self.assertEqual(self.agendamento.hora_fim, time(11, 0))
        self.assertEqual(self.agendamento.observacoes, 'Original.')
        self.assertEqual(self.agendamento.valor_cobrado, Decimal('90.00'))

    def _get_bloqueado(self, status):
        """GET no status informado vai para o detalhe com erro"""
        self._definir_status(status)
        response = self.client.get(self.url)
        self._assert_bloqueado(response, status)

    def _post_bloqueado(self, status):
        """POST no status informado vai para o detalhe e não grava"""
        self._definir_status(status)
        response = self.client.post(self.url, self._dados())
        self._assert_bloqueado(response, status)

    def test_get_confirmado_e_bloqueado(self):
        """GET em agendamento CONFIRMADO vai para o detalhe com erro"""
        self._get_bloqueado('CONFIRMADO')

    def test_get_concluido_e_bloqueado(self):
        """GET em agendamento CONCLUIDO vai para o detalhe com erro"""
        self._get_bloqueado('CONCLUIDO')

    def test_get_cancelado_e_bloqueado(self):
        """GET em agendamento CANCELADO vai para o detalhe com erro"""
        self._get_bloqueado('CANCELADO')

    def test_post_confirmado_e_bloqueado(self):
        """POST em agendamento CONFIRMADO vai para o detalhe e não grava"""
        self._post_bloqueado('CONFIRMADO')

    def test_post_concluido_e_bloqueado(self):
        """POST em agendamento CONCLUIDO vai para o detalhe e não grava"""
        self._post_bloqueado('CONCLUIDO')

    def test_post_cancelado_e_bloqueado(self):
        """POST em agendamento CANCELADO vai para o detalhe e não grava"""
        self._post_bloqueado('CANCELADO')


# ===============================================================
# ACESSO: OUTRO TERAPEUTA, ANÔNIMO E SEM PERFIL
# ===============================================================

class EdicaoAcessoTest(EdicaoAgendamentoBase):
    """
    Só o dono edita. Anônimo vai ao login e usuário sem perfil vai
    para a home. Em nenhum caso algo é gravado.
    """

    def test_agendamento_de_outro_terapeuta_da_404_no_get(self):
        """GET de outro terapeuta: 404"""
        outro_user = User.objects.create_user(
            username='outro_dono_get', password='senha123'
        )
        self._criar_terapeuta(outro_user, 'outro-get')
        self.client.login(username='outro_dono_get', password='senha123')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_agendamento_de_outro_terapeuta_da_404_no_post_e_nao_grava(self):
        """POST de outro terapeuta: 404 e nada gravado"""
        outro_user = User.objects.create_user(
            username='outro_dono_post', password='senha123'
        )
        self._criar_terapeuta(outro_user, 'outro-post')
        self.client.login(username='outro_dono_post', password='senha123')

        response = self.client.post(self.url, self._dados())
        self.assertEqual(response.status_code, 404)
        self._assert_nada_mudou()

    def test_anonimo_get_vai_para_o_login(self):
        """GET sem login redireciona para o login"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))

    def test_anonimo_post_vai_para_o_login_e_nao_grava(self):
        """POST sem login redireciona para o login e não grava"""
        self.client.logout()
        response = self.client.post(self.url, self._dados())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))
        self._assert_nada_mudou()

    def test_usuario_sem_perfil_get_vai_para_a_home(self):
        """GET sem perfil de terapeuta redireciona para a home"""
        User.objects.create_user(username='sem_perfil_get', password='senha123')
        self.client.login(username='sem_perfil_get', password='senha123')

        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse('core:home'), fetch_redirect_response=False
        )

    def test_usuario_sem_perfil_post_vai_para_a_home_e_nao_grava(self):
        """POST sem perfil de terapeuta redireciona e não grava"""
        User.objects.create_user(username='sem_perfil_post', password='senha123')
        self.client.login(username='sem_perfil_post', password='senha123')

        response = self.client.post(self.url, self._dados())
        self.assertRedirects(
            response, reverse('core:home'), fetch_redirect_response=False
        )
        self._assert_nada_mudou()


# ===============================================================
# SÓ OBSERVAÇÕES: HORÁRIO INALTERADO NÃO É REVALIDADO
# ===============================================================

class EdicaoSoObservacoesTest(EdicaoAgendamentoBase):
    """
    Se data e hora_inicio não mudaram, só as observações são salvas,
    mesmo dentro dos 30 minutos ou com a data já no passado. Mudar o
    horário continua passando por todas as regras.
    """

    def test_so_observacoes_dentro_dos_30_minutos_e_aceito(self):
        """Faltam 20 min para as 10:00: mudar só o texto é aceito"""
        # Agora simulado: amanhã às 09:40 em Brasília (12:40 UTC)
        agora = datetime.combine(
            self.amanha, time(12, 40), tzinfo=dt_timezone.utc
        )
        with mock.patch('agendamentos.forms.timezone.now', return_value=agora):
            response = self.client.post(self.url, self._dados(hora_inicio='10:00'))

        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.observacoes, 'Nova observação.')
        self.assertEqual(self.agendamento.hora_inicio, time(10, 0))
        self.assertEqual(self.agendamento.hora_fim, time(11, 0))

    def test_so_observacoes_com_data_no_passado_e_aceito(self):
        """Agendamento pendente que ficou no passado: texto pode mudar"""
        ontem = self.hoje - timedelta(days=1)
        Agendamento.objects.filter(pk=self.agendamento.pk).update(data=ontem)

        response = self.client.post(self.url, self._dados(
            data=ontem.isoformat(), hora_inicio='10:00'
        ))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.data, ontem)
        self.assertEqual(self.agendamento.observacoes, 'Nova observação.')
        self.assertEqual(self.agendamento.hora_inicio, time(10, 0))

    def test_mudar_a_hora_de_agendamento_no_passado_e_barrado(self):
        """Data no passado e hora diferente: a regra do passado vale"""
        ontem = self.hoje - timedelta(days=1)
        Agendamento.objects.filter(pk=self.agendamento.pk).update(data=ontem)

        response = self.client.post(self.url, self._dados(
            data=ontem.isoformat(), hora_inicio='11:00'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn('não pode ser no passado', self._erros_gerais(response))

        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.hora_inicio, time(10, 0))
        self.assertEqual(self.agendamento.hora_fim, time(11, 0))
        self.assertEqual(self.agendamento.observacoes, 'Original.')

    def test_horario_inalterado_nao_burla_mudanca_de_data(self):
        """Mesma hora mas outra data (ontem): a regra do passado vale"""
        ontem = self.hoje - timedelta(days=1)
        response = self.client.post(self.url, self._dados(
            data=ontem.isoformat(), hora_inicio='10:00'
        ))
        self._assert_barrado(response, 'não pode ser no passado')


# ===============================================================
# DETALHE E LISTA: BOTÃO EDITAR SÓ PARA PENDENTE
# ===============================================================

class EdicaoBotaoEditarTest(EdicaoAgendamentoBase):
    """
    O link Editar aparece no detalhe e na lista só para PENDENTE.
    O detalhe também não pode dar erro para usuário sem perfil.
    """

    def _definir_status(self, status):
        """Muda o status direto no banco, sem passar pela tela"""
        Agendamento.objects.filter(pk=self.agendamento.pk).update(status=status)

    def test_detalhe_pendente_mostra_editar(self):
        """Detalhe de PENDENTE tem o link para editar"""
        response = self.client.get(self.url_detalhe)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.url)

    def test_detalhe_confirmado_nao_mostra_editar(self):
        """Detalhe de CONFIRMADO não oferece o link para editar"""
        self._definir_status('CONFIRMADO')
        response = self.client.get(self.url_detalhe)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.url)

    def test_lista_pendente_mostra_editar(self):
        """Lista de agendamentos mostra Editar para PENDENTE"""
        response = self.client.get(self.url_dashboard)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.url)

    def test_lista_confirmado_nao_mostra_editar(self):
        """Lista de agendamentos não mostra Editar para CONFIRMADO"""
        self._definir_status('CONFIRMADO')
        response = self.client.get(self.url_dashboard)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.url)

    def test_detalhe_usuario_sem_perfil_vai_para_a_home(self):
        """Detalhe sem perfil de terapeuta redireciona, não dá erro 500"""
        User.objects.create_user(username='sem_perfil_detalhe', password='senha123')
        self.client.login(username='sem_perfil_detalhe', password='senha123')

        response = self.client.get(self.url_detalhe)
        self.assertRedirects(
            response, reverse('core:home'), fetch_redirect_response=False
        )
