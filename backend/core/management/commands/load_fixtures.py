# ===============================================================
# Management Command - Load Fixtures
# Descrição: Carrega fixtures de dados no banco
# ===============================================================

from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = 'Carrega todos os fixtures de dados'

    def load_fixture_with_encoding(self, fixture_path):
        """
        Carrega fixture forçando encoding UTF-8
        """
        import json
        from django.core import serializers
        
        # Ler o arquivo com encoding UTF-8 forçado
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Desserializar os objetos
        objects = serializers.deserialize('json', json.dumps(data))
        
        # Salvar os objetos
        for obj in objects:
            obj.save()

    def handle(self, *args, **options):
        """
        Carrega os fixtures na ordem correta para evitar erros de dependência
        """
        # Lista de fixtures na ordem correta
        fixtures = [
            ('paises.json', 'Países'),
            ('estados.json', 'Estados'),
            ('cidades.json', 'Cidades'),
            ('users.json', 'Usuários'),
            ('especialidades.json', 'Especialidades'),
            ('terapeutas.json', 'Terapeutas'),
            ('espacos.json', 'Espaços'),
        ]

        self.stdout.write(self.style.SUCCESS('🚀 Iniciando carga de fixtures...'))
        
        for fixture_file, description in fixtures:
            # Detectar o caminho base do backend
            # __file__ está em: backend/core/management/commands/load_fixtures.py
            # Precisamos subir 4 níveis para chegar em backend/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            fixture_path = os.path.join(base_dir, 'fixtures', fixture_file)
            
            # Verificar se o arquivo existe
            if not os.path.exists(fixture_path):
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Arquivo não encontrado: {fixture_path}')
                )
                continue
            
            # Carregar o fixture
            self.stdout.write(f'📦 Carregando {description}...')
            try:
                self.load_fixture_with_encoding(fixture_path)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {description} carregado com sucesso!')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao carregar {description}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Carga de fixtures concluída!'))