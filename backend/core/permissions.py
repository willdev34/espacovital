# ===============================================================
# Título: Sistema de Permissões Personalizadas - Espaço Vital
# Descrição: Configurações de permissões traduzidas e intuitivas
# Autor: Will
# Data: 27/09/2025
# ===============================================================

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

# ===============================================================
# DICIONÁRIO DE TRADUÇÃO DAS PERMISSÕES
# ===============================================================

PERMISSIONS_TRANSLATION = {
    # Permissões de Terapeutas
    'terapeutas.add_terapeuta': 'Cadastrar Terapeutas',
    'terapeutas.view_terapeuta': 'Visualizar Terapeutas',
    'terapeutas.change_terapeuta': 'Editar Terapeutas',
    'terapeutas.delete_terapeuta': 'Excluir Terapeutas',
    
    # Permissões de Especialidades
    'terapeutas.add_especialidade': 'Cadastrar Especialidades',
    'terapeutas.view_especialidade': 'Visualizar Especialidades',
    'terapeutas.change_especialidade': 'Editar Especialidades',
    'terapeutas.delete_especialidade': 'Excluir Especialidades',
    
    # Permissões de Cidades
    'terapeutas.add_cidade': 'Cadastrar Cidades',
    'terapeutas.view_cidade': 'Visualizar Cidades',
    'terapeutas.change_cidade': 'Editar Cidades',
    'terapeutas.delete_cidade': 'Excluir Cidades',
    
    # Permissões de Estados
    'terapeutas.add_estado': 'Cadastrar Estados',
    'terapeutas.view_estado': 'Visualizar Estados',
    'terapeutas.change_estado': 'Editar Estados',
    'terapeutas.delete_estado': 'Excluir Estados',
    
    # Permissões de Contatos (Terapeutas)
    'terapeutas.view_contato': 'Visualizar Contatos de Terapeutas',
    'terapeutas.change_contato': 'Responder Contatos de Terapeutas',
    'terapeutas.delete_contato': 'Excluir Contatos de Terapeutas',
    
    # Permissões de Avaliações
    'terapeutas.view_avaliacao': 'Visualizar Avaliações',
    'terapeutas.change_avaliacao': 'Moderar Avaliações',
    'terapeutas.delete_avaliacao': 'Excluir Avaliações',
    
    # Permissões do Core
    'core.add_contact': 'Criar Formulários de Contato',
    'core.view_contact': 'Visualizar Formulários de Contato',
    'core.change_contact': 'Editar Formulários de Contato',
    'core.delete_contact': 'Excluir Formulários de Contato',
    
    'core.view_newsletter': 'Visualizar Newsletter',
    'core.change_newsletter': 'Gerenciar Newsletter',
    'core.delete_newsletter': 'Excluir Inscrições Newsletter',
    
    'core.add_faq': 'Criar FAQs',
    'core.view_faq': 'Visualizar FAQs',
    'core.change_faq': 'Editar FAQs',
    'core.delete_faq': 'Excluir FAQs',
    
    'core.view_siteconfiguration': 'Visualizar Configurações do Site',
    'core.change_siteconfiguration': 'Editar Configurações do Site',
    
    # Permissões do Sistema
    'auth.add_user': 'Cadastrar Usuários',
    'auth.view_user': 'Visualizar Usuários',
    'auth.change_user': 'Editar Usuários',
    'auth.delete_user': 'Excluir Usuários',
    
    'auth.add_group': 'Criar Grupos de Permissão',
    'auth.view_group': 'Visualizar Grupos de Permissão',
    'auth.change_group': 'Editar Grupos de Permissão',
    'auth.delete_group': 'Excluir Grupos de Permissão',
}

# ===============================================================
# CONFIGURAÇÃO DOS GRUPOS DE USUÁRIOS
# ===============================================================

