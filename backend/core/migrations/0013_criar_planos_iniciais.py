# ===============================================================
# Título: Data Migration - Criar Planos de Assinatura
# Descrição: Cria os planos padrão do sistema automaticamente no deploy
# ===============================================================

from django.db import migrations


def criar_planos(apps, schema_editor):
    """Cria os planos padrão do sistema"""
    Plano = apps.get_model('core', 'Plano')

    planos_data = [
        {
            'nome': 'GRATUITO_FILIADO',
            'nome_exibicao': 'Gratuito Filiado',
            'descricao': 'Plano gratuito para terapeutas vinculados a espaços.',
            'valor': 0.00,
            'dias_trial': 0,
            'destaque_busca': False,
            'badge_verificado': False,
            'estatisticas_avancadas': False,
            'suporte_prioritario': False,
            'limite_fotos': 1,
            'vinculos_espacos': 1,
            'gerenciamento_salas': False,
            'divulgacao_perfil': False,
            'max_usuarios': None,
            'ordem_exibicao': 1,
            'recomendado': False
        },
        {
            'nome': 'BASIC',
            'nome_exibicao': 'Basic',
            'descricao': 'Plano básico para terapeutas. Perfil público com funcionalidades essenciais.',
            'valor': 9.00,
            'dias_trial': 15,
            'destaque_busca': False,
            'badge_verificado': False,
            'estatisticas_avancadas': False,
            'suporte_prioritario': False,
            'limite_fotos': 3,
            'vinculos_espacos': 2,
            'gerenciamento_salas': False,
            'divulgacao_perfil': True,
            'max_usuarios': None,
            'ordem_exibicao': 2,
            'recomendado': False
        },
        {
            'nome': 'PREMIUM_A',
            'nome_exibicao': 'Premium A',
            'descricao': 'Plano premium para terapeutas. Destaque nas buscas e suporte prioritário.',
            'valor': 49.90,
            'dias_trial': 15,
            'destaque_busca': True,
            'badge_verificado': True,
            'estatisticas_avancadas': True,
            'suporte_prioritario': True,
            'limite_fotos': 10,
            'vinculos_espacos': 5,
            'gerenciamento_salas': False,
            'divulgacao_perfil': True,
            'max_usuarios': 100,
            'ordem_exibicao': 3,
            'recomendado': True
        },
        {
            'nome': 'PREMIUM_S',
            'nome_exibicao': 'Premium S',
            'descricao': 'Plano premium para espaços terapêuticos.',
            'valor': 99.90,
            'dias_trial': 15,
            'destaque_busca': True,
            'badge_verificado': True,
            'estatisticas_avancadas': True,
            'suporte_prioritario': True,
            'limite_fotos': 15,
            'vinculos_espacos': 0,
            'gerenciamento_salas': False,
            'divulgacao_perfil': True,
            'max_usuarios': 50,
            'ordem_exibicao': 4,
            'recomendado': False
        },
        {
            'nome': 'PREMIUM_S_PLUS',
            'nome_exibicao': 'Premium S+',
            'descricao': 'Plano premium avançado para espaços com gerenciamento completo de salas.',
            'valor': 129.90,
            'dias_trial': 15,
            'destaque_busca': True,
            'badge_verificado': True,
            'estatisticas_avancadas': True,
            'suporte_prioritario': True,
            'limite_fotos': 20,
            'vinculos_espacos': 0,
            'gerenciamento_salas': True,
            'divulgacao_perfil': True,
            'max_usuarios': 30,
            'ordem_exibicao': 5,
            'recomendado': False
        },
        {
            'nome': 'COMBO_A_S',
            'nome_exibicao': 'Combo Premium A + S',
            'descricao': 'Combo completo para quem é terapeuta e tem espaço.',
            'valor': 139.90,
            'dias_trial': 15,
            'destaque_busca': True,
            'badge_verificado': True,
            'estatisticas_avancadas': True,
            'suporte_prioritario': True,
            'limite_fotos': 20,
            'vinculos_espacos': 5,
            'gerenciamento_salas': False,
            'divulgacao_perfil': True,
            'max_usuarios': 20,
            'ordem_exibicao': 6,
            'recomendado': False
        },
        {
            'nome': 'COMBO_A_S_PLUS',
            'nome_exibicao': 'Combo Premium A + S+',
            'descricao': 'Combo máximo! Terapeuta + Espaço com gerenciamento completo de salas.',
            'valor': 159.90,
            'dias_trial': 15,
            'destaque_busca': True,
            'badge_verificado': True,
            'estatisticas_avancadas': True,
            'suporte_prioritario': True,
            'limite_fotos': 25,
            'vinculos_espacos': 5,
            'gerenciamento_salas': True,
            'divulgacao_perfil': True,
            'max_usuarios': 10,
            'ordem_exibicao': 7,
            'recomendado': False
        },
    ]

    for plano_data in planos_data:
        Plano.objects.update_or_create(
            nome=plano_data['nome'],
            defaults=plano_data
        )


def remover_planos(apps, schema_editor):
    """Reverte a migration removendo os planos"""
    Plano = apps.get_model('core', 'Plano')
    nomes = [
        'GRATUITO_FILIADO', 'BASIC', 'PREMIUM_A', 'PREMIUM_S',
        'PREMIUM_S_PLUS', 'COMBO_A_S', 'COMBO_A_S_PLUS'
    ]
    Plano.objects.filter(nome__in=nomes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_plano_nome'),
    ]

    operations = [
        migrations.RunPython(criar_planos, remover_planos),
    ]