# ===============================================================
# Título: Management Command - Upgrade de Plano
# Descrição: Atualiza ou cria assinatura Premium S+ para testes
# ===============================================================

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import Assinatura, Plano


class Command(BaseCommand):
    """
    Management command para fazer upgrade de plano de um usuário.
    
    Uso:
        python manage.py upgrade_plano --usuario=admin --plano=premium_s_plus
        python manage.py upgrade_plano --usuario=admin --plano=combo_a_s_plus
    """
    
    help = 'Atualiza ou cria assinatura de plano para um usuário'
    
    def add_arguments(self, parser):
        """
        Define os argumentos do comando
        """
        parser.add_argument(
            '--usuario',
            type=str,
            required=True,
            help='Username do usuário que receberá o plano'
        )
        
        parser.add_argument(
            '--plano',
            type=str,
            default='premium_s_plus',
            help='Nome do plano (premium_s_plus, combo_a_s_plus, etc)'
        )
        
        parser.add_argument(
            '--dias-trial',
            type=int,
            default=30,
            help='Quantidade de dias de trial gratuito (padrão: 30)'
        )
    
    def handle(self, *args, **options):
        """
        Executa o comando
        """
        username = options['usuario']
        plano_nome = options['plano']
        dias_trial = options['dias_trial']
        
        # ===== BUSCAR USUÁRIO =====
        try:
            usuario = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuário encontrado: {usuario.username} (ID: {usuario.id})')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Usuário "{username}" não encontrado!')
            )
            return
        
        # ===== BUSCAR PLANO =====
        try:
            plano = Plano.objects.get(nome=plano_nome, is_active=True)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Plano encontrado: {plano.nome_exibicao} (R$ {plano.valor})')
            )
            self.stdout.write(
                self.style.WARNING(f'   → Gerenciamento de Salas: {"SIM" if plano.gerenciamento_salas else "NÃO"}')
            )
        except Plano.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Plano "{plano_nome}" não encontrado ou não está ativo!')
            )
            self.stdout.write(
                self.style.WARNING('Planos disponíveis:')
            )
            for p in Plano.objects.filter(is_active=True):
                self.stdout.write(f'   - {p.nome} ({p.nome_exibicao})')
            return
        
        # ===== VERIFICAR ASSINATURA EXISTENTE =====
        assinatura_existente = Assinatura.objects.filter(usuario=usuario).first()
        
        if assinatura_existente:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Assinatura existente encontrada (ID: {assinatura_existente.id})')
            )
            self.stdout.write(
                self.style.WARNING(f'   Plano atual: {assinatura_existente.plano.nome_exibicao}')
            )
            self.stdout.write(
                self.style.WARNING(f'   Status atual: {assinatura_existente.status}')
            )
        
        # ===== CONFIRMAR AÇÃO =====
        if assinatura_existente:
            confirmacao = input(f'\n🔄 Deseja ATUALIZAR a assinatura para {plano.nome_exibicao}? (s/n): ')
        else:
            confirmacao = input(f'\n➕ Deseja CRIAR nova assinatura {plano.nome_exibicao}? (s/n): ')
        
        if confirmacao.lower() != 's':
            self.stdout.write(self.style.WARNING('❌ Operação cancelada!'))
            return
        
        # ===== CALCULAR DATAS =====
        data_inicio = timezone.now()
        data_fim_trial = data_inicio + timedelta(days=dias_trial)
        
        # ===== ATUALIZAR OU CRIAR ASSINATURA =====
        if assinatura_existente:
            # Atualizar assinatura existente
            assinatura_existente.plano = plano
            assinatura_existente.status = 'active'
            assinatura_existente.data_inicio = data_inicio
            assinatura_existente.data_fim_trial = data_fim_trial
            assinatura_existente.is_active = True
            assinatura_existente.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Assinatura ATUALIZADA com sucesso!')
            )
            acao = 'ATUALIZADA'
            assinatura = assinatura_existente
            
        else:
            # Criar nova assinatura
            assinatura = Assinatura.objects.create(
                usuario=usuario,
                plano=plano,
                status='active',
                data_inicio=data_inicio,
                data_fim_trial=data_fim_trial,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Assinatura CRIADA com sucesso!')
            )
            acao = 'CRIADA'
        
        # ===== RESUMO FINAL =====
        self.stdout.write(
            self.style.SUCCESS('\n' + '='*60)
        )
        self.stdout.write(
            self.style.SUCCESS(f'📋 RESUMO DA ASSINATURA {acao}')
        )
        self.stdout.write(
            self.style.SUCCESS('='*60)
        )
        self.stdout.write(f'👤 Usuário: {usuario.username}')
        self.stdout.write(f'📦 Plano: {plano.nome_exibicao}')
        self.stdout.write(f'💰 Valor: R$ {plano.valor}/mês')
        self.stdout.write(f'📅 Data Início: {data_inicio.strftime("%d/%m/%Y %H:%M")}')
        self.stdout.write(f'🎁 Trial até: {data_fim_trial.strftime("%d/%m/%Y")} ({dias_trial} dias)')
        self.stdout.write(f'✅ Status: {assinatura.status.upper()}')
        self.stdout.write(f'🏢 Gerenciamento de Salas: {"✅ SIM" if plano.gerenciamento_salas else "❌ NÃO"}')
        self.stdout.write(
            self.style.SUCCESS('='*60 + '\n')
        )
        
        # ===== INSTRUÇÕES FINAIS =====
        if plano.gerenciamento_salas:
            self.stdout.write(
                self.style.SUCCESS('🎉 Agora você pode criar e gerenciar salas!')
            )
            self.stdout.write(
                self.style.SUCCESS('📍 Acesse: /espacos/dashboard/salas/')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Este plano NÃO inclui gerenciamento de salas.')
            )
            self.stdout.write(
                self.style.WARNING('💡 Use: premium_s_plus ou combo_a_s_plus para ativar salas.')
            )