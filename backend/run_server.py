# ===============================================================
# Titulo: Run Server - Espaco Vital  
# Descricao: Script para iniciar servidor com limpeza de variaveis
# ===============================================================

import os
import sys
import subprocess

print("=" * 60)
print("🚀 INICIANDO SERVIDOR ESPACO VITAL")
print("=" * 60)

# PASSO 1: FORCA UTF-8 ANTES DE TUDO
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'C.UTF-8'
    os.environ['LC_ALL'] = 'C.UTF-8'
    print("\n✅ UTF-8 forcado no sistema")

# PASSO 2: REMOVE TODAS AS VARIAVEIS POSTGRESQL DO SISTEMA
print("\n🧹 Limpando variaveis PostgreSQL do sistema...")
removed_vars = []
for key in list(os.environ.keys()):
    # Remove QUALQUER variavel relacionada ao PostgreSQL
    if any(x in key.upper() for x in ['PG', 'POSTGRES']):
        removed_vars.append(key)
        del os.environ[key]

if removed_vars:
    print(f"   🗑️  Removidas {len(removed_vars)} variaveis:")
    for var in removed_vars[:5]:  # Mostra apenas as primeiras 5
        print(f"      - {var}")
    if len(removed_vars) > 5:
        print(f"      ... e mais {len(removed_vars) - 5}")
else:
    print("   ✅ Nenhuma variavel PostgreSQL encontrada")

# PASSO 3: DEFINE VARIAVEIS LIMPAS PARA DOCKER
print("\n🐳 Configurando variaveis para Docker PostgreSQL...")
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'
print("   ✅ Variaveis Docker configuradas")

# PASSO 4: VERIFICA SE DOCKER ESTA RODANDO
print("\n🔍 Verificando Docker PostgreSQL...")
try:
    result = subprocess.run(
        ['docker', 'ps', '--filter', 'name=espacovital-postgres', '--format', '{{.Status}}'],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if 'Up' in result.stdout:
        print("   ✅ Docker PostgreSQL esta rodando!")
    else:
        print("   ⚠️  Docker PostgreSQL NAO esta rodando!")
        print("   💡 Execute: docker-compose up -d")
        sys.exit(1)
        
except Exception as e:
    print(f"   ⚠️  Nao foi possivel verificar Docker: {e}")
    print("   💡 Certifique-se que o Docker esta instalado e rodando")

# PASSO 5: INICIA O SERVIDOR DJANGO
print("\n🚀 Iniciando servidor Django...")
print("=" * 60)
print()

# Chama o manage.py com as variaveis limpas
os.system('python manage.py runserver')