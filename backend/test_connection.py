# -*- coding: utf-8 -*-
import os
import sys

# REMOVE TODAS as variaveis do PostgreSQL local
for key in list(os.environ.keys()):
    if 'PG' in key.upper() or 'POSTGRES' in key.upper():
        del os.environ[key]

# Define SOMENTE as variaveis do Docker
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Agora importa o psycopg2
import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        dbname='espacovital',
        options='-c client_encoding=UTF8'
    )
    print('✅ CONECTADO COM SUCESSO!')
    conn.close()
except Exception as e:
    print(f'❌ ERRO: {e}')
    import traceback
    traceback.print_exc()