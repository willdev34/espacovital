# ===============================================================
# Título: Testes de Busca Avançada, Listagens, Contato e Avaliação
# Descrição: Cobre os filtros e a ordenação de EspacoListView, a
#            disponibilidade por período (Espaco.atende_no_periodo),
#            o contexto das listagens, o contato com o espaço, a
#            avaliação, as estatísticas e a página por região.
# Autor: Will
# Data: 2026-10-15
# ===============================================================

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from core.models import Cidade, Estado
from espacos import views
from espacos.models import (
    AvaliacaoEspaco, Comodidade, ContatoEspaco, Espaco,
)
from core.models import Especialidade

pytestmark = pytest.mark.django_db

User = get_user_model()


# ---------------------------------------------------------------
# Monta o contexto de uma ListView sem renderizar template
# ---------------------------------------------------------------
def _contexto_lista(classe_view, query='', **kwargs):
    request = RequestFactory().get('/' + query)
    view = classe_view()
    view.setup(request, **kwargs)
    view.object_list = view.get_queryset()
    return view.get_context_data()


# ---------------------------------------------------------------
# Cenário: três espaços com localização, terapias e horários
#   zen   - Rio, acessível, aceita locação, destaque, funciona de manhã
#   lotus - Niterói, sem acessibilidade, premium, funciona à tarde/noite
#           e aos sábados
#   vida  - São Paulo, sem horários cadastrados
# ---------------------------------------------------------------
@pytest.fixture
def cenario():
    rj = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
    sp = Estado.objects.create(nome='São Paulo', sigla='SP')
    rio = Cidade.objects.create(nome='Rio de Janeiro', estado=rj)
    niteroi = Cidade.objects.create(nome='Niterói', estado=rj)
    sao_paulo = Cidade.objects.create(nome='São Paulo', estado=sp)

    reiki = Especialidade.objects.create(nome='Reiki')
    yoga = Especialidade.objects.create(nome='Yoga')
    sala_silenciosa = Comodidade.objects.create(nome='Sala silenciosa')
    estacionamento = Comodidade.objects.create(nome='Estacionamento')

    dono = User.objects.create_user(
        username='dono_busca', email='dono@busca.com', password='senha123'
    )

    def criar(slug, nome, cidade, **extras):
        dados = dict(
            nome=nome, slug=slug, descricao_breve=f'Breve {nome}',
            descricao_completa=f'<p>{nome}</p>', endereco='Rua A, 1',
            cep='20040-020', bairro='Centro', tipo_espaco='clinica',
            cidade=cidade, responsavel=dono, is_active=True,
        )
        dados.update(extras)
        return Espaco.objects.create(**dados)

    zen = criar(
        'zen', 'Espaço Zen', rio, tem_acessibilidade=True,
        aceita_locacao=True, is_destaque=True,
        horarios_semana={'segunda': [{'inicio': '08:00', 'fim': '12:00'}]},
    )
    lotus = criar(
        'lotus', 'Espaço Lótus', niteroi, tem_acessibilidade=False,
        aceita_locacao=False, is_premium=True, tipo_espaco='centro_holistico',
        horarios_semana={'sabado': [{'inicio': '14:00', 'fim': '20:00'}]},
    )
    vida = criar('vida', 'Espaço Vida', sao_paulo)

    zen.especialidades.add(reiki)
    zen.comodidades.add(sala_silenciosa)
    lotus.especialidades.add(yoga)
    lotus.comodidades.add(sala_silenciosa, estacionamento)

    return {
        'zen': zen, 'lotus': lotus, 'vida': vida, 'dono': dono,
        'rj': rj, 'sp': sp, 'rio': rio, 'niteroi': niteroi,
        'reiki': reiki, 'yoga': yoga,
        'sala_silenciosa': sala_silenciosa, 'estacionamento': estacionamento,
    }


def _nomes(resposta):
    return [e.nome for e in resposta.context['espacos']]


