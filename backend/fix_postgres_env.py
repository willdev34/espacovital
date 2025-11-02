# ===============================================================
# Título: Fix PostgreSQL Environment - Espaço Vital
# Descrição: Remove variáveis de ambiente problemáticas do PostgreSQL
# Autor: Will
# Data: 01/11/2025
# ===============================================================

import os
import sys

print("=" * 60)
print("🔧 LIMPANDO VARIÁVEIS DE AMBIENTE DO POSTGRESQL")
print("=" * 60)

# Lista de variáveis PostgreSQL que podem causar problemas
pg_vars = []
for key in list(os.environ.keys()):
    if any(x in key.upper() for x in ['PG', 'POSTGRES']):
        pg_vars.append(key)

if pg_vars:
    print(f"\n📋 Variáveis PostgreSQL encontradas:")
    for var in pg_vars:
        print(f"   - {var} = {os.environ[var][:50]}...")
    
    print(f"\n🗑️  Removendo variáveis...")
    for var in pg_vars:
        del os.environ[var]
    print(f"   ✅ {len(pg_vars)} variáveis removidas!")
else:
    print(f"\n✅ Nenhuma variável PostgreSQL encontrada no ambiente")

# Define variáveis limpas
os.environ['PGCLIENTENCODING'] = 'UTF8'
print(f"\n✅ PGCLIENTENCODING definido como UTF8")

print("=" * 60)

# Agora testa a conexão
print("\n🔄 Testando conexão...")

import psycopg2
from decouple import config

try:
    conn = psycopg2.connect(
        dbname=config('DB_NAME', default='espacovital'),
        user=config('DB_USER', default='postgres'),
        password=config('DB_PASSWORD', default='postgres'),
        host=config('DB_HOST', default='localhost'),
        port=config('DB_PORT', default='5432'),
        client_encoding='UTF8'
    )
    
    print("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
    
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f"\nPostgreSQL Version: {version[0][:50]}...")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERRO: {type(e).__name__}")
    print(f"   {str(e)}")

print("=" * 60)