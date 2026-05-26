#!/usr/bin/env python
# ===============================================================
# Título: Diagnóstico UTF-8 - Espaço Vital
# Descrição: Identifica problemas de encoding no Windows
# ===============================================================

import os
import sys
import locale

print("=" * 70)
print("🔍 DIAGNÓSTICO COMPLETO UTF-8 - ESPAÇO VITAL")
print("=" * 70)

# 1. Sistema Operacional e Python
print("\n1️⃣ INFORMAÇÕES DO SISTEMA:")
print(f"   - Sistema Operacional: {sys.platform}")
print(f"   - Versão Python: {sys.version}")
print(f"   - Encoding padrão: {sys.getdefaultencoding()}")
print(f"   - Encoding stdout: {sys.stdout.encoding}")
print(f"   - Encoding stderr: {sys.stderr.encoding}")
print(f"   - Encoding filesystem: {sys.getfilesystemencoding()}")

# 2. Locale do sistema
print("\n2️⃣ LOCALE DO SISTEMA:")
try:
    print(f"   - Locale atual: {locale.getlocale()}")
    print(f"   - Locale preferido: {locale.getpreferredencoding()}")
except Exception as e:
    print(f"   ⚠️  Erro ao obter locale: {e}")

# 3. Variáveis de Ambiente Python
print("\n3️⃣ VARIÁVEIS DE AMBIENTE PYTHON:")
env_vars = [
    'PYTHONUTF8',
    'PYTHONIOENCODING',
    'PYTHONLEGACYWINDOWSSTDIO',
    'LANG',
    'LC_ALL',
    'LC_CTYPE'
]
for var in env_vars:
    value = os.environ.get(var, '❌ NÃO DEFINIDA')
    print(f"   - {var}: {value}")

# 4. Variáveis do PostgreSQL
print("\n4️⃣ VARIÁVEIS DO POSTGRESQL:")
pg_vars = [
    'PGHOST',
    'PGPORT',
    'PGUSER',
    'PGPASSWORD',
    'PGDATABASE',
    'PGDATA',
    'PGSYSCONFDIR',
    'PGSERVICEFILE',
    'PGPASSFILE'
]
for var in pg_vars:
    value = os.environ.get(var, '❌ NÃO DEFINIDA')
    if 'PASSWORD' in var and value != '❌ NÃO DEFINIDA':
        value = '***OCULTO***'
    print(f"   - {var}: {value}")

# 5. Caminho do usuário (pode ter acentos!)
print("\n5️⃣ CAMINHOS DO SISTEMA:")
print(f"   - HOME: {os.environ.get('HOME', os.environ.get('USERPROFILE', 'N/A'))}")
print(f"   - USERNAME: {os.environ.get('USERNAME', os.environ.get('USER', 'N/A'))}")
print(f"   - PWD: {os.getcwd()}")

# Verifica se tem acentos no caminho
current_path = os.getcwd()
user_home = os.environ.get('HOME', os.environ.get('USERPROFILE', ''))

print("\n6️⃣ VERIFICAÇÃO DE CARACTERES ESPECIAIS:")
for path_name, path_value in [('Diretório atual', current_path), ('HOME', user_home)]:
    try:
        path_value.encode('ascii')
        print(f"   ✅ {path_name}: SEM caracteres especiais")
    except UnicodeEncodeError:
        print(f"   ⚠️  {path_name}: CONTÉM caracteres especiais!")
        print(f"      Caminho: {path_value}")

# 7. Testa carregar .env
print("\n7️⃣ TESTANDO CARREGAMENTO DO .ENV:")
try:
    from decouple import config
    print("   ✅ python-decouple importado com sucesso")
    
    # Tenta carregar variáveis
    db_name = config('DB_NAME', default='não configurado')
    db_user = config('DB_USER', default='não configurado')
    db_host = config('DB_HOST', default='não configurado')
    
    print(f"   - DB_NAME: {db_name}")
    print(f"   - DB_USER: {db_user}")
    print(f"   - DB_HOST: {db_host}")
    
    # Verifica encoding das strings
    for var_name, var_value in [('DB_NAME', db_name), ('DB_USER', db_user), ('DB_HOST', db_host)]:
        if isinstance(var_value, bytes):
            print(f"   ⚠️  {var_name} está como BYTES! Precisa decodificar!")
        else:
            try:
                var_value.encode('utf-8')
                print(f"   ✅ {var_name}: UTF-8 OK")
            except Exception as e:
                print(f"   ❌ {var_name}: ERRO UTF-8 - {e}")
                
except ImportError:
    print("   ❌ python-decouple não instalado!")
except Exception as e:
    print(f"   ❌ Erro ao carregar .env: {type(e).__name__}: {e}")

# 8. Testa conexão PostgreSQL
print("\n8️⃣ TESTANDO CONEXÃO POSTGRESQL:")
try:
    import psycopg2
    print("   ✅ psycopg2 importado")
    
    from decouple import config
    
    # Pega credenciais
    db_params = {
        'dbname': config('DB_NAME', default='espacovital_dev'),
        'user': config('DB_USER', default='espacovital_user'),
        'password': config('DB_PASSWORD', default='espacovital_pass_2025'),
        'host': config('DB_HOST', default='localhost'),
        'port': config('DB_PORT', default='5432'),
    }
    
    print(f"   Tentando conectar em: {db_params['user']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}")
    
    # Força client_encoding
    db_params['options'] = '-c client_encoding=UTF8'
    
    conn = psycopg2.connect(**db_params)
    print("   ✅ CONEXÃO ESTABELECIDA!")
    
    cursor = conn.cursor()
    cursor.execute("SHOW server_encoding;")
    server_encoding = cursor.fetchone()[0]
    print(f"   - Server Encoding: {server_encoding}")
    
    cursor.execute("SHOW client_encoding;")
    client_encoding = cursor.fetchone()[0]
    print(f"   - Client Encoding: {client_encoding}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ TODOS OS TESTES PASSARAM!")
    
except ImportError as e:
    print(f"   ❌ Erro ao importar: {e}")
except Exception as e:
    print(f"   ❌ ERRO NA CONEXÃO:")
    print(f"      Tipo: {type(e).__name__}")
    print(f"      Mensagem: {str(e)}")
    
    if isinstance(e, UnicodeDecodeError):
        print(f"\n   🔍 DETALHES DO ERRO UNICODE:")
        print(f"      - Encoding: {e.encoding}")
        print(f"      - Posição do erro: {e.start}-{e.end}")
        print(f"      - Byte problemático: {hex(e.object[e.start])}")
        print(f"      - Objeto sendo decodificado: {e.object[:100]}...")

print("\n" + "=" * 70)
print("💡 RECOMENDAÇÕES:")
print("=" * 70)

# Recomendações baseadas no que encontramos
if sys.platform == 'win32':
    print("\n📌 WINDOWS DETECTADO - Verifique:")
    print("   1. Nome de usuário do Windows tem acentos? (ex: 'José', 'André')")
    print("   2. PostgreSQL instalado em 'C:\\Program Files'? (tem espaço!)")
    print("   3. Variáveis PGDATA/PGHOST definidas com acentos?")
    print("\n🔧 SOLUÇÕES:")
    print("   • Use Docker para PostgreSQL (já está usando!)")
    print("   • Garanta que .env está em UTF-8")
    print("   • Execute: chcp 65001 no CMD antes de rodar o servidor")
    
print("\n" + "=" * 70)