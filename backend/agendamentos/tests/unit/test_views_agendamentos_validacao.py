# ===============================================================
# Título: Testes de Validação na Criação de Agendamento
# Descrição: Garante que a AgendamentoCriarView aplica as regras do
#            AgendamentoForm: data no passado, antecedência mínima
#            de 30 minutos, horário de funcionamento da sala,
#            conflito de horário, vínculo com o espaço, campos
#            forjados no POST, perfil de terapeuta e fuso horário.
#            Cada regra que barra afirma status 200, os erros do
#            formulário e que NADA foi gravado no banco.
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

from agendamentos.models import Agendamento, Sala, VinculoTerapeutaEspaco
from espacos.models import Espaco
from terapeutas.models import Terapeuta

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class CriarAgendamentoBase(TestCase):
    """
    Base compartilhada: terapeuta com vínculo APROVADO em um espaço
    que tem uma sala aberta das 08:00 às 18:00 (sessão de 60 min,
    R$ 90,00). Nenhum agendamento existe no início.
    """

    def setUp(self):
        """Cria os dados base antes de cada teste"""
        self.client = Client()
        self.url = reverse('agendamentos:agendamento_create')
        self.url_dashboard = reverse('terapeutas:dashboard_agendamentos')

        # Referências de data no fuso do projeto
        self.hoje = timezone.localdate()
        self.amanha = self.hoje + timedelta(days=1)

        # Terapeuta logado nos testes
        self.user_terapeuta = User.objects.create_user(
            username='terapeuta_valida', password='senha123'
        )
        self.terapeuta = self._criar_terapeuta(self.user_terapeuta, 'valida')

        # Espaço com uma sala, funcionando das 08:00 às 18:00
        self.espaco, self.sala = self._criar_espaco_com_sala('principal')

        # Vínculo aprovado e ativo entre o terapeuta e o espaço
        VinculoTerapeutaEspaco.objects.create(
            espaco=self.espaco,
            terapeuta=self.terapeuta,
            status='APROVADO',
            is_active=True,
        )

        self.client.login(username='terapeuta_valida', password='senha123')

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
        """Dados de um POST válido: amanhã às 10:00 na sala base"""
        dados = {
            'espaco': self.espaco.pk,
            'sala': self.sala.pk,
            'data': self.amanha.isoformat(),
            'hora_inicio': '10:00',
            'observacoes': 'Sessão de teste.',
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

    def _assert_barrado(self, response, total_antes, trecho_erro):
        """
        Confere que a regra barrou: status 200, o erro esperado no
        formulário e nenhum agendamento novo gravado.
        """
        self.assertEqual(response.status_code, 200)
        self.assertIn(trecho_erro, self._erros_gerais(response))
        # O erro também precisa aparecer na tela para o usuário
        self.assertContains(response, trecho_erro)
        self.assertEqual(Agendamento.objects.count(), total_antes)


# ===============================================================
# REGRAS DE DATA E HORÁRIO
# ===============================================================

class RegrasDeDataEHorarioTest(CriarAgendamentoBase):
    """
    Data no passado, antecedência mínima e horário de funcionamento.
    """

    def test_data_no_passado_e_rejeitada(self):
        """Agendar para ontem deve ser barrado"""
        ontem = self.hoje - timedelta(days=1)
        response = self.client.post(self.url, self._dados(data=ontem.isoformat()))
        self._assert_barrado(response, 0, 'não pode ser no passado')

    def test_menos_de_30_minutos_de_antecedencia_e_rejeitado(self):
        """Com 20 minutos de antecedência o agendamento é barrado"""
        # Agora simulado: amanhã às 09:40 em Brasília (12:40 UTC)
        agora = datetime.combine(
            self.amanha, time(12, 40), tzinfo=dt_timezone.utc
        )
        with mock.patch('agendamentos.forms.timezone.now', return_value=agora):
            response = self.client.post(
                self.url, self._dados(hora_inicio='10:00')
            )
        self._assert_barrado(response, 0, '30 minutos de antecedência')

    def test_antes_da_abertura_da_sala_e_rejeitado(self):
        """Início às 07:00 com a sala abrindo às 08:00 é barrado"""
        response = self.client.post(self.url, self._dados(hora_inicio='07:00'))
        self._assert_barrado(response, 0, 'só abre às 08:00')

    def test_no_horario_de_fechamento_e_rejeitado(self):
        """Início às 18:00 com a sala fechando às 18:00 é barrado"""
        response = self.client.post(self.url, self._dados(hora_inicio='18:00'))
        self._assert_barrado(response, 0, 'fecha às 18:00')

    def test_sessao_que_termina_apos_o_fechamento_e_rejeitada(self):
        """Início às 17:30 com sessão de 60 min termina às 18:30: barrado"""
        response = self.client.post(self.url, self._dados(hora_inicio='17:30'))
        self._assert_barrado(response, 0, 'após o horário de fechamento')


class SessaoQueCruzaAMeiaNoiteTest(CriarAgendamentoBase):
    """
    Sala que fecha tarde da noite: a sessão que termina depois da
    meia-noite não pode passar pela conferência de fechamento.
    """

    def setUp(self):
        super().setUp()
        # Sala noturna: abre às 08:00 e fecha às 23:59, sessão de 60 min
        self.espaco_noturno, self.sala_noturna = self._criar_espaco_com_sala(
            'noturno', fechamento='23:59:00', duracao=60
        )
        VinculoTerapeutaEspaco.objects.create(
            espaco=self.espaco_noturno,
            terapeuta=self.terapeuta,
            status='APROVADO',
            is_active=True,
        )

    def _dados_noturnos(self, hora_inicio):
        """POST na sala noturna, amanhã, no horário informado"""
        return self._dados(
            espaco=self.espaco_noturno.pk,
            sala=self.sala_noturna.pk,
            hora_inicio=hora_inicio,
        )

    def test_sessao_que_termina_apos_a_meia_noite_e_rejeitada(self):
        """Início 23:30 + 60 min vira 00:30 do dia seguinte: barrado"""
        response = self.client.post(self.url, self._dados_noturnos('23:30'))
        self._assert_barrado(response, 0, 'após o horário de fechamento')

    def test_sessao_que_termina_exatamente_a_meia_noite_e_rejeitada(self):
        """Início 23:00 + 60 min termina 00:00 do dia seguinte: barrado"""
        response = self.client.post(self.url, self._dados_noturnos('23:00'))
        self._assert_barrado(response, 0, 'após o horário de fechamento')

    def test_sessao_que_termina_exatamente_no_fechamento_e_aceita(self):
        """Início 22:59 + 60 min termina às 23:59, no fechamento: aceito"""
        response = self.client.post(self.url, self._dados_noturnos('22:59'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        agendamento = Agendamento.objects.get()
        self.assertEqual(agendamento.hora_inicio, time(22, 59))
        self.assertEqual(agendamento.hora_fim, time(23, 59))

    def test_sessao_que_termina_antes_do_fechamento_e_aceita(self):
        """Início 22:30 + 60 min termina às 23:30, antes das 23:59: aceito"""
        response = self.client.post(self.url, self._dados_noturnos('22:30'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        agendamento = Agendamento.objects.get()
        self.assertEqual(agendamento.hora_inicio, time(22, 30))
        self.assertEqual(agendamento.hora_fim, time(23, 30))


# ===============================================================
# SALA QUE FECHA À MEIA-NOITE (00:00)
# ===============================================================

class SalaQueFechaAMeiaNoiteTest(CriarAgendamentoBase):
    """
    Sala configurada com fechamento 00:00, que vale como o fim do dia.
    Antes da correção a sala nunca aceitava agendamento, porque 00:00
    era comparado como o começo do dia.
    """

    def setUp(self):
        super().setUp()
        # Sala que abre às 08:00 e fecha à meia-noite, sessão de 60 min
        self.espaco_meia_noite, self.sala_meia_noite = self._criar_espaco_com_sala(
            'meianoite', fechamento='00:00:00', duracao=60
        )
        VinculoTerapeutaEspaco.objects.create(
            espaco=self.espaco_meia_noite,
            terapeuta=self.terapeuta,
            status='APROVADO',
            is_active=True,
        )

    def _dados_meia_noite(self, hora_inicio):
        """POST na sala que fecha à meia-noite, amanhã, no horário informado"""
        return self._dados(
            espaco=self.espaco_meia_noite.pk,
            sala=self.sala_meia_noite.pk,
            hora_inicio=hora_inicio,
        )

    def test_horario_no_meio_do_dia_e_aceito(self):
        """10:00 às 11:00 numa sala que fecha 00:00 deve ser aceito"""
        response = self.client.post(self.url, self._dados_meia_noite('10:00'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_ultima_sessao_do_dia_termina_a_meia_noite_e_e_aceita(self):
        """Início 23:00 + 60 min termina 00:00 (fechamento): aceito"""
        response = self.client.post(self.url, self._dados_meia_noite('23:00'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        agendamento = Agendamento.objects.get()
        self.assertEqual(agendamento.hora_inicio, time(23, 0))
        self.assertEqual(agendamento.hora_fim, time(0, 0))

    def test_sessao_que_passa_da_meia_noite_e_rejeitada(self):
        """Início 23:30 + 60 min termina 00:30, depois do fechamento: barrado"""
        response = self.client.post(self.url, self._dados_meia_noite('23:30'))
        self._assert_barrado(response, 0, 'após o horário de fechamento')

    def test_conflito_com_sessao_que_termina_a_meia_noite(self):
        """
        Existente 23:00 às 00:00. Pedir 23:00 de novo precisa conflitar,
        mesmo com hora_fim 00:00 (que como time parece menor que o início).
        """
        outro_user = User.objects.create_user(
            username='outro_terapeuta_meianoite', password='senha123'
        )
        outro = self._criar_terapeuta(outro_user, 'meianoite')
        Agendamento.objects.create(
            terapeuta=outro,
            sala=self.sala_meia_noite,
            espaco=self.espaco_meia_noite,
            data=self.amanha,
            hora_inicio=time(23, 0),
            hora_fim=time(0, 0),
            valor_cobrado=Decimal('90.00'),
            status='PENDENTE',
        )
        response = self.client.post(self.url, self._dados_meia_noite('23:00'))
        self._assert_barrado(response, 1, 'Conflito de horário')

    def test_sessao_logo_antes_da_que_termina_a_meia_noite_e_aceita(self):
        """Existente 23:00 às 00:00. Pedir 22:00 às 23:00 não conflita"""
        outro_user = User.objects.create_user(
            username='outro_terapeuta_antes', password='senha123'
        )
        outro = self._criar_terapeuta(outro_user, 'antes')
        Agendamento.objects.create(
            terapeuta=outro,
            sala=self.sala_meia_noite,
            espaco=self.espaco_meia_noite,
            data=self.amanha,
            hora_inicio=time(23, 0),
            hora_fim=time(0, 0),
            valor_cobrado=Decimal('90.00'),
            status='PENDENTE',
        )
        response = self.client.post(self.url, self._dados_meia_noite('22:00'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.assertEqual(Agendamento.objects.count(), 2)


# ===============================================================
# CONFLITO DE HORÁRIO
# ===============================================================

class ConflitoDeHorarioTest(CriarAgendamentoBase):
    """
    Sobreposição com outro agendamento na mesma sala e data.
    """

    def setUp(self):
        super().setUp()
        # Outro terapeuta já tem a sala amanhã das 10:00 às 11:00
        outro_user = User.objects.create_user(
            username='outro_terapeuta_conflito', password='senha123'
        )
        outro = self._criar_terapeuta(outro_user, 'conflito')
        self.existente = Agendamento.objects.create(
            terapeuta=outro,
            sala=self.sala,
            espaco=self.espaco,
            data=self.amanha,
            hora_inicio=time(10, 0),
            hora_fim=time(11, 0),
            valor_cobrado=Decimal('90.00'),
            status='PENDENTE',
        )

    def test_horario_sobreposto_e_rejeitado(self):
        """Início às 10:30 sobrepõe o agendamento das 10:00 às 11:00"""
        response = self.client.post(self.url, self._dados(hora_inicio='10:30'))
        self._assert_barrado(response, 1, 'Conflito de horário')

    def test_mesmo_horario_e_rejeitado(self):
        """Mesmo horário do agendamento existente é barrado"""
        response = self.client.post(self.url, self._dados(hora_inicio='10:00'))
        self._assert_barrado(response, 1, 'Conflito de horário')

    def test_horario_logo_apos_o_existente_e_aceito(self):
        """Início às 11:00, quando o outro termina, não conflita"""
        response = self.client.post(self.url, self._dados(hora_inicio='11:00'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.assertEqual(Agendamento.objects.count(), 2)


# ===============================================================
# VÍNCULO COM O ESPAÇO
# ===============================================================

class VinculoComOEspacoTest(CriarAgendamentoBase):
    """
    O terapeuta só agenda em espaço com vínculo APROVADO e ativo.
    """

    def _espaco_sem_vinculo_valido(self, sufixo, **dados_vinculo):
        """Cria outro espaço, com vínculo conforme os dados recebidos"""
        espaco, sala = self._criar_espaco_com_sala(sufixo)
        if dados_vinculo:
            VinculoTerapeutaEspaco.objects.create(
                espaco=espaco, terapeuta=self.terapeuta, **dados_vinculo
            )
        return espaco, sala

    def _postar_em(self, espaco, sala):
        """POST válido para o espaço e a sala informados"""
        return self.client.post(
            self.url, self._dados(espaco=espaco.pk, sala=sala.pk)
        )

    def test_espaco_sem_vinculo_e_rejeitado(self):
        """Sem nenhum vínculo com o espaço, o agendamento é barrado"""
        espaco, sala = self._espaco_sem_vinculo_valido('sem-vinculo')
        response = self._postar_em(espaco, sala)
        self.assertEqual(response.status_code, 200)
        self.assertIn('espaco', response.context['form'].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_vinculo_pendente_e_rejeitado(self):
        """Vínculo ainda PENDENTE não permite agendar"""
        espaco, sala = self._espaco_sem_vinculo_valido(
            'pendente', status='PENDENTE', is_active=True
        )
        response = self._postar_em(espaco, sala)
        self.assertEqual(response.status_code, 200)
        self.assertIn('espaco', response.context['form'].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_vinculo_inativo_e_rejeitado(self):
        """Vínculo APROVADO porém inativo não permite agendar"""
        espaco, sala = self._espaco_sem_vinculo_valido(
            'inativo', status='APROVADO', is_active=False
        )
        response = self._postar_em(espaco, sala)
        self.assertEqual(response.status_code, 200)
        self.assertIn('espaco', response.context['form'].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_sala_de_outro_espaco_e_rejeitada(self):
        """Espaço vinculado com sala de outro espaço é barrado"""
        _, sala_alheia = self._criar_espaco_com_sala('alheio')
        response = self.client.post(
            self.url, self._dados(sala=sala_alheia.pk)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('sala', response.context['form'].errors)
        self.assertEqual(Agendamento.objects.count(), 0)


class TerapeutaSemNenhumEspacoTest(CriarAgendamentoBase):
    """
    Terapeuta que ainda não tem vínculo com nenhum espaço.
    """

    def setUp(self):
        super().setUp()
        # Remove o vínculo criado na base: o terapeuta fica sem espaço
        VinculoTerapeutaEspaco.objects.all().delete()

    def test_tela_mostra_mensagem_clara(self):
        """GET mostra aviso de que não há espaço vinculado"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'não está vinculado a nenhum espaço')

    def test_post_valido_nao_grava_nada(self):
        """POST com dados completos, mas sem vínculo, não grava"""
        response = self.client.post(self.url, self._dados())
        self.assertEqual(response.status_code, 200)
        self.assertIn('espaco', response.context['form'].errors)
        self.assertEqual(Agendamento.objects.count(), 0)


# ===============================================================
# CRIAÇÃO VÁLIDA E CAMPOS FORJADOS
# ===============================================================

class CriacaoValidaTest(CriarAgendamentoBase):
    """
    Criação válida e proteção contra campos forjados no POST.
    """

    def test_criacao_valida_grava_com_dados_calculados(self):
        """POST válido grava terapeuta, sala, status, hora_fim e valor"""
        response = self.client.post(self.url, self._dados(hora_inicio='10:00'))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        self.assertEqual(Agendamento.objects.count(), 1)

        agendamento = Agendamento.objects.get()
        self.assertEqual(agendamento.terapeuta, self.terapeuta)
        self.assertEqual(agendamento.sala, self.sala)
        self.assertEqual(agendamento.espaco, self.espaco)
        self.assertEqual(agendamento.data, self.amanha)
        self.assertEqual(agendamento.hora_inicio, time(10, 0))
        # Calculados pelo formulário a partir da sala
        self.assertEqual(agendamento.hora_fim, time(11, 0))
        self.assertEqual(agendamento.valor_cobrado, Decimal('90.00'))
        self.assertEqual(agendamento.status, 'PENDENTE')
        self.assertFalse(agendamento.pago)

    def test_campos_forjados_no_post_sao_ignorados(self):
        """status, pago, valor, hora_fim e terapeuta forjados não valem"""
        outro_user = User.objects.create_user(
            username='outro_terapeuta_forjado', password='senha123'
        )
        outro = self._criar_terapeuta(outro_user, 'forjado')

        response = self.client.post(self.url, self._dados(
            status='CONFIRMADO',
            pago='on',
            valor_cobrado='0.00',
            hora_fim='23:00',
            terapeuta=outro.pk,
        ))
        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )

        agendamento = Agendamento.objects.get()
        self.assertEqual(agendamento.terapeuta, self.terapeuta)
        self.assertEqual(agendamento.status, 'PENDENTE')
        self.assertFalse(agendamento.pago)
        self.assertEqual(agendamento.valor_cobrado, Decimal('90.00'))
        self.assertEqual(agendamento.hora_fim, time(11, 0))


# ===============================================================
# ACESSO: ANÔNIMO E USUÁRIO SEM PERFIL DE TERAPEUTA
# ===============================================================

class AcessoTest(TestCase):
    """
    Anônimo vai para o login; usuário sem perfil vai para a home.
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse('agendamentos:agendamento_create')

    def test_anonimo_get_vai_para_o_login(self):
        """GET sem login redireciona para o login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))

    def test_anonimo_post_vai_para_o_login_e_nao_grava(self):
        """POST sem login redireciona para o login e não grava"""
        response = self.client.post(self.url, {'sala': 1})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_usuario_sem_perfil_get_vai_para_a_home_com_erro(self):
        """GET sem perfil de terapeuta redireciona para a home"""
        User.objects.create_user(username='sem_perfil', password='senha123')
        self.client.login(username='sem_perfil', password='senha123')
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse('core:home'), fetch_redirect_response=False
        )
        mensagens = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('perfil de terapeuta' in m for m in mensagens))

    def test_usuario_sem_perfil_post_vai_para_a_home_e_nao_grava(self):
        """POST sem perfil de terapeuta redireciona e não grava"""
        User.objects.create_user(username='sem_perfil', password='senha123')
        self.client.login(username='sem_perfil', password='senha123')
        response = self.client.post(self.url, {})
        self.assertRedirects(
            response, reverse('core:home'), fetch_redirect_response=False
        )
        self.assertEqual(Agendamento.objects.count(), 0)


# ===============================================================
# DATA E FUSO HORÁRIO
# ===============================================================

class FusoHorarioTest(CriarAgendamentoBase):
    """
    Às 22h em Brasília já é o dia seguinte em UTC. O "hoje" do
    agendamento deve ser o dia local, não o dia UTC.
    """

    def test_dia_local_de_hoje_e_aceito_a_noite(self):
        """Às 22h locais, agendar hoje às 22:40 deve ser aceito"""
        # Sala que funciona à noite, com sessões de 30 minutos
        espaco, sala = self._criar_espaco_com_sala(
            'noturno', fechamento='23:59:00', duracao=30
        )
        VinculoTerapeutaEspaco.objects.create(
            espaco=espaco, terapeuta=self.terapeuta,
            status='APROVADO', is_active=True,
        )

        # Agora simulado: 01:00 UTC do dia seguinte (22:00 em Brasília)
        agora = datetime.combine(
            self.hoje + timedelta(days=1), time(1, 0), tzinfo=dt_timezone.utc
        )
        dados = self._dados(
            espaco=espaco.pk,
            sala=sala.pk,
            data=self.hoje.isoformat(),
            hora_inicio='22:40',
        )
        with mock.patch('agendamentos.forms.timezone.now', return_value=agora):
            response = self.client.post(self.url, dados)

        self.assertRedirects(
            response, self.url_dashboard, fetch_redirect_response=False
        )
        agendamento = Agendamento.objects.get()
        self.assertEqual(agendamento.data, self.hoje)
        self.assertEqual(agendamento.hora_inicio, time(22, 40))
        self.assertEqual(agendamento.hora_fim, time(23, 10))