# ===============================================================
# Busca avançada: EspacoListView
# ===============================================================
class TestBuscaAvancada:

    def _buscar(self, client, **params):
        return client.get(reverse('espacos:busca_avancada'), params)

    def test_sem_filtros_lista_todos(self, client, cenario):
        resposta = self._buscar(client)

        assert resposta.status_code == 200
        assert len(_nomes(resposta)) == 3
        assert resposta.context['total_espacos'] == 3

    def test_filtra_por_tipo_de_espaco(self, client, cenario):
        resposta = self._buscar(client, tipo_espaco='centro_holistico')

        assert _nomes(resposta) == ['Espaço Lótus']

    def test_tipo_todos_nao_filtra(self, client, cenario):
        assert len(_nomes(self._buscar(client, tipo_espaco='todos'))) == 3

    def test_filtra_por_estado_e_cidade(self, client, cenario):
        por_estado = self._buscar(client, estado=cenario['sp'].id)
        por_cidade = self._buscar(client, cidade=cenario['niteroi'].id)

        assert _nomes(por_estado) == ['Espaço Vida']
        assert _nomes(por_cidade) == ['Espaço Lótus']

    def test_filtra_por_pais(self, client, cenario):
        resposta = self._buscar(client, pais=999999)

        assert resposta.status_code == 200
        assert _nomes(resposta) == []

    def test_filtra_por_terapias(self, client, cenario):
        resposta = self._buscar(client, terapias=cenario['yoga'].id)

        assert _nomes(resposta) == ['Espaço Lótus']

    def test_terapias_todas_ou_invalidas_nao_filtram(self, client, cenario):
        todas = self._buscar(client, terapias='todas')
        invalidas = self._buscar(client, terapias='abc')

        assert len(_nomes(todas)) == 3
        assert len(_nomes(invalidas)) == 3

    def test_filtra_por_acessibilidade(self, client, cenario):
        com = self._buscar(client, acessibilidade='sim')
        sem = self._buscar(client, acessibilidade='nao')

        assert _nomes(com) == ['Espaço Zen']
        assert set(_nomes(sem)) == {'Espaço Lótus', 'Espaço Vida'}

    def test_filtra_por_locacao(self, client, cenario):
        aceita = self._buscar(client, locacao='sim')
        nao_aceita = self._buscar(client, locacao='nao')

        assert _nomes(aceita) == ['Espaço Zen']
        assert set(_nomes(nao_aceita)) == {'Espaço Lótus', 'Espaço Vida'}

    def test_comodidades_exigem_todas_as_marcadas(self, client, cenario):
        resposta = self._buscar(
            client,
            comodidades=[
                cenario['sala_silenciosa'].id, cenario['estacionamento'].id
            ],
        )

        assert _nomes(resposta) == ['Espaço Lótus']

    def test_comodidade_invalida_e_ignorada(self, client, cenario):
        assert len(_nomes(self._buscar(client, comodidades='abc'))) == 3

    def test_busca_por_texto(self, client, cenario):
        por_nome = self._buscar(client, busca='Lótus')
        por_cidade = self._buscar(client, busca='Niter')
        por_terapia = self._buscar(client, busca='Reiki')

        assert _nomes(por_nome) == ['Espaço Lótus']
        assert _nomes(por_cidade) == ['Espaço Lótus']
        assert _nomes(por_terapia) == ['Espaço Zen']

    # ---- Disponibilidade por período ----

    def test_disponibilidade_manha(self, client, cenario):
        resposta = self._buscar(client, disponibilidade='manha')

        assert _nomes(resposta) == ['Espaço Zen']

    def test_disponibilidade_varios_periodos_somam(self, client, cenario):
        resposta = self._buscar(
            client, disponibilidade=['manha', 'finais_de_semana']
        )

        assert set(_nomes(resposta)) == {'Espaço Zen', 'Espaço Lótus'}

    def test_disponibilidade_noite_e_fim_de_semana(self, client, cenario):
        noite = self._buscar(client, disponibilidade='noite')
        fds = self._buscar(client, disponibilidade='finais_de_semana')

        assert _nomes(noite) == ['Espaço Lótus']
        assert _nomes(fds) == ['Espaço Lótus']

    # ---- Ordenação ----

    def test_ordem_padrao_destaque_primeiro(self, client, cenario):
        assert _nomes(self._buscar(client))[0] == 'Espaço Zen'

    def test_ordem_por_nome(self, client, cenario):
        resposta = self._buscar(client, ordem='nome')

        assert _nomes(resposta) == [
            'Espaço Lótus', 'Espaço Vida', 'Espaço Zen'
        ]

    def test_ordem_por_avaliacao(self, client, cenario):
        usuario = User.objects.create_user(
            username='avaliador_busca', email='a@busca.com', password='x12345'
        )
        AvaliacaoEspaco.objects.create(
            espaco=cenario['vida'], usuario=usuario, nota=5,
            comentario='Ótimo', is_active=True,
        )

        resposta = self._buscar(client, ordem='avaliacao')

        assert resposta.status_code == 200
        assert _nomes(resposta)[0] == 'Espaço Vida'

    def test_ordem_por_recente(self, client, cenario):
        resposta = self._buscar(client, ordem='recente')

        assert _nomes(resposta)[0] == 'Espaço Vida'

    def test_contexto_mantem_filtros_aplicados(self, client, cenario):
        resposta = self._buscar(client, busca='Zen', ordem='nome')

        filtros = resposta.context['filtros_aplicados']
        assert filtros['busca'] == 'Zen'
        assert filtros['ordem'] == 'nome'
        assert resposta.context['espacos_verificados'] == 0


