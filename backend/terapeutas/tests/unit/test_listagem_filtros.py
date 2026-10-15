# ===============================================================
# Título: Testes dos Filtros de Listagem de Terapeutas
# Descrição: Cobre a busca avançada (TerapeutaListView) e a listagem
#            simples (terapeutas_sem_filtro): tipo de sessão, local,
#            terapias, acessibilidade, perfil, público, texto e
#            ordenação, além dos valores inválidos que devem ser
#            ignorados sem derrubar a página.
# Autor: Will
# Data: 2026-10-15
# ===============================================================

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import Cidade, Especialidade, Estado
from terapeutas.models import Terapeuta, TerapeutaEspecialidade

pytestmark = pytest.mark.django_db

User = get_user_model()


# ---------------------------------------------------------------
# Cria um terapeuta ativo com os campos que os filtros usam.
# Os valores padrão podem ser trocados por argumento nomeado.
# ---------------------------------------------------------------
def _criar_terapeuta(sufixo, cidade, especialidade, **extras):
    user = User.objects.create_user(
        username=f'filtro_{sufixo}',
        email=f'filtro_{sufixo}@teste.com',
        password='senha123',
    )
    dados = dict(
        user=user,
        nome_completo=f'Terapeuta {sufixo}',
        nome_exibicao=f'Terapeuta {sufixo}',
        slug=f'terapeuta-{sufixo}',
        bio_curta=f'Bio curta {sufixo}.',
        bio_completa=f'<p>Bio {sufixo}.</p>',
        formacao='Formação de teste',
        cidade_principal=cidade,
        is_active=True,
    )
    dados.update(extras)
    terapeuta = Terapeuta.objects.create(**dados)
    TerapeutaEspecialidade.objects.create(
        terapeuta=terapeuta, especialidade=especialidade
    )
    return terapeuta


# ---------------------------------------------------------------
# Cenário: três terapeutas bem diferentes entre si
#   ana    - Rio de Janeiro, presencial+online, acessível, premium_s
#   bruno  - Niterói, domicílio, sem acessibilidade, basic
#   carla  - São Paulo, online, premium_a, mais experiente
# ---------------------------------------------------------------
@pytest.fixture
def cenario():
    rj = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
    sp = Estado.objects.create(nome='São Paulo', sigla='SP')
    rio = Cidade.objects.create(nome='Rio de Janeiro', estado=rj)
    niteroi = Cidade.objects.create(nome='Niterói', estado=rj)
    sao_paulo = Cidade.objects.create(nome='São Paulo', estado=sp)

    reiki = Especialidade.objects.create(nome='Reiki')
    massoterapia = Especialidade.objects.create(nome='Massoterapia')
    acupuntura = Especialidade.objects.create(nome='Acupuntura')

    ana = _criar_terapeuta(
        'ana', rio, reiki,
        tipos_sessao=['presencial', 'online'], acessibilidade=True,
        plano='premium_s', tipo_perfil='individual', para_quem=['adultos'],
        experiencia_anos=10, nome_exibicao='Ana Reiki',
    )
    bruno = _criar_terapeuta(
        'bruno', niteroi, massoterapia,
        tipos_sessao=['domicilio'], acessibilidade=False,
        plano='basic', tipo_perfil='espacos', para_quem=['criancas'],
        experiencia_anos=2, nome_exibicao='Bruno Massagem',
    )
    carla = _criar_terapeuta(
        'carla', sao_paulo, acupuntura,
        tipos_sessao=['online'], acessibilidade=False,
        plano='premium_a', tipo_perfil='individual', para_quem=['adultos'],
        experiencia_anos=20, nome_exibicao='Carla Acupuntura',
    )
    return {
        'ana': ana, 'bruno': bruno, 'carla': carla,
        'rj': rj, 'sp': sp,
        'rio': rio, 'niteroi': niteroi, 'sao_paulo': sao_paulo,
        'reiki': reiki, 'massoterapia': massoterapia,
    }


# ---------------------------------------------------------------
# Atalho: devolve os nomes de exibição da página, na ordem em que
# a view os entregou ao template.
# ---------------------------------------------------------------
def _nomes(response):
    return [t.nome_exibicao for t in response.context['terapeutas']]


