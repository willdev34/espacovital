# ===============================================================
# Título: Testes Unitários - Views do App Terapias
# Descrição: Testa respostas HTTP das views de listagem
#            e detalhe de terapias
# ===============================================================

import pytest
from django.urls import reverse
from core.models import Especialidade


# ---------------------------------------------------------------
# Testes da view de listagem de terapias
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestTerapiasListView:

    def test_listagem_retorna_200(self, client_anonimo):
        # quando a página de listagem é acessada
        url = reverse('terapias:listagem')
        response = client_anonimo.get(url)

        # então deve retornar 200
        assert response.status_code == 200

    def test_listagem_exibe_especialidades_ativas(self, client_anonimo):
        # dado especialidades ativas e inativas no banco
        Especialidade.objects.create(nome='Reiki Ativo', is_active=True)
        Especialidade.objects.create(nome='Reiki Inativo', is_active=False)

        url = reverse('terapias:listagem')
        response = client_anonimo.get(url)

        # então apenas a ativa deve aparecer na resposta
        assert 'Reiki Ativo' in response.content.decode()
        assert 'Reiki Inativo' not in response.content.decode()


# ---------------------------------------------------------------
# Testes da view de detalhe de terapia
# ---------------------------------------------------------------
@pytest.mark.django_db
class TestTerapiaDetalheView:

    def test_detalhe_retorna_200_para_slug_valido(self, client_anonimo):
        # dado uma especialidade existente
        Especialidade.objects.create(nome='Yoga', slug='yoga')

        url = reverse('terapias:detalhe', kwargs={'slug': 'yoga'})
        response = client_anonimo.get(url)

        # então deve retornar 200
        assert response.status_code == 200

    def test_detalhe_retorna_404_para_slug_inexistente(self, client_anonimo):
        # quando um slug inválido é acessado
        url = reverse('terapias:detalhe', kwargs={'slug': 'nao-existe'})
        response = client_anonimo.get(url)

        # então deve retornar 404
        assert response.status_code == 404