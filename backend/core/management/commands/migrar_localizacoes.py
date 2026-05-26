# ===============================================================
# Título: Comando para Migrar Estados e Cidades para Core
# Descrição: Migra dados de localização de terapeutas/espacos para core
# ===============================================================

from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps


class Command(BaseCommand):
    """
    Comando para migrar Estados e Cidades dos apps específicos para o core.
    Uso: python manage.py migrar_localizacoes
    """
    
    help = 'Migra Estados e Cidades de terapeutas para core'

    def handle(self, *args, **options):
        """
        Método principal que executa a migração de dados.
        """
        
        self.stdout.write(self.style.WARNING('🚀 Iniciando migração de Estados e Cidades...'))
        
        try:
            # Importar models antigos e novos
            EstadoAntigo = apps.get_model('terapeutas', 'Estado')
            CidadeAntiga = apps.get_model('terapeutas', 'Cidade')
            EstadoNovo = apps.get_model('core', 'Estado')
            CidadeNova = apps.get_model('core', 'Cidade')
            
            with transaction.atomic():
                # Mapeamento de IDs antigos para novos (para manter relacionamentos)
                mapa_estados = {}
                mapa_cidades = {}
                
                # ===== MIGRAR ESTADOS =====
                self.stdout.write(self.style.SUCCESS('\n📍 Migrando Estados...'))
                estados_antigos = EstadoAntigo.objects.all()
                
                for estado_antigo in estados_antigos:
                    # Verificar se já existe no core
                    estado_novo, created = EstadoNovo.objects.get_or_create(
                        sigla=estado_antigo.sigla,
                        defaults={
                            'nome': estado_antigo.nome,
                            'ativo': True
                        }
                    )
                    
                    # Mapear ID antigo -> ID novo
                    mapa_estados[estado_antigo.id] = estado_novo.id
                    
                    if created:
                        self.stdout.write(f'  ✅ Estado migrado: {estado_novo.nome} ({estado_novo.sigla})')
                    else:
                        self.stdout.write(f'  ⚠️  Estado já existe: {estado_novo.nome} ({estado_novo.sigla})')
                
                # ===== MIGRAR CIDADES =====
                self.stdout.write(self.style.SUCCESS('\n🏙️  Migrando Cidades...'))
                cidades_antigas = CidadeAntiga.objects.all().select_related('estado')
                
                for cidade_antiga in cidades_antigas:
                    # Pegar o novo estado correspondente
                    novo_estado_id = mapa_estados.get(cidade_antiga.estado_id)
                    
                    if not novo_estado_id:
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Estado não encontrado para cidade: {cidade_antiga.nome}')
                        )
                        continue
                    
                    novo_estado = EstadoNovo.objects.get(id=novo_estado_id)
                    
                    # Verificar se já existe no core
                    cidade_nova, created = CidadeNova.objects.get_or_create(
                        nome=cidade_antiga.nome,
                        estado=novo_estado,
                        defaults={
                            'ativo': True
                        }
                    )
                    
                    # Mapear ID antigo -> ID novo
                    mapa_cidades[cidade_antiga.id] = cidade_nova.id
                    
                    if created:
                        self.stdout.write(f'  ✅ Cidade migrada: {cidade_nova.nome} - {cidade_nova.estado.sigla}')
                
                # ===== RESUMO =====
                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('📊 RESUMO DA MIGRAÇÃO'))
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write(f'  Total de Estados no Core: {EstadoNovo.objects.count()}')
                self.stdout.write(f'  Total de Cidades no Core: {CidadeNova.objects.count()}')
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Migração concluída com sucesso!\n')
                )
                
                # Salvar mapeamento para referência
                self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANTE:'))
                self.stdout.write('Agora você precisa:')
                self.stdout.write('1. Atualizar as ForeignKeys em Terapeuta para apontar para core.Cidade')
                self.stdout.write('2. Atualizar as ForeignKeys em Espaco para apontar para core.Cidade')
                self.stdout.write('3. Remover os models Estado e Cidade de terapeutas e espacos\n')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Erro ao migrar dados: {str(e)}\n')
            )
            raise