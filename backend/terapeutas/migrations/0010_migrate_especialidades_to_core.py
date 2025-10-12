# ===============================================================
# Título: Migration para migrar Especialidades para Core
# Descrição: Copia dados de terapeutas.Especialidade para core.Especialidade
# Autor: Will
# Data: 12/10/2025
# ===============================================================

from django.db import migrations


def migrate_especialidades_to_core(apps, schema_editor):
    """
    Migra todas as especialidades de terapeutas para core
    Preserva todos os campos e IDs
    """
    # Pegar os models usando apps.get_model() para usar versão histórica
    TerapeutaEspecialidade = apps.get_model('terapeutas', 'Especialidade')
    CoreEspecialidade = apps.get_model('core', 'Especialidade')
    
    # Copiar todas as especialidades
    especialidades_to_create = []
    
    for esp in TerapeutaEspecialidade.objects.all():
        especialidades_to_create.append(
            CoreEspecialidade(
                id=esp.id,
                nome=esp.nome,
                slug=esp.slug,
                descricao_curta=esp.descricao_curta if hasattr(esp, 'descricao_curta') else '',
                descricao_completa=esp.descricao_completa if hasattr(esp, 'descricao_completa') else '',
                categoria=esp.categoria if hasattr(esp, 'categoria') else '',
                cor_destaque=esp.cor_destaque if hasattr(esp, 'cor_destaque') else '#6C63FF',
                ordem=esp.ordem if hasattr(esp, 'ordem') else 0,
                destaque=esp.destaque if hasattr(esp, 'destaque') else False,
                is_active=esp.is_active if hasattr(esp, 'is_active') else True,
                created_at=esp.created_at,
                updated_at=esp.updated_at,
            )
        )
    
    # Criar todas de uma vez (bulk_create)
    if especialidades_to_create:
        CoreEspecialidade.objects.bulk_create(especialidades_to_create)
        print(f"✓ {len(especialidades_to_create)} especialidades migradas de terapeutas para core")


def reverse_migrate(apps, schema_editor):
    """
    Reverte a migração (se necessário fazer rollback)
    """
    CoreEspecialidade = apps.get_model('core', 'Especialidade')
    CoreEspecialidade.objects.all().delete()
    print("✓ Especialidades removidas de core")


class Migration(migrations.Migration):
    """
    Migration customizada para migrar dados de especialidades
    """

    dependencies = [
        ('terapeutas', '0009_terapeuta_estado'),
        ('core', '0006_especialidade'),
    ]

    operations = [
        migrations.RunPython(
            migrate_especialidades_to_core,
            reverse_migrate
        ),
    ]