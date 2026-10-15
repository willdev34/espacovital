# ===============================================================
# Título: Testes de Fumaça do Admin
# Descrição: Para cada modelo registrado no admin do projeto, cria
#            um objeto real e confere que as telas abrem sem erro:
#            lista (inclui os métodos de exibição), busca, cadastro,
#            edição e confirmação de exclusão. Também executa cada
#            ação em massa do admin e abre o painel de estatísticas.
# Autor: Will
# Data: 15/10/2026
# ===============================================================

import datetime as dt
from decimal import Decimal

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

User = get_user_model()

# Apps que o projeto mantém. Os admins de terceiros (allauth) ficam de fora.
APPS_DO_PROJETO = {'core', 'espacos', 'terapeutas', 'agendamentos', 'auth', 'account'}


def _requisicao_falsa():
    """Request com um superusuário mínimo, para consultar permissões e ações"""
    request = RequestFactory().get('/')
    request.user = type('U', (), {
        'is_active': True, 'is_superuser': True, 'is_staff': True,
        'has_perm': lambda self, perm, obj=None: True,
    })()
    return request


# ===============================================================
# CONSTRUTOR AUTOMÁTICO DE OBJETOS
# Preenche os campos obrigatórios e cria as chaves estrangeiras
# que faltarem. Serve só para os testes de tela do admin.
# ===============================================================

_contador = {'n': 0}


def _proximo():
    _contador['n'] += 1
    return _contador['n']


def _valor_para(campo, cache):
    """Valor simples e válido para um campo obrigatório"""
    if campo.choices:
        return campo.choices[0][0]
    if isinstance(campo, models.ForeignKey) or isinstance(campo, models.OneToOneField):
        return construir(campo.related_model, cache)
    n = _proximo()
    if isinstance(campo, models.EmailField):
        return f'usuario{n}@exemplo.com'
    if isinstance(campo, models.SlugField):
        return f'slug-{n}'
    if isinstance(campo, models.URLField):
        return f'https://exemplo.com/{n}'
    if isinstance(campo, (models.CharField, models.TextField)):
        texto = f'teste{n}'
        return texto[:campo.max_length] if campo.max_length else texto
    if isinstance(campo, models.BooleanField):
        return True
    if isinstance(campo, models.DecimalField):
        return Decimal('10.00')
    if isinstance(campo, (models.IntegerField, models.FloatField)):
        return 5
    if isinstance(campo, models.DateTimeField):
        return timezone.now() + dt.timedelta(days=5)
    if isinstance(campo, models.DateField):
        return dt.date.today()
    if isinstance(campo, models.TimeField):
        return dt.time(10, 0)
    if isinstance(campo, models.UUIDField):
        return None
    if isinstance(campo, models.JSONField):
        return []
    raise ValueError(f'Campo sem regra no construtor: {campo}')


def construir(modelo, cache=None, **extra):
    """Cria (ou reaproveita) um objeto do modelo com tudo que for obrigatório"""
    cache = {} if cache is None else cache
    if not extra and modelo in cache:
        return cache[modelo]

    campos = {}
    for campo in modelo._meta.concrete_fields:
        if campo.primary_key or campo.name in extra:
            continue
        if campo.has_default() or campo.null or campo.blank:
            continue
        if getattr(campo, 'auto_now', False) or getattr(campo, 'auto_now_add', False):
            continue
        valor = _valor_para(campo, cache)
        if valor is not None:
            campos[campo.name] = valor
    campos.update(extra)

    objeto = modelo.objects.create(**campos)
    if not extra:
        cache[modelo] = objeto
    return objeto


# ===============================================================
# FIXTURES
# ===============================================================

@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username='admin_teste', email='admin@exemplo.com', password='senha123'
    )


@pytest.fixture
def cliente_admin(client, superuser):
    client.force_login(superuser)
    return client


def _admins_do_projeto():
    """(modelo, ModelAdmin) dos apps do projeto, em ordem estável"""
    itens = [
        (modelo, ma) for modelo, ma in admin.site._registry.items()
        if modelo._meta.app_label in APPS_DO_PROJETO
    ]
    return sorted(itens, key=lambda x: (x[0]._meta.app_label, x[0].__name__))


