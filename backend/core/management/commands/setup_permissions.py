# ===============================================================
# Título: Comando para Configurar Permissões - Espaço Vital
# Descrição: Management command para criar grupos e permissões
# Autor: Will
# Data: 27/09/2025
# ===============================================================

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.permissions import create_groups_and_permissions, GROUPS_CONFIG

class Command(BaseCommand):
    """
    Command para configurar grupos e permissões do sistema
    Uso: python manage.py setup_permissions
    """
    help = 'Configura grupos de usuários e permissões do sistema'

    def add_arguments(self, parser):
        """
        Adiciona argumentos opcionais ao comando
        """
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remove todos os grupos existentes antes de criar novos',
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true', 
            help='Exibe informações detalhadas sobre o processo',
        )

    def handle(self, *args, **options):
        """
        Executa o comando
        """
        verbose = options['verbose']
        reset = options['reset']
        
        self.stdout.write(
            self.style.SUCCESS('🔧 Configurando Sistema de Permissões - Espaço Vital')
        )
        
        if reset:
            self.stdout.write(
                self.style.WARNING('⚠ Removendo grupos existentes...')
            )
            # Remove apenas os grupos que estão na nossa configuração
            for group_name in GROUPS_CONFIG.keys():
                try:
                    group = Group.objects.get(name=group_name)
                    group.delete()
                    if verbose:
                        self.stdout.write(f"  ❌ Grupo '{group_name}' removido")
                except Group.DoesNotExist:
                    if verbose:
                        self.stdout.write(f"  ℹ Grupo '{group_name}' não existia")
        
        # Criar grupos e permissões
        self.stdout.write('📝 Criando grupos e configurando permissões...')
        
        try:
            create_groups_and_permissions()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Sistema de permissões configurado com sucesso!')
            )
            
            # Exibir resumo
            self.stdout.write('\n📊 Resumo dos Grupos Criados:')
            for group_name, config in GROUPS_CONFIG.items():
                try:
                    group = Group.objects.get(name=group_name)
                    perm_count = group.permissions.count()
                    
                    self.stdout.write(
                        f"  🏷 {group_name}: {perm_count} permissões"
                    )
                    
                    if verbose:
                        self.stdout.write(f"     📋 {config['description']}")
                        
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Erro: Grupo '{group_name}' não foi criado")
                    )
            
            # Instruções finais
            self.stdout.write('\n📌 Próximos passos:')
            self.stdout.write('   1. Acesse o admin Django')
            self.stdout.write('   2. Vá em "Autenticação e Autorização" > "Usuários"')
            self.stdout.write('   3. Edite um usuário e atribua-o a um grupo')
            self.stdout.write('   4. Salve e teste as permissões')
            
            self.stdout.write(
                f'\n🌐 Acesse: http://localhost:8000/admin/auth/user/'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao configurar permissões: {str(e)}')
            )
            raise e