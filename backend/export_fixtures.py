# ===============================================================
# Script - Export Fixtures
# Descrição: Exporta fixtures com encoding UTF-8 correto
# Autor: Will
# Data: 17/10/2025
# ===============================================================

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'espacovital.settings')
django.setup()

from django.core.management import call_command

fixtures = {
    'users.json': ['auth.User'],
    'especialidades.json': ['core.Especialidade'],
    'terapeutas.json': ['terapeutas.Terapeuta'],
    'espacos.json': ['espacos.Espaco'],
}

for filename, models in fixtures.items():
    filepath = os.path.join('fixtures', filename)
    print(f'Exportando {filename}...')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        call_command('dumpdata', *models, indent=2, stdout=f)
    
    print(f'✅ {filename} exportado com sucesso!')

print('\n🎉 Todos os fixtures exportados!')