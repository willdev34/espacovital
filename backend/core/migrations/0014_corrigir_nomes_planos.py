# ===============================================================
# Título: Data Migration - Corrigir nomes dos planos para minúsculas
# Descrição: Atualiza os nomes dos planos criados com maiúsculas
# ===============================================================

from django.db import migrations


def corrigir_nomes(apps, schema_editor):
    """Corrige os nomes dos planos de maiúsculas para minúsculas"""
    Plano = apps.get_model('core', 'Plano')

    # Mapeamento: nome errado -> nome correto
    correcoes = {
        'GRATUITO_FILIADO': 'gratuito_filiado',
        'BASIC': 'basic',
        'PREMIUM_A': 'premium_a',
        'PREMIUM_S': 'premium_s',
        'PREMIUM_S_PLUS': 'premium_s_plus',
        'COMBO_A_S': 'combo_a_s',
        'COMBO_A_S_PLUS': 'combo_a_s_plus',
    }

    for nome_errado, nome_correto in correcoes.items():
        Plano.objects.filter(nome=nome_errado).update(nome=nome_correto)


def reverter_nomes(apps, schema_editor):
    """Reverte os nomes para maiúsculas"""
    Plano = apps.get_model('core', 'Plano')

    correcoes = {
        'gratuito_filiado': 'GRATUITO_FILIADO',
        'basic': 'BASIC',
        'premium_a': 'PREMIUM_A',
        'premium_s': 'PREMIUM_S',
        'premium_s_plus': 'PREMIUM_S_PLUS',
        'combo_a_s': 'COMBO_A_S',
        'combo_a_s_plus': 'COMBO_A_S_PLUS',
    }

    for nome_errado, nome_correto in correcoes.items():
        Plano.objects.filter(nome=nome_errado).update(nome=nome_correto)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_criar_planos_iniciais'),
    ]

    operations = [
        migrations.RunPython(corrigir_nomes, reverter_nomes),
    ]