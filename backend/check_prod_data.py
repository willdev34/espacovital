# ===============================================================
# Título: Verificar Dados de Produção
# Descrição: Script para verificar dados no banco de produção
# ===============================================================

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'espacovital.settings')
django.setup()

from core.models import Pais, Estado, Cidade, Especialidade
from terapeutas.models import Terapeuta

print("=" * 60)
print("🔍 VERIFICANDO DADOS DE PRODUÇÃO")
print("=" * 60)

# Verifica dados de localização
print(f"\n📍 LOCALIZAÇÃO:")
print(f"   - Países: {Pais.objects.count()}")
print(f"   - Estados: {Estado.objects.count()}")
print(f"   - Cidades: {Cidade.objects.count()}")

# Verifica especialidades
print(f"\n💆 ESPECIALIDADES:")
print(f"   - Total: {Especialidade.objects.count()}")

# Verifica terapeutas
print(f"\n👤 TERAPEUTAS:")
print(f"   - Total: {Terapeuta.objects.count()}")

print("\n" + "=" * 60)