GROUPS_CONFIG = {
    'Administradores': {
        'description': 'Acesso total ao sistema - podem gerenciar tudo',
        'permissions': [
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
            
            # Contatos e Avaliações (terapeutas)
            'terapeutas.view_contato',
            'terapeutas.change_contato',
            'terapeutas.delete_contato',
            'terapeutas.view_avaliacao',
            'terapeutas.change_avaliacao',
            'terapeutas.delete_avaliacao',
            
            # Core
            'core.add_contact',
            'core.view_contact',
            'core.change_contact',
            'core.delete_contact',
            'core.view_newsletter',
            'core.change_newsletter',
            'core.delete_newsletter',
            'core.view_faq',
            'core.change_faq',
            'core.add_faq',
            'core.delete_faq',
            'core.view_siteconfiguration',
            'core.change_siteconfiguration',
        ]
    },
    
    'Terapeutas': {
        'description': 'Profissionais que podem gerenciar seus próprios perfis',
        'permissions': [
            # Pode visualizar e editar apenas seu próprio perfil
            'terapeutas.view_terapeuta',
            'terapeutas.change_terapeuta',  # Limitado ao próprio perfil
            
            # Pode visualizar especialidades existentes
            'terapeutas.view_especialidade',
            
            # Pode visualizar cidades para atendimento
            'terapeutas.view_cidade',
            'terapeutas.view_estado',
            
            # Pode ver suas próprias avaliações
            'terapeutas.view_avaliacao',
            
            # Pode ver contatos direcionados a ele
            'terapeutas.view_contato',
            'terapeutas.change_contato',  # Responder contatos
        ]
    },
    
    'Gestores de Espaços': {
        'description': 'Responsáveis por espaços terapêuticos',
        'permissions': [
            # Visualização de dados relacionados
            'terapeutas.view_terapeuta',
            'terapeutas.view_especialidade',
            'terapeutas.view_cidade',
            'terapeutas.view_estado',
        ]
    },
    
    'Editores de Conteúdo': {
        'description': 'Responsáveis pelo blog e conteúdo educativo',
        'permissions': [
            # Visualização para criação de conteúdo
            'terapeutas.view_terapeuta',
            'terapeutas.view_especialidade',
            
            # Core content
            'core.add_faq',
            'core.view_faq',
            'core.change_faq',
            'core.delete_faq',
            'core.view_contact',
        ]
    }
}

# ===============================================================
# FUNÇÕES UTILITÁRIAS
# ===============================================================

def create_groups_and_permissions():
    """
    Cria os grupos e atribui as permissões definidas
    Deve ser executado nas migrations ou management command
    """
    for group_name, config in GROUPS_CONFIG.items():
        # Criar ou obter o grupo
        group, created = Group.objects.get_or_create(name=group_name)
        
        if created:
            print(f"✓ Grupo '{group_name}' criado")
        
        # Limpar permissões existentes
        group.permissions.clear()
        
        # Adicionar permissões definidas
        for perm_codename in config['permissions']:
            try:
                # Separar app_label.codename
                app_label, codename = perm_codename.split('.', 1)
                
                # Buscar a permissão
                permission = Permission.objects.get(
                    codename=codename,
                    content_type__app_label=app_label
                )
                
                # Adicionar ao grupo
                group.permissions.add(permission)
                
            except Permission.DoesNotExist:
                print(f"⚠ Permissão '{perm_codename}' não encontrada")
            except Exception as e:
                print(f"❌ Erro ao processar '{perm_codename}': {e}")
        
        print(f"✓ Permissões configuradas para '{group_name}'")

def get_translated_permission_name(permission):
    """
    Retorna o nome traduzido da permissão
    """
    codename = f"{permission.content_type.app_label}.{permission.codename}"
    return PERMISSIONS_TRANSLATION.get(codename, permission.name)

def get_user_permissions_summary(user):
    """
    Retorna um resumo das permissões do usuário
    """
    permissions = []
    
    # Permissões diretas
    for perm in user.user_permissions.all():
        permissions.append({
            'name': get_translated_permission_name(perm),
            'source': 'Direto'
        })
    
    # Permissões via grupos
    for group in user.groups.all():
        for perm in group.permissions.all():
            permissions.append({
                'name': get_translated_permission_name(perm),
                'source': f'Grupo: {group.name}'
            })
    
    return permissions

def assign_user_to_group(user, group_name):
    """
    Atribui um usuário a um grupo específico
    """
    try:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return True, f"Usuário adicionado ao grupo '{group_name}'"
    except Group.DoesNotExist:
        return False, f"Grupo '{group_name}' não encontrado"

def is_admin_user(user):
    """
    Verifica se o usuário é administrador
    """
    return user.is_superuser or user.groups.filter(name='Administradores').exists()

def is_therapist_user(user):
    """
    Verifica se o usuário é terapeuta
    """
    return user.groups.filter(name='Terapeutas').exists()

def is_space_manager_user(user):
    """
    Verifica se o usuário é gestor de espaços
    """
    return user.groups.filter(name='Gestores de Espaços').exists()