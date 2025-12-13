# ===============================================================
# Título: Management Command - Criar Planos de Assinatura
# Descrição: Popula o banco com os planos padrão do sistema
# Autor: Will
# Data: Dezembro 2025
# ===============================================================

from django.core.management.base import BaseCommand
from core.models import Plano, PlanoChoices


class Command(BaseCommand):
    """
    Comando para criar os planos de assinatura padrão
    Uso: python manage.py criar_planos
    """
    help = 'Cria os planos de assinatura padrão do sistema'

    def handle(self, *args, **kwargs):
        """
        Executa o comando de criação de planos
        """
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando criação dos planos...'))
        
        # Lista de planos a serem criados
        planos_data = [
            {
                'nome': PlanoChoices.GRATUITO_FILIADO,
                'nome_exibicao': 'Gratuito Filiado',
                'descricao': 'Plano gratuito para terapeutas vinculados a espaços. Acesso ao sistema de agendamento sem divulgação pública.',
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
                'nome': PlanoChoices.BASIC,
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
                'nome': PlanoChoices.PREMIUM_A,
                'nome_exibicao': 'Premium A',
                'descricao': 'Plano premium para terapeutas. Destaque nas buscas, estatísticas avançadas e suporte prioritário.',
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
                'nome': PlanoChoices.PREMIUM_S,
                'nome_exibicao': 'Premium S',
                'descricao': 'Plano premium para espaços terapêuticos. Destaque, estatísticas avançadas e recursos exclusivos.',
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
                'nome': PlanoChoices.PREMIUM_S_PLUS,
                'nome_exibicao': 'Premium S+',
                'descricao': 'Plano premium avançado para espaços com gerenciamento completo de salas e agendamentos.',
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
                'nome': PlanoChoices.COMBO_A_S,
                'nome_exibicao': 'Combo Premium A + S',
                'descricao': 'Combo completo para quem é terapeuta E tem espaço. Todos os benefícios dos planos Premium A e S.',
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
                'nome': PlanoChoices.COMBO_A_S_PLUS,
                'nome_exibicao': 'Combo Premium A + S+',
                'descricao': 'Combo máximo! Terapeuta + Espaço com gerenciamento completo de salas. Todos os recursos premium.',
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
            }
        ]
        
        # Criar ou atualizar cada plano
        criados = 0
        atualizados = 0
        
        for plano_data in planos_data:
            plano, created = Plano.objects.update_or_create(
                nome=plano_data['nome'],
                defaults=plano_data
            )
            
            if created:
                criados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Plano "{plano.nome_exibicao}" criado com sucesso!')
                )
            else:
                atualizados += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Plano "{plano.nome_exibicao}" atualizado!')
                )
        
        # Resumo
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'✨ Processo concluído!'))
        self.stdout.write(self.style.SUCCESS(f'📊 Total de planos criados: {criados}'))
        self.stdout.write(self.style.SUCCESS(f'🔄 Total de planos atualizados: {atualizados}'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))