# ===============================================================
# Título: Run Server - Espaço Vital  
# Descrição: Script para iniciar servidor com limpeza de variáveis
# Autor: Will
# Data: 08/11/2025
# ===============================================================

import os
import sys
import subprocess

print("=" * 60)
print("🚀 INICIANDO SERVIDOR ESPAÇO VITAL")
print("=" * 60)

# ⚠️ PASSO 1: FORÇA UTF-8 ANTES DE TUDO
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'C.UTF-8'
    os.environ['LC_ALL'] = 'C.UTF-8'
    print("\n✅ UTF-8 forçado no sistema")

# ⚠️ PASSO 2: REMOVE TODAS AS VARIÁVEIS POSTGRESQL DO SISTEMA
print("\n🧹 Limpando variáveis PostgreSQL do sistema...")
removed_vars = []
for key in list(os.environ.keys()):
    # Remove QUALQUER variável relacionada ao PostgreSQL
    if any(x in key.upper() for x in ['PG', 'POSTGRES']):
        removed_vars.append(key)
        del os.environ[key]

if removed_vars:
    print(f"   🗑️  Removidas {len(removed_vars)} variáveis:")
    for var in removed_vars[:5]:  # Mostra apenas as primeiras 5
        print(f"      - {var}")
    if len(removed_vars) > 5:
        print(f"      ... e mais {len(removed_vars) - 5}")
else:
    print("   ✅ Nenhuma variável PostgreSQL encontrada")

# ⚠️ PASSO 3: DEFINE VARIÁVEIS LIMPAS PARA DOCKER
print("\n🐳 Configurando variáveis para Docker PostgreSQL...")
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'
print("   ✅ Variáveis Docker configuradas")

# ⚠️ PASSO 4: VERIFICA SE DOCKER ESTÁ RODANDO
print("\n🔍 Verificando Docker PostgreSQL...")
try:
    result = subprocess.run(
        ['docker', 'ps', '--filter', 'name=espacovital_postgres', '--format', '{{.Status}}'],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if 'Up' in result.stdout:
        print("   ✅ Docker PostgreSQL está rodando!")
    else:
        print("   ⚠️  Docker PostgreSQL NÃO está rodando!")
        print("   💡 Execute: docker-compose up -d")
        sys.exit(1)
        
except Exception as e:
    print(f"   ⚠️  Não foi possível verificar Docker: {e}")
    print("   💡 Certifique-se que o Docker está instalado e rodando")

# ⚠️ PASSO 5: INICIA O SERVIDOR DJANGO
print("\n🚀 Iniciando servidor Django...")
print("=" * 60)
print()

# Chama o manage.py com as variáveis limpas
os.system('python manage.py runserver')