# ===============================================================
# Busca avançada: TerapeutaListView
# ===============================================================
class TestBuscaAvancada:

    def _buscar(self, client, **params):
        return client.get(reverse('terapeutas:buscar'), params)

    def test_sem_filtros_lista_todos_ativos(self, client, cenario):
        resposta = self._buscar(client)

        assert resposta.status_code == 200
        assert set(_nomes(resposta)) == {
            'Ana Reiki', 'Bruno Massagem', 'Carla Acupuntura'
        }
        assert resposta.context['total_resultados'] == 3

    def test_ignora_terapeuta_inativo(self, client, cenario):
        cenario['bruno'].is_active = False
        cenario['bruno'].save()

        assert 'Bruno Massagem' not in _nomes(self._buscar(client))

    def test_filtra_por_tipo_de_sessao(self, client, cenario):
        resposta = self._buscar(client, tipos_sessao='domicilio')

        assert _nomes(resposta) == ['Bruno Massagem']

    def test_tipo_de_sessao_invalido_e_ignorado(self, client, cenario):
        resposta = self._buscar(client, tipos_sessao='teletransporte')

        assert len(_nomes(resposta)) == 3

    def test_filtra_por_cidade(self, client, cenario):
        resposta = self._buscar(client, cidade=cenario['niteroi'].id)

        assert _nomes(resposta) == ['Bruno Massagem']
        assert resposta.context['localizacao_atual'] == 'Niterói - RJ'

    def test_cidade_adicional_tambem_conta(self, client, cenario):
        # Ana atende também em Niterói, além da cidade principal
        cenario['ana'].cidades_atendimento.add(cenario['niteroi'])

        resposta = self._buscar(client, cidade=cenario['niteroi'].id)

        assert set(_nomes(resposta)) == {'Ana Reiki', 'Bruno Massagem'}

    def test_cidade_nao_numerica_nao_quebra(self, client, cenario):
        resposta = self._buscar(client, cidade='xyz')

        assert resposta.status_code == 200
        assert 'localizacao_atual' not in resposta.context

    def test_cidade_inexistente_nao_define_localizacao(self, client, cenario):
        resposta = self._buscar(client, cidade=999999)

        assert resposta.status_code == 200
        assert 'localizacao_atual' not in resposta.context

    def test_filtra_por_estado(self, client, cenario):
        resposta = self._buscar(client, estado=cenario['rj'].id)

        assert set(_nomes(resposta)) == {'Ana Reiki', 'Bruno Massagem'}

    def test_estado_nao_numerico_e_ignorado(self, client, cenario):
        resposta = self._buscar(client, estado='abc')

        assert resposta.status_code == 200

    def test_filtra_por_especialidade(self, client, cenario):
        resposta = self._buscar(client, especialidades=cenario['reiki'].id)

        assert _nomes(resposta) == ['Ana Reiki']

    def test_especialidade_nao_numerica_e_ignorada(self, client, cenario):
        resposta = self._buscar(client, especialidades='abc')

        assert resposta.status_code == 200

    def test_filtra_por_acessibilidade(self, client, cenario):
        resposta = self._buscar(client, acessibilidade='sim')

        assert _nomes(resposta) == ['Ana Reiki']

    def test_filtra_por_perfil_profissional(self, client, cenario):
        resposta = self._buscar(client, perfil_profissional='espacos')

        assert _nomes(resposta) == ['Bruno Massagem']

    def test_perfil_profissional_invalido_e_ignorado(self, client, cenario):
        resposta = self._buscar(client, perfil_profissional='alienigena')

        assert len(_nomes(resposta)) == 3

    def test_filtra_por_publico(self, client, cenario):
        resposta = self._buscar(client, para_quem='criancas')

        assert _nomes(resposta) == ['Bruno Massagem']

    def test_publico_invalido_e_ignorado(self, client, cenario):
        resposta = self._buscar(client, para_quem='marcianos')

        assert len(_nomes(resposta)) == 3

    def test_busca_por_texto_no_nome_e_na_especialidade(self, client, cenario):
        por_nome = self._buscar(client, q='Carla')
        por_terapia = self._buscar(client, q='Massoterapia')

        assert _nomes(por_nome) == ['Carla Acupuntura']
        assert _nomes(por_terapia) == ['Bruno Massagem']

    def test_ordenar_por_nome(self, client, cenario):
        resposta = self._buscar(client, ordenacao='nome')

        assert _nomes(resposta) == [
            'Ana Reiki', 'Bruno Massagem', 'Carla Acupuntura'
        ]

    def test_ordenar_por_mais_experiente(self, client, cenario):
        resposta = self._buscar(client, ordenacao='mais_experiente')

        assert _nomes(resposta)[0] == 'Carla Acupuntura'

    def test_ordenar_por_melhor_avaliado_responde_ok(self, client, cenario):
        resposta = self._buscar(client, ordenacao='melhor_avaliado')

        assert resposta.status_code == 200
        assert len(_nomes(resposta)) == 3

    def test_relevancia_coloca_plano_mais_alto_primeiro(self, client, cenario):
        resposta = self._buscar(client)

        # premium_s > premium_a > basic
        assert _nomes(resposta) == [
            'Ana Reiki', 'Carla Acupuntura', 'Bruno Massagem'
        ]


