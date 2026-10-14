# ===============================================================
# Título: Fixtures Globais de Teste - Espaço Vital
# Descrição: Fixtures compartilhadas entre todos os apps.
#            Disponível automaticamente para qualquer teste
#            sem necessidade de importação.
# ===============================================================

import pytest
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------
# Fixture: cliente HTTP sem autenticação
# Uso: def test_algo(client_anonimo): ...
# ---------------------------------------------------------------
@pytest.fixture
def client_anonimo():
    return Client()


# ---------------------------------------------------------------
# Fixture: usuário comum criado no banco de teste
# Uso: def test_algo(usuario_comum): ...
# ---------------------------------------------------------------
@pytest.fixture
def usuario_comum(db):
    return User.objects.create_user(
        username='usuario_teste',
        email='usuario@teste.com',
        password='senha_teste_123',
    )


# ---------------------------------------------------------------
# Fixture: usuário administrador criado no banco de teste
# Uso: def test_algo(usuario_admin): ...
# ---------------------------------------------------------------
@pytest.fixture
def usuario_admin(db):
    return User.objects.create_superuser(
        username='admin_teste',
        email='admin@teste.com',
        password='senha_admin_123',
    )


# ---------------------------------------------------------------
# Fixture: cliente HTTP autenticado como usuário comum
# Uso: def test_algo(client_autenticado): ...
# ---------------------------------------------------------------
@pytest.fixture
def client_autenticado(usuario_comum):
    client = Client()
    client.force_login(usuario_comum)
    return client


# ---------------------------------------------------------------
# Fixture: cliente HTTP autenticado como admin
# Uso: def test_algo(client_admin): ...
# ---------------------------------------------------------------
@pytest.fixture
def client_admin(usuario_admin):
    client = Client()
    client.force_login(usuario_admin)
    return client


# ---------------------------------------------------------------
# Fixture autouse: hasher de senha rápido SÓ nos testes
# O PBKDF2 padrão do Django leva ~0,37s por senha e cada teste cria
# usuários e faz login. O MD5 é inseguro: por isso fica restrito a
# este conftest e nunca entra no settings.py de produção.
# Obs.: não vale para setUpTestData (roda antes dos fixtures).
# ---------------------------------------------------------------
@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]


# ---------------------------------------------------------------
# Fixture autouse: armazenamento de estáticos simples SÓ nos testes
# O settings usa o WhiteNoise em modo manifesto, que exige o
# staticfiles.json gerado pelo collectstatic: sem ele, qualquer
# {% static %} de arquivo novo levanta ValueError. O projeto usa
# STATICFILES_STORAGE (Django 4.2), então trocamos essa chave.
# O StaticFilesStorage só monta a URL, sem consultar manifesto.
# Produção e Vercel continuam com o WhiteNoise (settings.py intacto).
# ---------------------------------------------------------------
@pytest.fixture(autouse=True)
def estaticos_simples(settings):
    settings.STATICFILES_STORAGE = (
        'django.contrib.staticfiles.storage.StaticFilesStorage'
    )


# ---------------------------------------------------------------
# Hook: aplica os markers unit e integration pelo caminho do teste
# Testes em pasta "integration" recebem @pytest.mark.integration
# Testes em pasta "unit" recebem @pytest.mark.unit
# Assim não precisamos editar cada arquivo de teste
# ---------------------------------------------------------------
def pytest_collection_modifyitems(items):
    for item in items:
        pastas = item.path.parts
        if 'integration' in pastas:
            item.add_marker(pytest.mark.integration)
        elif 'unit' in pastas:
            item.add_marker(pytest.mark.unit)
