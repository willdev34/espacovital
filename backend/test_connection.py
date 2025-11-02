# ===============================================================
# Título: Test Connection - Diagnóstico de Conexão
# Descrição: Script para testar conexão com PostgreSQL
# Autor: Will
# Data: 01/11/2025
# ===============================================================

import os
import sys

# Força UTF-8
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

print("=" * 60)
print("🔍 DIAGNÓSTICO DE CONEXÃO - ESPAÇO VITAL")
print("=" * 60)

# 1. Verifica encoding do sistema
print(f"\n1️⃣ Encoding do Sistema:")
print(f"   - sys.stdout.encoding: {sys.stdout.encoding}")
print(f"   - sys.getdefaultencoding(): {sys.getdefaultencoding()}")
print(f"   - Plataforma: {sys.platform}")

# 2. Verifica variáveis de ambiente
print(f"\n2️⃣ Variáveis de Ambiente:")
env_vars = ['PYTHONUTF8', 'PYTHONIOENCODING', 'DB_NAME', 'DB_USER', 'DB_HOST', 'DB_PORT']
for var in env_vars:
    value = os.environ.get(var, 'NÃO DEFINIDA')
    # Esconde senha se existir
    if 'PASSWORD' in var and value != 'NÃO DEFINIDA':
        value = '*' * len(value)
    print(f"   - {var}: {value}")

# 3. Testa import do psycopg2
print(f"\n3️⃣ Testando psycopg2:")
try:
    import psycopg2
    print(f"   ✅ psycopg2 importado com sucesso!")
    print(f"   - Versão: {psycopg2.__version__}")
except ImportError as e:
    print(f"   ❌ Erro ao importar psycopg2: {e}")
    sys.exit(1)

# 4. Testa conexão com PostgreSQL
print(f"\n4️⃣ Testando Conexão com PostgreSQL:")

# Carrega variáveis do .env se existir
try:
    from decouple import config
    DB_NAME = config('DB_NAME', default='espacovital')
    DB_USER = config('DB_USER', default='postgres')
    DB_PASSWORD = config('DB_PASSWORD', default='postgres')
    DB_HOST = config('DB_HOST', default='localhost')
    DB_PORT = config('DB_PORT', default='5432')
    print(f"   ✅ Variáveis carregadas do .env")
except:
    DB_NAME = 'espacovital'
    DB_USER = 'postgres'
    DB_PASSWORD = 'postgres'
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    print(f"   ⚠️  Usando valores padrão (sem .env)")

print(f"   - Banco: {DB_NAME}")
print(f"   - Usuário: {DB_USER}")
print(f"   - Host: {DB_HOST}")
print(f"   - Porta: {DB_PORT}")

try:
    # FORÇA encoding UTF-8 nas variáveis ANTES de conectar
    if isinstance(DB_NAME, bytes):
        DB_NAME = DB_NAME.decode('utf-8')
    if isinstance(DB_USER, bytes):
        DB_USER = DB_USER.decode('utf-8')
    if isinstance(DB_PASSWORD, bytes):
        DB_PASSWORD = DB_PASSWORD.decode('utf-8')
    if isinstance(DB_HOST, bytes):
        DB_HOST = DB_HOST.decode('utf-8')
    
    print(f"\n   🔄 Método 1: Connection String Manual...")
    
    # Método 1: Connection string manual
    try:
        connection_string = (
            f"dbname='{DB_NAME}' "
            f"user='{DB_USER}' "
            f"password='{DB_PASSWORD}' "
            f"host='{DB_HOST}' "
            f"port='{DB_PORT}' "
            f"client_encoding='UTF8'"
        )
        conn = psycopg2.connect(connection_string)
        print(f"   ✅ Sucesso com connection string!")
        
    except UnicodeDecodeError:
        print(f"   ❌ Falhou - tentando Método 2...")
        
        # Método 2: Limpar TODAS as variáveis de ambiente do PostgreSQL
        # Remove variáveis que podem ter caminhos com acentos
        for key in list(os.environ.keys()):
            if 'PG' in key.upper() or 'POSTGRES' in key.upper():
                del os.environ[key]
        
        # Força variáveis limpas
        os.environ['PGCLIENTENCODING'] = 'UTF8'
        
        print(f"   🔄 Método 2: Parâmetros diretos sem env vars...")
        
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            options='-c client_encoding=UTF8'
        )
        print(f"   ✅ Sucesso com parâmetros diretos!")
    
    print(f"\n   ✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
    
    # Testa query simples
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f"   - PostgreSQL Version: {version[0][:50]}...")
    
    cursor.close()
    conn.close()
    print(f"\n✅ TODOS OS TESTES PASSARAM!")
    
except Exception as e:
    print(f"\n   ❌ ERRO NA CONEXÃO:")
    print(f"   - Tipo: {type(e).__name__}")
    print(f"   - Mensagem: {str(e)}")
    
    # Debug adicional para UnicodeDecodeError
    if isinstance(e, UnicodeDecodeError):
        print(f"\n   🔍 DETALHES DO ERRO UNICODE:")
        print(f"   - Encoding: {e.encoding}")
        print(f"   - Posição: {e.start}-{e.end}")
        print(f"   - Byte problemático: {hex(e.object[e.start])}")
        
        print(f"\n   💡 O problema está nas configurações do PostgreSQL no Windows!")
        print(f"   📁 Verifique se há acentos nesses locais:")
        print(f"      - C:\\Program Files\\PostgreSQL\\...")
        print(f"      - C:\\Users\\{os.getlogin()}\\AppData\\...")
        print(f"      - Variáveis PGDATA, PGHOST, etc.")
    
    print(f"\n💡 POSSÍVEIS SOLUÇÕES:")
    print(f"   1. Verifique se o PostgreSQL está rodando")
    print(f"   2. Reinstale PostgreSQL em caminho SEM acentos")
    print(f"   3. Use Docker para PostgreSQL")
    print(f"   4. Configure PostgreSQL para escutar em 127.0.0.1")

print("=" * 60)