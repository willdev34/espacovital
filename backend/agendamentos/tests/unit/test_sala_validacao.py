# ===============================================================
# Título: Testes de Validação do Model Sala
# Descrição: Garante as regras de horário e duração da Sala:
#            duração mínima de 1 minuto, fechamento depois da
#            abertura (00:00 vale como meia-noite do fim do dia)
#            e duração que cabe no funcionamento da sala.
# Autor: Will
# Data: 15/10/2026
# ===============================================================

from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from agendamentos.models import Sala
from espacos.models import Espaco

User = get_user_model()


# ---------------------------------------------------------------
# Base: cria um espaço e monta salas (sem salvar) para validar
# ---------------------------------------------------------------
class SalaValidacaoBase(TestCase):

    def setUp(self):
        dono = User.objects.create_user(username='dono_sala', password='senha123')
        self.espaco = Espaco.objects.create(
            nome='Espaço Sala',
            slug='espaco-sala',
            descricao_breve='Teste.',
            descricao_completa='<p>Teste.</p>',
            endereco='Rua Z, 1',
            cep='20000-000',
            bairro='Centro',
            tipo_espaco='clinica',
            responsavel=dono,
            is_active=True,
        )

    def _sala(self, abertura=time(8, 0), fechamento=time(18, 0), duracao=60):
        """Monta uma Sala em memória, sem gravar no banco"""
        return Sala(
            espaco=self.espaco,
            nome='Sala teste',
            capacidade=4,
            valor_sessao=Decimal('90.00'),
            duracao_sessao=duracao,
            horario_abertura=abertura,
            horario_fechamento=fechamento,
        )


# ---------------------------------------------------------------
# Horário de fechamento em minutos
# ---------------------------------------------------------------
class FechamentoEmMinutosTest(SalaValidacaoBase):

    def test_fechamento_comum_em_minutos(self):
        """18:00 vale 1080 minutos desde o começo do dia"""
        self.assertEqual(self._sala(fechamento=time(18, 0)).fechamento_em_minutos, 1080)

    def test_fechamento_a_meia_noite_vale_fim_do_dia(self):
        """00:00 vale 1440 (24:00), não 0"""
        self.assertEqual(self._sala(fechamento=time(0, 0)).fechamento_em_minutos, 1440)

    def test_abertura_em_minutos(self):
        """08:30 vale 510 minutos"""
        self.assertEqual(self._sala(abertura=time(8, 30)).abertura_em_minutos, 510)


# ---------------------------------------------------------------
# Sala.clean(): horários de abertura e fechamento
# ---------------------------------------------------------------
class SalaCleanHorariosTest(SalaValidacaoBase):

    def test_sala_valida_passa(self):
        self._sala().full_clean(exclude=['espaco'])

    def test_fechamento_a_meia_noite_e_valido(self):
        """08:00 às 00:00 é uma sala aberta até o fim do dia"""
        self._sala(fechamento=time(0, 0)).full_clean(exclude=['espaco'])

    def test_sala_24_horas_e_valida(self):
        """Abertura e fechamento às 00:00 formam um dia inteiro"""
        self._sala(abertura=time(0, 0), fechamento=time(0, 0), duracao=60).full_clean(
            exclude=['espaco']
        )

    def test_fechamento_antes_da_abertura_e_rejeitado(self):
        sala = self._sala(abertura=time(18, 0), fechamento=time(8, 0))
        with self.assertRaises(ValidationError) as ctx:
            sala.full_clean(exclude=['espaco'])
        self.assertIn('horario_fechamento', ctx.exception.message_dict)

    def test_fechamento_igual_a_abertura_e_rejeitado(self):
        sala = self._sala(abertura=time(8, 0), fechamento=time(8, 0))
        with self.assertRaises(ValidationError) as ctx:
            sala.full_clean(exclude=['espaco'])
        self.assertIn('horario_fechamento', ctx.exception.message_dict)


# ---------------------------------------------------------------
# Duração da sessão: mínimo de 1 minuto e cabe no funcionamento
# ---------------------------------------------------------------
class SalaCleanDuracaoTest(SalaValidacaoBase):

    def test_duracao_zero_e_rejeitada(self):
        with self.assertRaises(ValidationError) as ctx:
            self._sala(duracao=0).full_clean(exclude=['espaco'])
        self.assertIn('duracao_sessao', ctx.exception.message_dict)

    def test_duracao_de_um_minuto_e_aceita(self):
        self._sala(duracao=1).full_clean(exclude=['espaco'])

    def test_duracao_maior_que_o_funcionamento_e_rejeitada(self):
        """Sala aberta 1 hora com sessão de 90 min nunca teria horário"""
        sala = self._sala(abertura=time(8, 0), fechamento=time(9, 0), duracao=90)
        with self.assertRaises(ValidationError) as ctx:
            sala.full_clean(exclude=['espaco'])
        self.assertIn('duracao_sessao', ctx.exception.message_dict)

    def test_duracao_igual_ao_funcionamento_e_aceita(self):
        """Sessão de 60 min numa sala aberta exatamente 60 min"""
        self._sala(abertura=time(8, 0), fechamento=time(9, 0), duracao=60).full_clean(
            exclude=['espaco']
        )

    def test_duracao_considera_fechamento_a_meia_noite(self):
        """Sala 23:00 às 00:00 comporta uma sessão de 60 min"""
        self._sala(abertura=time(23, 0), fechamento=time(0, 0), duracao=60).full_clean(
            exclude=['espaco']
        )
