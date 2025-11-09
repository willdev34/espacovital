# ===============================================================
# Título: Corrigir Sequences do PostgreSQL
# Descrição: Reseta sequences de IDs após importação de dados
# Autor: Will
# Data: 09/11/2025
# ===============================================================

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Corrige sequences do PostgreSQL após importação de dados'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('🔧 CORRIGINDO SEQUENCES DO POSTGRESQL')
        self.stdout.write('=' * 60)
        
        with connection.cursor() as cursor:
            # Lista de tabelas para corrigir
            tabelas = [
                'core_especialidade',
                'core_pais',
                'core_estado',
                'core_cidade',
                'terapeutas_terapeuta',
                'espacos_espaco',
                'espacos_comodidade',
            ]
            
            corrigidas = 0
            
            for tabela in tabelas:
                try:
                    # Corrige a sequence de cada tabela
                    cursor.execute(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{tabela}', 'id'),
                            COALESCE((SELECT MAX(id) FROM {tabela}), 1),
                            true
                        );
                    """)
                    
                    result = cursor.fetchone()
                    new_value = result[0] if result else 0
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ {tabela}: sequence ajustada para {new_value}')
                    )
                    corrigidas += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  {tabela}: {str(e)}')
                    )
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'✅ {corrigidas} sequence(s) corrigida(s)!')
        )
        self.stdout.write('=' * 60)