# ===============================================================
# Espaco.atende_no_periodo
# ===============================================================
class TestAtendeNoPeriodo:

    def _espaco(self, horarios):
        return Espaco(nome='X', horarios_semana=horarios)

    def test_sem_horarios_nao_atende_em_nenhum_periodo(self):
        espaco = self._espaco({})

        for periodo in ('manha', 'tarde', 'noite', 'finais_de_semana'):
            assert espaco.atende_no_periodo(periodo) is False

    def test_faixas_do_dia(self):
        espaco = self._espaco(
            {'terca': [{'inicio': '09:00', 'fim': '13:00'}]}
        )

        assert espaco.atende_no_periodo('manha') is True
        assert espaco.atende_no_periodo('tarde') is True
        assert espaco.atende_no_periodo('noite') is False

    def test_dia_de_semana_nao_conta_como_fim_de_semana(self):
        espaco = self._espaco(
            {'quarta': [{'inicio': '09:00', 'fim': '18:00'}]}
        )

        assert espaco.atende_no_periodo('finais_de_semana') is False

    def test_domingo_conta_como_fim_de_semana(self):
        espaco = self._espaco(
            {'domingo': [{'inicio': '09:00', 'fim': '12:00'}]}
        )

        assert espaco.atende_no_periodo('finais_de_semana') is True

    def test_horario_que_passa_da_meia_noite_cobre_a_noite(self):
        espaco = self._espaco(
            {'sexta': [{'inicio': '22:00', 'fim': '02:00'}]}
        )

        assert espaco.atende_no_periodo('noite') is True
        assert espaco.atende_no_periodo('manha') is False

    def test_horario_invalido_e_ignorado(self):
        espaco = self._espaco({
            'segunda': [
                {'inicio': 'abc', 'fim': '10:00'},
                {'inicio': '', 'fim': ''},
            ],
            'terca': None,
        })

        assert espaco.atende_no_periodo('manha') is False

    def test_periodo_desconhecido_nao_atende(self):
        espaco = self._espaco(
            {'segunda': [{'inicio': '08:00', 'fim': '12:00'}]}
        )

        assert espaco.atende_no_periodo('madrugada') is False


