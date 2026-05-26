# ===============================================================
# Título: Comando para corrigir slugs de Especialidades
# Descrição: Gera slugs para especialidades que não possuem
# ===============================================================

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Especialidade

class Command(BaseCommand):
    help = 'Corrige slugs faltantes nas Especialidades'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('🔧 CORRIGINDO SLUGS DE ESPECIALIDADES')
        self.stdout.write('=' * 60)
        
        # Busca especialidades sem slug ou com slug vazio
        especialidades_sem_slug = Especialidade.objects.filter(
            slug__isnull=True
        ) | Especialidade.objects.filter(slug='')
        
        total = especialidades_sem_slug.count()
        
        if total == 0:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Todas as especialidades já possuem slug!')
            )
            return
        
        self.stdout.write(f'\n📋 Encontradas {total} especialidade(s) sem slug\n')
        
        corrigidas = 0
        for esp in especialidades_sem_slug:
            slug_original = esp.slug
            
            # Gera slug baseado no nome
            base_slug = slugify(esp.nome)
            slug = base_slug
            counter = 1
            
            # Garante slug único
            while Especialidade.objects.filter(slug=slug).exclude(pk=esp.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            esp.slug = slug
            esp.save()
            
            self.stdout.write(
                f'  ✅ {esp.nome}: "{slug_original or "(vazio)"}" → "{slug}"'
            )
            corrigidas += 1
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'✅ {corrigidas} especialidade(s) corrigida(s) com sucesso!')
        )
        self.stdout.write('=' * 60)