# ===============================================================
# Título: Testes dos Fluxos do Dashboard do Espaço
# Descrição: Cobre o painel principal (planos e completude), a edição
#            do perfil, a assinatura, as salas (duplicidade, permissões
#            e ativação) e os convites de terapeutas (cadastrado, novo
#            por e-mail, repetido e falha no envio).
# Autor: Will
# Data: 2026-10-15
# ===============================================================

from datetime import date
from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from agendamentos.models import ConviteExterno, Sala, VinculoTerapeutaEspaco
from core.models import (
    Assinatura, Cidade, Especialidade, Estado, Plano,
)
from espacos.models import AvaliacaoEspaco, Comodidade, ContatoEspaco, Espaco
from terapeutas.models import Terapeuta

pytestmark = pytest.mark.django_db

User = get_user_model()


# ---------------------------------------------------------------
# Gestor com espaço e plano que libera o gerenciamento de salas
# ---------------------------------------------------------------
@pytest.fixture
def gestor(client):
    usuario = User.objects.create_user(
        username='gestor_fluxo', email='gestor@fluxo.com', password='senha123'
    )
    espaco = Espaco.objects.create(
        nome='Espaço Fluxo', slug='espaco-fluxo', descricao_breve='Breve',
        descricao_completa='<p>Completa</p>', endereco='Rua B, 2',
        cep='20040-020', bairro='Centro', tipo_espaco='clinica',
        responsavel=usuario, is_active=True,
    )
    plano, _ = Plano.objects.get_or_create(
        nome='premium_s_plus',
        defaults={
            'nome_exibicao': 'Premium S+', 'descricao': 'Com salas',
            'valor': Decimal('99.90'), 'dias_trial': 15, 'is_active': True,
            'gerenciamento_salas': True,
        },
    )
    assinatura = Assinatura.objects.create(
        usuario=usuario, plano=plano, status='active',
        data_inicio=date.today(),
    )
    client.login(username='gestor_fluxo', password='senha123')
    return {'usuario': usuario, 'espaco': espaco, 'assinatura': assinatura}


# ---------------------------------------------------------------
# Troca o plano do gestor por um que não libera salas
# ---------------------------------------------------------------
def _rebaixar_para_basic(gestor):
    basic, _ = Plano.objects.get_or_create(
        nome='basic',
        defaults={
            'nome_exibicao': 'Basic', 'descricao': 'Básico',
            'valor': Decimal('19.90'), 'dias_trial': 7, 'is_active': True,
            'gerenciamento_salas': False,
        },
    )
    gestor['assinatura'].plano = basic
    gestor['assinatura'].save()


def _dados_sala(**extras):
    dados = {
        'nome': 'Sala Nova', 'capacidade': 4, 'valor_sessao': '70.00',
        'duracao_sessao': 60, 'horario_abertura': '08:00:00',
        'horario_fechamento': '18:00:00',
    }
    dados.update(extras)
    return dados


def _criar_sala(espaco, nome='Sala Zen', **extras):
    dados = dict(
        espaco=espaco, nome=nome, capacidade=5,
        valor_sessao=Decimal('80.00'), duracao_sessao=60,
        horario_abertura='08:00:00', horario_fechamento='18:00:00',
        is_active=True,
    )
    dados.update(extras)
    return Sala.objects.create(**dados)


# ===============================================================
# Painel principal
# ===============================================================
class TestPainelPrincipal:

    def test_espaco_basico(self, client, gestor):
        resposta = client.get(reverse('espacos:dashboard'))

        assert resposta.status_code == 200
        assert resposta.context['plano_atual'] == 'Basic'
        assert resposta.context['total_contatos'] == 0
        assert resposta.context['media_avaliacoes'] == 0

    def test_plano_premium_a_para_destaque(self, client, gestor):
        gestor['espaco'].is_destaque = True
        gestor['espaco'].save()

        resposta = client.get(reverse('espacos:dashboard'))

        assert resposta.context['plano_atual'] == 'Premium A'

    def test_plano_premium_s_para_premium(self, client, gestor):
        gestor['espaco'].is_premium = True
        gestor['espaco'].save()

        resposta = client.get(reverse('espacos:dashboard'))

        assert resposta.context['plano_atual'] == 'Premium S'

    def test_conta_contatos_avaliacoes_e_completude(self, client, gestor):
        espaco = gestor['espaco']
        ContatoEspaco.objects.create(
            espaco=espaco, nome='Ana', email='ana@teste.com',
            assunto='Oi', mensagem='Mensagem de teste',
        )
        avaliador = User.objects.create_user(
            username='aval_fluxo', email='av@fluxo.com', password='senha123'
        )
        AvaliacaoEspaco.objects.create(
            espaco=espaco, usuario=avaliador, nota=4,
            comentario='Gostei', is_active=True,
        )
        espaco.comodidades.add(Comodidade.objects.create(nome='Wi-Fi'))
        espaco.especialidades.add(Especialidade.objects.create(nome='Reiki'))
        estado = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
        espaco.cidade = Cidade.objects.create(nome='Rio', estado=estado)
        espaco.save()

        resposta = client.get(reverse('espacos:dashboard'))
        contexto = resposta.context

        assert contexto['total_contatos'] == 1
        assert contexto['contatos_30_dias'] == 1
        assert contexto['total_avaliacoes'] == 1
        assert contexto['media_avaliacoes'] == 4.0
        # nome, descrição completa, descrição breve, cidade, comodidade
        # e especialidade: os 6 itens preenchidos
        assert contexto['percentual_completude'] == 100


