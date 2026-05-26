# ===============================================================
# Título: Migration Corrigida - Múltiplas Cidades
# Descrição: Migration correta para implementar múltiplas cidades
# ===============================================================

from django.db import migrations, models
import django.db.models.deletion


def migrar_cidades_existentes(apps, schema_editor):
    """
    Migra dados do campo cidade antigo para cidade_principal
    """
    Terapeuta = apps.get_model('terapeutas', 'Terapeuta')
    
    terapeutas_migrados = 0
    for terapeuta in Terapeuta.objects.all():
        if hasattr(terapeuta, 'cidade') and terapeuta.cidade:
            terapeuta.cidade_principal = terapeuta.cidade
            terapeuta.save()
            terapeutas_migrados += 1
    
    print(f"✅ Migrados dados de {terapeutas_migrados} terapeutas")


def reverter_migracao_cidades(apps, schema_editor):
    """
    Função reversa para desfazer a migração se necessário
    """
    Terapeuta = apps.get_model('terapeutas', 'Terapeuta')
    
    for terapeuta in Terapeuta.objects.all():
        if hasattr(terapeuta, 'cidade_principal') and terapeuta.cidade_principal:
            if hasattr(terapeuta, 'cidade'):
                terapeuta.cidade = terapeuta.cidade_principal
                terapeuta.save()


class Migration(migrations.Migration):
    """
    Migration para implementar múltiplas cidades de atendimento
    """

    dependencies = [
        ('terapeutas', '0001_initial'),
    ]

    operations = [
        # 1. Adicionar campo cidade_principal (temporariamente opcional)
        migrations.AddField(
            model_name='terapeuta',
            name='cidade_principal',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='terapeutas_principal',
                to='terapeutas.cidade',
                verbose_name='Cidade Principal',
                help_text='Cidade principal onde atua'
            ),
        ),
        
        # 2. Adicionar campo ManyToMany para cidades adicionais
        migrations.AddField(
            model_name='terapeuta',
            name='cidades_atendimento',
            field=models.ManyToManyField(
                blank=True,
                related_name='terapeutas_adicionais',
                to='terapeutas.cidade',
                verbose_name='Outras Cidades de Atendimento',
                help_text='Outras cidades onde também atende (além da principal)'
            ),
        ),
        
        # 3. Migrar dados do campo antigo para o novo
        migrations.RunPython(
            migrar_cidades_existentes,
            reverse_code=reverter_migracao_cidades
        ),
        
        # 4. Tornar cidade_principal obrigatório após migração
        migrations.AlterField(
            model_name='terapeuta',
            name='cidade_principal',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='terapeutas_principal',
                to='terapeutas.cidade',
                verbose_name='Cidade Principal',
                help_text='Cidade principal onde atua'
            ),
        ),
        
        # 5. Adicionar índices para performance
        migrations.AddIndex(
            model_name='terapeuta',
            index=models.Index(
                fields=['cidade_principal', 'is_active'], 
                name='terapeutas_cidade_principal_idx'
            ),
        ),
        
        # IMPORTANTE: 
        # Mantenha o campo 'cidade' antigo por enquanto para segurança
        # Remova apenas após confirmar que tudo funciona:
        # 
        # migrations.RemoveField(
        #     model_name='terapeuta',
        #     name='cidade',
        # ),
    ]