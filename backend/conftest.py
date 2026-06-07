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