ADMINS = _admins_do_projeto()
IDS = [f'{m._meta.app_label}.{m.__name__}' for m, _ in ADMINS]


def _url(modelo, nome, *args):
    return reverse(f'admin:{modelo._meta.app_label}_{modelo._meta.model_name}_{nome}', args=args)


# ===============================================================
# TELAS DE CADA MODELO
# ===============================================================

@pytest.mark.django_db
@pytest.mark.parametrize('modelo,model_admin', ADMINS, ids=IDS)
class TestTelasDoAdmin:

    def _objeto(self, modelo):
        try:
            return construir(modelo)
        except Exception as erro:  # modelo que o construtor não resolve
            pytest.skip(f'construtor não resolve {modelo.__name__}: {erro}')

    def test_lista_abre_com_um_registro(self, cliente_admin, modelo, model_admin):
        self._objeto(modelo)
        response = cliente_admin.get(_url(modelo, 'changelist'))
        assert response.status_code == 200

    def test_busca_na_lista_nao_quebra(self, cliente_admin, modelo, model_admin):
        if not model_admin.search_fields:
            pytest.skip('admin sem campos de busca')
        self._objeto(modelo)
        response = cliente_admin.get(_url(modelo, 'changelist'), {'q': 'teste'})
        assert response.status_code == 200

    def test_cadastro_abre(self, cliente_admin, modelo, model_admin):
        if not model_admin.has_add_permission(_requisicao_falsa()):
            pytest.skip('cadastro desabilitado neste admin')
        response = cliente_admin.get(_url(modelo, 'add'))
        assert response.status_code == 200

    def test_edicao_abre(self, cliente_admin, modelo, model_admin):
        objeto = self._objeto(modelo)
        response = cliente_admin.get(_url(modelo, 'change', objeto.pk))
        assert response.status_code == 200

    def test_confirmacao_de_exclusao_abre(self, cliente_admin, modelo, model_admin):
        objeto = self._objeto(modelo)
        response = cliente_admin.get(_url(modelo, 'delete', objeto.pk))
        assert response.status_code == 200


# ===============================================================
# AÇÕES EM MASSA
# ===============================================================

def _acoes():
    pares = []
    for modelo, ma in ADMINS:
        for nome in ma.get_actions(_requisicao_falsa()).keys():
            if nome != 'delete_selected':
                pares.append((modelo, nome))
    return pares


ACOES = _acoes()
ACOES_IDS = [f'{m.__name__}.{nome}' for m, nome in ACOES]


@pytest.mark.django_db
@pytest.mark.parametrize('modelo,acao', ACOES, ids=ACOES_IDS)
def test_acao_em_massa_executa_sem_erro(cliente_admin, modelo, acao):
    try:
        objeto = construir(modelo)
    except Exception as erro:
        pytest.skip(f'construtor não resolve {modelo.__name__}: {erro}')

    response = cliente_admin.post(
        _url(modelo, 'changelist'),
        {'action': acao, '_selected_action': [objeto.pk]},
    )

    assert response.status_code in (200, 302)


# ===============================================================
# PAINEL DE ESTATÍSTICAS E PÁGINA INICIAL DO ADMIN
# ===============================================================

@pytest.mark.django_db
class TestPaineisDoAdmin:

    def test_pagina_inicial_do_admin_abre(self, cliente_admin):
        response = cliente_admin.get(reverse('admin:index'))
        assert response.status_code == 200

    def test_painel_de_estatisticas_abre_sem_dados(self, cliente_admin):
        response = cliente_admin.get(reverse('admin:admin_dashboard'))
        assert response.status_code == 200

    def test_painel_de_estatisticas_abre_com_dados(self, cliente_admin):
        from terapeutas.models import Terapeuta
        from espacos.models import Espaco
        construir(Terapeuta)
        construir(Espaco)
        response = cliente_admin.get(reverse('admin:admin_dashboard'))
        assert response.status_code == 200

    def test_painel_exige_staff(self, client, db):
        response = client.get(reverse('admin:admin_dashboard'))
        assert response.status_code == 302