# ===============================================================
# Listagem simples: terapeutas_sem_filtro
# ===============================================================
class TestListagemSimples:

    def _listar(self, client, **params):
        return client.get(reverse('terapeutas:listagem_simples'), params)

    def test_sem_filtros_lista_todos(self, client, cenario):
        resposta = self._listar(client)

        assert resposta.status_code == 200
        assert len(_nomes(resposta)) == 3
        assert resposta.context['titulo_pagina'] == 'Terapeutas'
        assert resposta.context['filtros_aplicados'] == []

    def test_filtra_por_tipo_de_sessao(self, client, cenario):
        resposta = self._listar(client, tipo_sessao='domicilio')

        assert _nomes(resposta) == ['Bruno Massagem']
        assert 'Tipos: domicilio' in resposta.context['filtros_aplicados']

    def test_tipo_de_sessao_desconhecido_e_ignorado(self, client, cenario):
        resposta = self._listar(client, tipo_sessao='teletransporte')

        assert len(_nomes(resposta)) == 3

    def test_filtra_por_estado_pelo_nome_ou_sigla(self, client, cenario):
        por_sigla = self._listar(client, estado='SP')
        por_nome = self._listar(client, estado='Rio')

        assert _nomes(por_sigla) == ['Carla Acupuntura']
        assert set(_nomes(por_nome)) == {'Ana Reiki', 'Bruno Massagem'}
        assert por_sigla.context['titulo_pagina'] == 'Terapeutas no SP'

    def test_filtra_por_cidade(self, client, cenario):
        resposta = self._listar(client, cidade='Niter')

        assert _nomes(resposta) == ['Bruno Massagem']
        assert resposta.context['titulo_pagina'] == 'Terapeutas em Niter'

    def test_filtra_por_terapia_conhecida(self, client, cenario):
        resposta = self._listar(client, terapias='reiki')

        assert _nomes(resposta) == ['Ana Reiki']
        assert 'Terapias: reiki' in resposta.context['filtros_aplicados']

    @pytest.mark.parametrize('chave,nome', [
        ('aromaterapia', 'Aromaterapia'),
        ('cristaloterapia', 'Cristaloterapia'),
        ('massoterapia', 'Massoterapia'),
        ('terapia-tantrica', 'Terapia Tântrica'),
        ('ThetaHealing', 'ThetaHealing'),
        ('psicoterapia', 'Psicoterapia'),
        ('acupuntura', 'Acupuntura'),
    ])
    def test_cada_terapia_do_modal_resolve_a_especialidade(
        self, client, cenario, chave, nome
    ):
        # Garante a especialidade e confere que a página responde
        Especialidade.objects.get_or_create(nome=nome)

        resposta = self._listar(client, terapias=chave)

        assert resposta.status_code == 200

    def test_terapia_generica_busca_por_nome(self, client, cenario):
        Especialidade.objects.create(nome='Yoga')

        resposta = self._listar(client, terapias='yoga')

        # Existe a especialidade, mas ninguém a oferece
        assert resposta.status_code == 200
        assert _nomes(resposta) == []

    def test_terapia_inexistente_nao_filtra(self, client, cenario):
        resposta = self._listar(client, terapias='aromaterapia')

        # Sem a especialidade cadastrada, o filtro é descartado
        assert len(_nomes(resposta)) == 3

    def test_filtra_por_acessibilidade(self, client, cenario):
        com = self._listar(client, acessibilidade='sim')
        sem = self._listar(client, acessibilidade='nao')

        assert _nomes(com) == ['Ana Reiki']
        assert set(_nomes(sem)) == {'Bruno Massagem', 'Carla Acupuntura'}
        assert 'Acessibilidade: sim' in com.context['filtros_aplicados']

    def test_listagem_por_especialidade_na_url(self, client, cenario):
        url = reverse(
            'terapeutas:por_especialidade',
            kwargs={'especialidade_slug': cenario['reiki'].slug},
        )

        resposta = client.get(url)

        assert _nomes(resposta) == ['Ana Reiki']
        assert resposta.context['titulo_pagina'] == 'Reiki'
        assert resposta.context['especialidade_atual'] == cenario['reiki']

    def test_especialidade_inexistente_retorna_404(self, client, cenario):
        url = reverse(
            'terapeutas:por_especialidade',
            kwargs={'especialidade_slug': 'nao-existe'},
        )

        assert client.get(url).status_code == 404

    def test_ordena_destaque_premium_verificado_nome(self, client, cenario):
        cenario['carla'].destaque = True
        cenario['carla'].save()

        resposta = self._listar(client)

        assert _nomes(resposta)[0] == 'Carla Acupuntura'