# ===============================================================
# Home, listagem simples e por região (contexto das views)
# ===============================================================
class TestHomeEListagens:

    def test_home_traz_destaques_e_totais(self, cenario):
        request = RequestFactory().get('/')
        view = views.EspacoHomeView()
        view.setup(request)

        contexto = view.get_context_data()

        assert list(contexto['espacos_destaque']) == [cenario['zen']]
        assert contexto['total_espacos'] == 3
        assert contexto['total_cidades'] == 3
        assert contexto['total_comodidades'] == 2

    def test_home_responde_pela_url(self, client, cenario):
        resposta = client.get(reverse('espacos:home'))

        assert resposta.status_code == 200
        assert resposta.context['total_espacos'] == 3
        assert 'Espaço Zen' in resposta.content.decode()

    def test_listagem_simples_agrupa_por_regiao(self, cenario):
        contexto = _contexto_lista(views.EspacoListagemSimplesView)

        grupos = contexto['espacos_por_regiao']
        assert [e.nome for e in grupos['Rio de Janeiro']] == ['Espaço Zen']
        assert [e.nome for e in grupos['São Paulo']] == ['Espaço Vida']
        assert [e.nome for e in grupos['Outras']] == ['Espaço Lótus']
        assert list(grupos['Belo Horizonte']) == []

    def test_listagem_simples_mostra_cards_e_contador(self, client, cenario):
        resposta = client.get(reverse('espacos:listagem_simples'))

        html = resposta.content.decode()
        assert resposta.status_code == 200
        assert '<strong>3</strong>' in html
        for nome in ('Espaço Zen', 'Espaço Lótus', 'Espaço Vida'):
            assert nome in html
        assert reverse('espacos:detalhe', kwargs={'slug': 'zen'}) in html

    def test_listagem_simples_oferece_filtro_para_a_busca(
        self, client, cenario
    ):
        resposta = client.get(reverse('espacos:listagem_simples'))

        html = resposta.content.decode()
        assert f'action="{reverse("espacos:busca_avancada")}"' in html
        assert 'name="estado"' in html
        assert 'Rio de Janeiro' in html

    def test_listagem_simples_sem_espacos(self, client, db):
        resposta = client.get(reverse('espacos:listagem_simples'))

        assert resposta.status_code == 200
        assert 'Nenhum espaço encontrado' in resposta.content.decode()

    def test_por_regiao_lista_espacos_da_cidade(self, client, cenario):
        url = reverse('espacos:por_regiao', kwargs={'cidade_slug': 'niteroi'})

        resposta = client.get(url)

        assert resposta.status_code == 200
        assert resposta.context['cidade'] == cenario['niteroi']
        assert resposta.context['total_espacos'] == 1
        assert 'Espaço Lótus' in resposta.content.decode()

    def test_por_regiao_cidade_sem_espaco_retorna_404(self, client, cenario):
        Cidade.objects.create(nome='Cidade Vazia', estado=cenario['rj'])
        url = reverse(
            'espacos:por_regiao', kwargs={'cidade_slug': 'cidade-vazia'}
        )

        assert client.get(url).status_code == 404


# ===============================================================
# Contato com o espaço
# ===============================================================
class TestContatoComOEspaco:

    def _url(self, espaco):
        return reverse('espacos:contato', kwargs={'slug': espaco.slug})

    def _dados(self, **extras):
        dados = {
            'nome': 'Maria Visitante', 'email': 'maria@teste.com',
            'telefone': '(21) 98765-4321', 'assunto': 'Valores',
            'mensagem': 'Gostaria de saber os valores das salas.',
        }
        dados.update(extras)
        return dados

    def test_envio_valido_cria_contato_e_volta_ao_perfil(
        self, client, cenario
    ):
        resposta = client.post(self._url(cenario['zen']), self._dados())

        assert resposta.status_code == 302
        assert resposta.url == reverse(
            'espacos:detalhe', kwargs={'slug': 'zen'}
        )
        contato = ContatoEspaco.objects.get()
        assert contato.espaco == cenario['zen']
        assert contato.email == 'maria@teste.com'

    def test_formulario_de_contato_abre(self, client, cenario):
        resposta = client.get(self._url(cenario['zen']))

        assert resposta.status_code == 200
        assert 'Fale com Espaço Zen' in resposta.content.decode()

    def test_envio_invalido_reexibe_o_formulario(self, client, cenario):
        resposta = client.post(
            self._url(cenario['zen']), self._dados(email='nao-e-email')
        )

        assert resposta.status_code == 200
        assert ContatoEspaco.objects.count() == 0
        assert 'email' in resposta.context['form'].errors
        assert resposta.context['espaco'] == cenario['zen']

    def test_espaco_inativo_nao_recebe_contato(self, client, cenario):
        cenario['zen'].is_active = False
        cenario['zen'].save()

        resposta = client.post(self._url(cenario['zen']), self._dados())

        assert resposta.status_code == 404
        assert ContatoEspaco.objects.count() == 0