# ===============================================================
# Edição do perfil do espaço
# ===============================================================
class TestEditarPerfil:

    def _dados(self, **extras):
        dados = {
            'nome': 'Espaço Fluxo Editado', 'descricao_breve': 'Nova breve',
            'cep': '20040020', 'bairro': 'Lapa', 'tipo_espaco': 'clinica',
            'email': 'contato@fluxo.com', 'cidade_texto': 'Lisboa',
            'fotos_galeria-TOTAL_FORMS': 0, 'fotos_galeria-INITIAL_FORMS': 0,
        }
        dados.update(extras)
        return dados

    def test_dados_validos_atualizam_o_espaco(self, client, gestor):
        resposta = client.post(reverse('espacos:dashboard_editar'), self._dados())

        assert resposta.status_code == 302
        assert resposta.url == reverse('espacos:dashboard_editar')
        gestor['espaco'].refresh_from_db()
        assert gestor['espaco'].nome == 'Espaço Fluxo Editado'
        assert gestor['espaco'].cep == '20040-020'

    def test_dados_invalidos_reexibem_o_formulario(self, client, gestor):
        resposta = client.post(
            reverse('espacos:dashboard_editar'), self._dados(nome='')
        )

        assert resposta.status_code == 200
        assert 'nome' in resposta.context['form'].errors
        mensagens = [str(m) for m in resposta.context['messages']]
        assert any('Corrija os campos' in m for m in mensagens)
        gestor['espaco'].refresh_from_db()
        assert gestor['espaco'].nome == 'Espaço Fluxo'


# ===============================================================
# Assinatura, pagamentos e disponibilidade
# ===============================================================
class TestAssinaturaEPaginas:

    @pytest.mark.parametrize('campos,plano,preco', [
        ({}, 'Basic', 9.99),
        ({'is_destaque': True}, 'Premium A', 49.90),
        ({'is_premium': True}, 'Premium S', 99.90),
    ])
    def test_assinatura_mostra_o_plano_atual(
        self, client, gestor, campos, plano, preco
    ):
        for campo, valor in campos.items():
            setattr(gestor['espaco'], campo, valor)
        gestor['espaco'].save()

        resposta = client.get(reverse('espacos:dashboard_assinatura'))

        assert resposta.status_code == 200
        assert resposta.context['plano_atual'] == plano
        assert resposta.context['preco_atual'] == preco
        assert len(resposta.context['planos']) == 3

    def test_pagamentos_responde_com_totais_zerados(self, client, gestor):
        resposta = client.get(reverse('espacos:dashboard_pagamentos'))

        assert resposta.status_code == 200
        assert resposta.context['total_transacoes'] == 0


# ===============================================================
# Salas
# ===============================================================
class TestSalas:

    def test_criar_sala_duplicada_mostra_erro_e_nao_duplica(
        self, client, gestor
    ):
        _criar_sala(gestor['espaco'], nome='Sala Repetida')

        resposta = client.post(
            reverse('espacos:dashboard_sala_criar'),
            _dados_sala(nome='Sala Repetida'),
        )

        assert resposta.status_code == 200
        assert Sala.objects.filter(nome='Sala Repetida').count() == 1
        mensagens = [str(m) for m in resposta.context['messages']]
        assert any('Já existe uma sala' in m for m in mensagens)

    def test_editar_sala_com_sucesso(self, client, gestor):
        sala = _criar_sala(gestor['espaco'])

        resposta = client.post(
            reverse('espacos:dashboard_sala_editar', kwargs={'pk': sala.pk}),
            _dados_sala(nome='Sala Renomeada', is_active='on'),
        )

        assert resposta.status_code == 302
        sala.refresh_from_db()
        assert sala.nome == 'Sala Renomeada'

    def test_editar_sala_para_nome_ja_usado_mostra_erro(self, client, gestor):
        _criar_sala(gestor['espaco'], nome='Sala Um')
        outra = _criar_sala(gestor['espaco'], nome='Sala Dois')

        resposta = client.post(
            reverse('espacos:dashboard_sala_editar', kwargs={'pk': outra.pk}),
            _dados_sala(nome='Sala Um', is_active='on'),
        )

        assert resposta.status_code == 200
        outra.refresh_from_db()
        assert outra.nome == 'Sala Dois'
        mensagens = [str(m) for m in resposta.context['messages']]
        assert any('Já existe outra sala' in m for m in mensagens)

    def test_editar_sala_sem_permissao_do_plano(self, client, gestor):
        sala = _criar_sala(gestor['espaco'])
        _rebaixar_para_basic(gestor)

        resposta = client.get(
            reverse('espacos:dashboard_sala_editar', kwargs={'pk': sala.pk})
        )

        assert resposta.status_code == 302
        assert resposta.url == reverse('espacos:dashboard_salas')

    def test_nao_edita_sala_de_outro_espaco(self, client, gestor):
        dono = User.objects.create_user(
            username='outro_dono', email='o@fluxo.com', password='senha123'
        )
        outro_espaco = Espaco.objects.create(
            nome='Outro Espaço', slug='outro-espaco', descricao_breve='b',
            descricao_completa='<p>c</p>', endereco='Rua C', cep='20040-020',
            bairro='Centro', tipo_espaco='clinica', responsavel=dono,
            is_active=True,
        )
        sala_alheia = _criar_sala(outro_espaco, nome='Sala Alheia')

        resposta = client.get(reverse(
            'espacos:dashboard_sala_editar', kwargs={'pk': sala_alheia.pk}
        ))

        assert resposta.status_code == 404

    def test_toggle_desativa_e_reativa(self, client, gestor):
        sala = _criar_sala(gestor['espaco'])
        url = reverse('espacos:dashboard_sala_toggle', kwargs={'pk': sala.pk})

        client.get(url)
        sala.refresh_from_db()
        assert sala.is_active is False

        client.get(url)
        sala.refresh_from_db()
        assert sala.is_active is True

    def test_toggle_sem_permissao_do_plano(self, client, gestor):
        sala = _criar_sala(gestor['espaco'])
        _rebaixar_para_basic(gestor)

        resposta = client.get(reverse(
            'espacos:dashboard_sala_toggle', kwargs={'pk': sala.pk}
        ))

        assert resposta.status_code == 302
        sala.refresh_from_db()
        assert sala.is_active is True

    def test_toggle_sala_inexistente(self, client, gestor):
        resposta = client.get(reverse(
            'espacos:dashboard_sala_toggle', kwargs={'pk': 999999}
        ))

        assert resposta.status_code == 302
        assert resposta.url == reverse('espacos:dashboard_salas')


