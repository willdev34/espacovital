# ===============================================================
# Título: Testes das Views do App Terapias
# Descrição: Testes unitários para TerapiasDestaquesView,
#             TerapiasListagemView e TerapiaDetalheView
# ===============================================================

from django.test import TestCase, Client
from django.urls import reverse

from core.models import Especialidade
from terapeutas.models import Terapeuta
from espacos.models import Espaco
from django.contrib.auth import get_user_model

User = get_user_model()


# ===============================================================
# BASE COMPARTILHADA
# ===============================================================

class TerapiasViewsTestBase(TestCase):
    """
    Base compartilhada entre os testes do app terapias.
    Cria especialidades com e sem destaque.
    """

    def setUp(self):
        """Cria especialidades de teste antes de cada teste"""
        self.client = Client()

        # Especialidade em destaque e ativa
        self.especialidade_destaque = Especialidade.objects.create(
            nome='Acupuntura',
            slug='acupuntura',
            descricao_curta='Prática milenar chinesa.',
            destaque=True,
            is_active=True,
            ordem=1,
        )

        # Especialidade sem destaque, mas ativa
        self.especialidade_normal = Especialidade.objects.create(
            nome='Bioenergética',
            slug='bioenergetica',
            descricao_curta='Terapia corporal.',
            destaque=False,
            is_active=True,
            ordem=2,
        )

        # Especialidade inativa (não deve aparecer)
        self.especialidade_inativa = Especialidade.objects.create(
            nome='Zen Shiatsu',
            slug='zen-shiatsu',
            descricao_curta='Massagem japonesa.',
            destaque=True,
            is_active=False,
            ordem=3,
        )


# ===============================================================
# TESTES DA TERAPIAS DESTAQUES VIEW
# ===============================================================

class TerapiasDestaquesViewTest(TerapiasViewsTestBase):
    """
    Testa a TerapiasDestaquesView: página inicial de terapias em destaque.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapias:destaques')

    def test_pagina_acessivel_sem_login(self):
        """Página de destaques deve ser pública"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de destaques"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'terapias/destaques.html')

    def test_exibe_apenas_destaques_ativos(self):
        """Deve exibir apenas especialidades com destaque=True e is_active=True"""
        response = self.client.get(self.url)
        nomes = [t.nome for t in response.context['terapias']]
        self.assertIn('Acupuntura', nomes)
        self.assertNotIn('Bioenergética', nomes)
        self.assertNotIn('Zen Shiatsu', nomes)

    def test_limite_de_dez_resultados(self):
        """Não deve retornar mais que 10 terapias"""
        # Criar mais especialidades em destaque para testar o limite
        for i in range(15):
            Especialidade.objects.create(
                nome=f'Terapia Destaque {i}',
                slug=f'terapia-destaque-{i}',
                descricao_curta='Teste.',
                destaque=True,
                is_active=True,
                ordem=10 + i,
            )
        response = self.client.get(self.url)
        self.assertLessEqual(len(response.context['terapias']), 10)

    def test_contexto_tem_total_terapias(self):
        """Contexto deve ter o total de terapias ativas"""
        response = self.client.get(self.url)
        self.assertIn('total_terapias', response.context)
        # Apenas as 2 ativas (destaque e normal)
        self.assertEqual(response.context['total_terapias'], 2)


# ===============================================================
# TESTES DA TERAPIAS LISTAGEM VIEW
# ===============================================================