# ===============================================================
# Avaliação do espaço
# ===============================================================
class TestAvaliarEspaco:

    def _url(self, espaco):
        return reverse('espacos:avaliar', kwargs={'slug': espaco.slug})

    @pytest.fixture
    def usuario_logado(self, client):
        usuario = User.objects.create_user(
            username='avaliador', email='avaliador@teste.com',
            password='senha123',
        )
        client.login(username='avaliador', password='senha123')
        return usuario

    def test_exige_login(self, client, cenario):
        resposta = client.get(self._url(cenario['zen']))

        assert resposta.status_code == 302
        assert resposta.url.startswith('/accounts/login/')

    def test_formulario_de_avaliacao_abre(
        self, client, cenario, usuario_logado
    ):
        resposta = client.get(self._url(cenario['zen']))

        assert resposta.status_code == 200
        assert 'Enviar avaliação' in resposta.content.decode()

    def test_mostra_aviso_para_quem_ja_avaliou(
        self, client, cenario, usuario_logado
    ):
        existente = AvaliacaoEspaco.objects.create(
            espaco=cenario['zen'], usuario=usuario_logado, nota=4,
            comentario='Bom', is_active=True,
        )

        resposta = client.get(self._url(cenario['zen']))

        assert resposta.status_code == 200
        assert resposta.context['avaliacao_existente'] == existente
        assert 'Você já avaliou este espaço' in resposta.content.decode()

    def test_avaliacao_valida_e_salva(
        self, client, cenario, usuario_logado
    ):
        resposta = client.post(
            self._url(cenario['zen']),
            {'nota': 5, 'comentario': 'Lugar muito acolhedor.'},
        )

        assert resposta.status_code == 302
        avaliacao = AvaliacaoEspaco.objects.get()
        assert avaliacao.usuario == usuario_logado
        assert avaliacao.espaco == cenario['zen']

    def test_nao_avalia_duas_vezes(self, client, cenario, usuario_logado):
        AvaliacaoEspaco.objects.create(
            espaco=cenario['zen'], usuario=usuario_logado, nota=3,
            comentario='Ok', is_active=True,
        )

        resposta = client.post(
            self._url(cenario['zen']),
            {'nota': 5, 'comentario': 'Segunda tentativa.'},
        )

        assert resposta.status_code == 302
        assert AvaliacaoEspaco.objects.count() == 1


# ===============================================================
# Estatísticas do espaço (apenas do responsável)
# ===============================================================
class TestEstatisticasDoEspaco:

    def _url(self, espaco):
        return reverse('espacos:estatisticas', kwargs={'slug': espaco.slug})

    def test_responsavel_ve_totais(self, client, cenario):
        ContatoEspaco.objects.create(
            espaco=cenario['zen'], nome='Ana', email='ana@teste.com',
            assunto='Oi', mensagem='Olá',
        )
        client.login(username='dono_busca', password='senha123')

        resposta = client.get(self._url(cenario['zen']))

        assert resposta.status_code == 200
        assert resposta.context['total_contatos'] == 1
        assert resposta.context['contatos_mes'] == 1
        assert resposta.context['total_avaliacoes'] == 0
        assert 'Estatísticas de Espaço Zen' in resposta.content.decode()

    def test_outro_usuario_nao_acessa(self, client, cenario):
        User.objects.create_user(
            username='intruso', email='i@teste.com', password='senha123'
        )
        client.login(username='intruso', password='senha123')

        resposta = client.get(self._url(cenario['zen']))

        assert resposta.status_code == 404
