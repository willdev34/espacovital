# ===============================================================
# Título: Comando para Popular Comodidades
# Descrição: Popula tabela de comodidades dos espaços terapêuticos
# ===============================================================

from django.core.management.base import BaseCommand
from django.db import transaction
from espacos.models import Comodidade


class Command(BaseCommand):
    """
    Comando para popular tabela Comodidade com dados iniciais
    Baseado no layout de filtros da busca de espaços
    """
    help = 'Popula tabela de Comodidades com dados iniciais'

    # ===============================================================
    # DADOS DAS COMODIDADES (baseado no layout espacoComFiltro.pdf)
    # ===============================================================
    COMODIDADES = [
        {
            'nome': 'Ar-condicionado',
            'icone': 'air-conditioning',
            'descricao': 'Ambiente climatizado com ar-condicionado',
            'is_destaque': True
        },
        {
            'nome': 'Maca',
            'icone': 'bed',
            'descricao': 'Maca profissional para atendimentos',
            'is_destaque': True
        },
        {
            'nome': 'Tatame / Futon / Colchão',
            'icone': 'mattress',
            'descricao': 'Tatame, futon ou colchão para práticas no chão',
            'is_destaque': True
        },
        {
            'nome': 'Isolamento acústico',
            'icone': 'soundproof',
            'descricao': 'Ambiente com isolamento acústico adequado',
            'is_destaque': True
        },
        {
            'nome': 'Estacionamento',
            'icone': 'parking',
            'descricao': 'Estacionamento disponível no local ou próximo',
            'is_destaque': True
        },
        {
            'nome': 'Wi-Fi',
            'icone': 'wifi',
            'descricao': 'Internet Wi-Fi disponível para clientes',
            'is_destaque': True
        },
        {
            'nome': 'Espaço para trabalho em grupo',
            'icone': 'group-work',
            'descricao': 'Ambiente adequado para sessões em grupo',
            'is_destaque': True
        },
        {
            'nome': 'Café / Recepção',
            'icone': 'coffee',
            'descricao': 'Área de recepção com café e comodidades',
            'is_destaque': True
        },
        {
            'nome': 'Banheiro com chuveiro',
            'icone': 'shower',
            'descricao': 'Banheiro equipado com chuveiro',
            'is_destaque': True
        },
        # Comodidades adicionais (não destaque)
        {
            'nome': 'Sala de espera',
            'icone': 'waiting-room',
            'descricao': 'Sala de espera confortável para clientes',
            'is_destaque': False
        },
        {
            'nome': 'Vestiário',
            'icone': 'locker-room',
            'descricao': 'Vestiário para troca de roupas',
            'is_destaque': False
        },
        {
            'nome': 'Música ambiente',
            'icone': 'music',
            'descricao': 'Sistema de som com música relaxante',
            'is_destaque': False
        },
        {
            'nome': 'Iluminação natural',
            'icone': 'sun',
            'descricao': 'Ambiente com boa iluminação natural',
            'is_destaque': False
        },
        {
            'nome': 'Plantas / Jardim',
            'icone': 'plant',
            'descricao': 'Ambiente com plantas ou acesso a jardim',
            'is_destaque': False
        },
        {
            'nome': 'Ventilação natural',
            'icone': 'wind',
            'descricao': 'Boa circulação de ar natural',
            'is_destaque': False
        },
        {
            'nome': 'Armários / Guarda-volumes',
            'icone': 'locker',
            'descricao': 'Armários para guardar pertences',
            'is_destaque': False
        },
        {
            'nome': 'Cozinha',
            'icone': 'kitchen',
            'descricao': 'Cozinha disponível para uso',
            'is_destaque': False
        },
        {
            'nome': 'Banheiro acessível',
            'icone': 'accessible-bathroom',
            'descricao': 'Banheiro adaptado para pessoas com mobilidade reduzida',
            'is_destaque': False
        },
    ]

    def add_arguments(self, parser):
        """
        Adiciona argumentos opcionais ao comando
        """
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Limpa todas as comodidades antes de popular'
        )

    def handle(self, *args, **options):
        """
        Executa o comando de população
        """
        # Cores para output no terminal
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('🏥 POPULANDO COMODIDADES DOS ESPAÇOS TERAPÊUTICOS'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))

        # Limpar tabela se solicitado
        if options['limpar']:
            self.stdout.write(self.style.WARNING('\n⚠️  Limpando tabela de Comodidades...'))
            Comodidade.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Tabela limpa com sucesso!\n'))

        # Estatísticas
        total_criadas = 0
        total_existentes = 0

        try:
            with transaction.atomic():
                self.stdout.write(self.style.HTTP_INFO('\n📋 Criando Comodidades...\n'))

                # Criar comodidades
                for comodidade_data in self.COMODIDADES:
                    comodidade, created = Comodidade.objects.get_or_create(
                        nome=comodidade_data['nome'],
                        defaults={
                            'icone': comodidade_data['icone'],
                            'descricao': comodidade_data['descricao'],
                            'is_destaque': comodidade_data['is_destaque']
                        }
                    )

                    if created:
                        total_criadas += 1
                        destaque_icon = '⭐' if comodidade.is_destaque else '  '
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  {destaque_icon} ✓ Criada: {comodidade.nome}'
                            )
                        )
                    else:
                        total_existentes += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'     ⚠ Já existe: {comodidade.nome}'
                            )
                        )

            # Resumo final
            self.stdout.write(self.style.HTTP_INFO('\n' + '=' * 70))
            self.stdout.write(self.style.HTTP_INFO('📊 RESUMO DA IMPORTAÇÃO'))
            self.stdout.write(self.style.HTTP_INFO('=' * 70))
            self.stdout.write(self.style.SUCCESS(f'✓ Comodidades criadas: {total_criadas}'))
            self.stdout.write(self.style.WARNING(f'⚠ Comodidades já existentes: {total_existentes}'))
            self.stdout.write(self.style.HTTP_INFO(f'📦 Total de comodidades: {Comodidade.objects.count()}'))
            self.stdout.write(self.style.HTTP_INFO(f'⭐ Comodidades em destaque: {Comodidade.objects.filter(is_destaque=True).count()}'))
            self.stdout.write(self.style.HTTP_INFO('=' * 70))
            self.stdout.write(self.style.SUCCESS('\n✅ Comando executado com sucesso!\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro ao popular comodidades: {str(e)}\n'))
            raise