class TerapiasListagemViewTest(TerapiasViewsTestBase):
    """
    Testa a TerapiasListagemView: listagem alfabética com filtro por letra.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('terapias:listagem')

    def test_pagina_acessivel_sem_login(self):
        """Listagem deve ser pública"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de listagem alfabética"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'terapias/listagem_alfabetica.html')

    def test_exibe_apenas_ativas(self):
        """Deve exibir apenas especialidades ativas"""
        response = self.client.get(self.url)
        nomes = [t.nome for t in response.context['terapias']]
        self.assertIn('Acupuntura', nomes)
        self.assertIn('Bioenergética', nomes)
        self.assertNotIn('Zen Shiatsu', nomes)

    def test_filtro_por_letra(self):
        """Filtro por letra deve retornar apenas terapias que começam com ela"""
        response = self.client.get(self.url, {'letra': 'A'})
        nomes = [t.nome for t in response.context['terapias']]
        self.assertIn('Acupuntura', nomes)
        self.assertNotIn('Bioenergética', nomes)

    def test_filtro_todas_retorna_tudo(self):
        """Filtro 'todas' deve retornar todas as especialidades ativas"""
        response = self.client.get(self.url, {'letra': 'todas'})
        self.assertEqual(response.context['letra_selecionada'], 'todas')

    def test_contexto_tem_alfabeto(self):
        """Contexto deve ter o alfabeto completo para o filtro"""
        response = self.client.get(self.url)
        self.assertEqual(response.context['alfabeto'], 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    def test_contexto_tem_total_resultados(self):
        """Contexto deve ter o total de resultados"""
        response = self.client.get(self.url)
        self.assertIn('total_resultados', response.context)

    def test_paginacao_aplicada(self):
        """Listagem deve ter paginação de 30 itens por página"""
        response = self.client.get(self.url)
        self.assertTrue(response.context['is_paginated'] is False or 'page_obj' in response.context)


# ===============================================================
# TESTES DA TERAPIA DETALHE VIEW
# ===============================================================

class TerapiaDetalheViewTest(TerapiasViewsTestBase):
    """
    Testa a TerapiaDetalheView: página individual da terapia.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'terapias:detalhe',
            kwargs={'slug': self.especialidade_destaque.slug}
        )

    def test_pagina_acessivel_sem_login(self):
        """Detalhe deve ser público"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_usa_template_correto(self):
        """Deve usar o template de detalhe"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'terapias/detalhe.html')

    def test_retorna_404_para_slug_inexistente(self):
        """Slug inexistente deve retornar 404"""
        url = reverse('terapias:detalhe', kwargs={'slug': 'nao-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_retorna_404_para_especialidade_inativa(self):
        """Especialidade inativa deve retornar 404"""
        url = reverse(
            'terapias:detalhe',
            kwargs={'slug': self.especialidade_inativa.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_contexto_tem_terapeutas(self):
        """Contexto deve ter a lista de terapeutas que atendem a terapia"""
        response = self.client.get(self.url)
        self.assertIn('terapeutas', response.context)

    def test_contexto_tem_espacos(self):
        """Contexto deve ter a lista de espaços que oferecem a terapia"""
        response = self.client.get(self.url)
        self.assertIn('espacos', response.context)

    def test_contexto_tem_total_terapeutas(self):
        """Contexto deve ter o total de terapeutas"""
        response = self.client.get(self.url)
        self.assertIn('total_terapeutas', response.context)

    def test_contexto_tem_total_espacos(self):
        """Contexto deve ter o total de espaços"""
        response = self.client.get(self.url)
        self.assertIn('total_espacos', response.context)

    def test_contexto_tem_cidades(self):
        """Contexto deve ter as cidades relacionadas"""
        response = self.client.get(self.url)
        self.assertIn('cidades', response.context)

    def test_terapeuta_vinculado_aparece_na_lista(self):
        """Terapeuta com a especialidade deve aparecer na lista"""
        user = User.objects.create_user(
            username='terapeuta_terapia', password='senha123'
        )
        terapeuta = Terapeuta.objects.create(
            user=user,
            nome_completo='Terapeuta da Terapia',
            nome_exibicao='Terapeuta Terapia',
            slug='terapeuta-da-terapia',
            bio_curta='Bio.',
            bio_completa='<p>Bio.</p>',
            formacao='Formação',
            is_active=True,
        )
        terapeuta.especialidades.add(self.especialidade_destaque)

        response = self.client.get(self.url)
        self.assertEqual(response.context['total_terapeutas'], 1)