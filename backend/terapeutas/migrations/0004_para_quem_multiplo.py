# ===============================================================
# Título: Migration - Para Quem Múltiplo (VERSÃO FINAL)
# Descrição: Altera campo para_quem de CharField para JSONField usando SQL
# Autor: Will
# Data: 28/09/2025
# ===============================================================

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('terapeutas', '0003_remove_terapeuta_terapeutas__cidade__8466f0_idx_and_more'),
    ]

    operations = [
        # ETAPA 1: Adicionar novo campo JSONField temporário
        migrations.AddField(
            model_name='terapeuta',
            name='para_quem_novo',
            field=models.JSONField(
                default=list,
                help_text='Público-alvo dos atendimentos (múltipla seleção)',
                verbose_name='Para Quem Novo',
                null=True,
                blank=True
            ),
        ),
        
        # ETAPA 2: Copiar dados do campo antigo para o novo usando SQL
        migrations.RunSQL(
            # Converter string para array JSON
            sql="""
                UPDATE terapeutas_terapeuta 
                SET para_quem_novo = 
                    CASE 
                        WHEN para_quem IS NULL OR para_quem = '' THEN '[]'::jsonb
                        ELSE jsonb_build_array(para_quem)
                    END;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        
        # ETAPA 3: Remover campo antigo
        migrations.RemoveField(
            model_name='terapeuta',
            name='para_quem',
        ),
        
        # ETAPA 4: Renomear campo novo para o nome original
        migrations.RenameField(
            model_name='terapeuta',
            old_name='para_quem_novo',
            new_name='para_quem',
        ),
        
        # ETAPA 5: Ajustar o campo para remover null e blank
        migrations.AlterField(
            model_name='terapeuta',
            name='para_quem',
            field=models.JSONField(
                default=list,
                help_text='Público-alvo dos atendimentos (múltipla seleção): adultos, criancas, idosos, casais, grupos',
                verbose_name='Para Quem'
            ),
        ),
    ]