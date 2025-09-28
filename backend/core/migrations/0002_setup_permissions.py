# ===============================================================
# Título: Migration para Configurar Permissões - Espaço Vital
# Descrição: Migration que cria grupos e configura permissões automaticamente
# Autor: Will
# Data: 27/09/2025
# ===============================================================

from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def create_permissions_and_groups(apps, schema_editor):
    """
    Cria grupos e configura permissões do sistema
    """
    # Configuração dos grupos
    groups_config = {
        'Administradores': [
            # Terapeutas
            'terapeutas.add_terapeuta',
            'terapeutas.view_terapeuta', 
            'terapeutas.change_terapeuta',
            'terapeutas.delete_terapeuta',
            
            # Especialidades
            'terapeutas.add_especialidade',
            'terapeutas.view_especialidade',
            'terapeutas.change_especialidade', 
            'terapeutas.delete_especialidade',
            
            # Espaços (quando existir)
            'espacos.add_espaco',
            'espacos.view_espaco',
            'espacos.change_espaco',
            'espacos.delete_espaco',
            
            # Localização
            'terapeutas.add_cidade',
            'terapeutas.view_cidade',
            'terapeutas.change_cidade',
            'terapeutas.delete_cidade',
            'terapeutas.add_estado',
            'terapeutas.view_estado',
            'terapeutas.change_estado',
            'terapeutas.delete_estado',
            
            # Usuários e Grupos
            'auth.add_user',
            'auth.view_user',
            'auth.change_user',
            'auth.delete_user',
            'auth.add_group',
            'auth.view_group',
            'auth.change_group',
            'auth.delete_group',
            
            # Contatos e Avaliações
            'terapeutas.view_contato',
            'terapeutas.change_contato',
            'terapeutas.delete_contato',
            'terapeutas.view_avaliacao',
            'terapeutas.change_avaliacao',
            'terapeutas.delete_avaliacao',
        ],
        
        'Terapeutas': [
            # Perfil próprio (controlado por view)
            'terapeutas.view_terapeuta',
            'terapeutas.change_terapeuta',
            
            # Visualização de dados
            'terapeutas.view_especialidade',
            'terapeutas.view_cidade',
            'terapeutas.view_estado',
            
            # Próprias avaliações e contatos
            'terapeutas.view_avaliacao',
            'terapeutas.view_contato',
            'terapeutas.change_contato',
        ],
        
        'Gestores de Espaços': [
            # Gestão de espaços (controlado por view)
            'espacos.view_espaco',
            'espacos.change_espaco',
            
            # Visualização de dados relacionados
            'terapeutas.view_terapeuta',
            'terapeutas.view_especialidade',
            'terapeutas.view_cidade',
            'terapeutas.view_estado',
        ],
        
        'Editores de Conteúdo': [
            # Visualização para criação de conteúdo
            'terapeutas.view_terapeuta',
            'terapeutas.view_especialidade',
            'espacos.view_espaco',
        ]
    }
    
    # Criar grupos e atribuir permissões
    for group_name, permissions_list in groups_config.items():
        # Criar ou obter o grupo
        group, created = Group.objects.get_or_create(name=group_name)
        
        if created:
            print(f"✓ Grupo '{group_name}' criado")
        else:
            print(f"ℹ Grupo '{group_name}' já existe")
        
        # Limpar permissões existentes
        group.permissions.clear()
        
        # Adicionar permissões
        permissions_added = 0
        for perm_string in permissions_list:
            try:
                # Separar app_label.codename
                app_label, codename = perm_string.split('.', 1)
                
                # Buscar a permissão
                permission = Permission.objects.get(
                    codename=codename,
                    content_type__app_label=app_label
                )
                
                # Adicionar ao grupo
                group.permissions.add(permission)
                permissions_added += 1
                
            except Permission.DoesNotExist:
                print(f"⚠ Permissão '{perm_string}' não encontrada (pode ser criada posteriormente)")
            except Exception as e:
                print(f"❌ Erro ao processar '{perm_string}': {e}")
        
        print(f"✓ {permissions_added} permissões configuradas para '{group_name}'")

def reverse_permissions_and_groups(apps, schema_editor):
    """
    Remove os grupos criados (rollback)
    """
    group_names = ['Administradores', 'Terapeutas', 'Gestores de Espaços', 'Editores de Conteúdo']
    
    for group_name in group_names:
        try:
            group = Group.objects.get(name=group_name)
            group.delete()
            print(f"✓ Grupo '{group_name}' removido")
        except Group.DoesNotExist:
            print(f"ℹ Grupo '{group_name}' não existia")

class Migration(migrations.Migration):
    """
    Migration para configurar sistema de permissões
    """
    dependencies = [
        ('core', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),  # Garantir que auth está configurado
        ('contenttypes', '0002_remove_content_type_name'),  # Garantir que content types existem
    ]

    operations = [
        migrations.RunPython(
            create_permissions_and_groups,
            reverse_permissions_and_groups,
            hints={'ignore_not_found': True}
        ),
    ]