# ===============================================================
# Convites de terapeutas
# ===============================================================
class TestConvites:

    @pytest.fixture
    def terapeuta(self):
        usuario = User.objects.create_user(
            username='terap_convite', email='terapeuta@convite.com',
            password='senha123',
        )
        return Terapeuta.objects.create(
            user=usuario, nome_completo='Terapeuta Convite',
            nome_exibicao='Terapeuta Convite', slug='terapeuta-convite',
            bio_curta='Bio.', bio_completa='<p>Bio.</p>', formacao='Formação',
            is_active=True,
        )

    def _convidar(self, client, email, mensagem=''):
        return client.post(
            reverse('espacos:convidar_terapeuta'),
            {'email_terapeuta': email, 'mensagem': mensagem},
        )

    def test_terapeuta_cadastrado_recebe_convite_pendente(
        self, client, gestor, terapeuta
    ):
        resposta = self._convidar(client, 'terapeuta@convite.com')

        assert resposta.status_code == 302
        vinculo = VinculoTerapeutaEspaco.objects.get()
        assert vinculo.status == 'PENDENTE'
        assert vinculo.tipo == 'CONVITE'

    def test_convite_pendente_nao_duplica(self, client, gestor, terapeuta):
        VinculoTerapeutaEspaco.objects.create(
            terapeuta=terapeuta, espaco=gestor['espaco'],
            status='PENDENTE', tipo='CONVITE',
        )

        self._convidar(client, 'terapeuta@convite.com')

        assert VinculoTerapeutaEspaco.objects.count() == 1

    def test_vinculo_recusado_e_reaberto_como_convite(
        self, client, gestor, terapeuta
    ):
        VinculoTerapeutaEspaco.objects.create(
            terapeuta=terapeuta, espaco=gestor['espaco'],
            status='RECUSADO', tipo='SOLICITACAO', is_active=False,
        )

        self._convidar(client, 'terapeuta@convite.com')

        vinculo = VinculoTerapeutaEspaco.objects.get()
        assert vinculo.status == 'PENDENTE'
        assert vinculo.tipo == 'CONVITE'
        assert vinculo.is_active is True

    def test_email_novo_gera_convite_externo_e_envia_email(
        self, client, gestor
    ):
        resposta = self._convidar(
            client, 'novo@terapeuta.com', 'Venha fazer parte!'
        )

        assert resposta.status_code == 302
        convite = ConviteExterno.objects.get()
        assert convite.email == 'novo@terapeuta.com'
        assert convite.espaco == gestor['espaco']
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['novo@terapeuta.com']
        assert str(convite.token) in mail.outbox[0].alternatives[0][0]

    def test_convite_externo_pendente_nao_reenvia(self, client, gestor):
        self._convidar(client, 'novo@terapeuta.com')
        self._convidar(client, 'novo@terapeuta.com')

        assert ConviteExterno.objects.count() == 1
        assert len(mail.outbox) == 1

    def test_falha_no_envio_desfaz_o_convite(self, client, gestor):
        with mock.patch(
            'django.core.mail.send_mail', side_effect=OSError('smtp fora')
        ):
            self._convidar(client, 'novo@terapeuta.com')

        assert ConviteExterno.objects.count() == 0
