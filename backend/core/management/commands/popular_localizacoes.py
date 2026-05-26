# ===============================================================
# Título: Comando para Popular Países, Estados e Cidades
# Descrição: Command Django para popular o banco com dados de localização internacional
# ===============================================================

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Pais, Estado, Cidade


class Command(BaseCommand):
    """
    Comando para popular o banco de dados com países, estados e cidades.
    Uso: python manage.py popular_localizacoes
    """
    
    help = 'Popula o banco de dados com países, estados e cidades'

    # Países principais onde terapeutas brasileiros podem estar
    PAISES = [
        {'nome': 'Brasil', 'codigo': 'BRA', 'ddi': '+55'},
        {'nome': 'Estados Unidos', 'codigo': 'USA', 'ddi': '+1'},
        {'nome': 'Portugal', 'codigo': 'PRT', 'ddi': '+351'},
        {'nome': 'Espanha', 'codigo': 'ESP', 'ddi': '+34'},
        {'nome': 'França', 'codigo': 'FRA', 'ddi': '+33'},
        {'nome': 'Reino Unido', 'codigo': 'GBR', 'ddi': '+44'},
        {'nome': 'Alemanha', 'codigo': 'DEU', 'ddi': '+49'},
        {'nome': 'Itália', 'codigo': 'ITA', 'ddi': '+39'},
        {'nome': 'Canadá', 'codigo': 'CAN', 'ddi': '+1'},
        {'nome': 'Argentina', 'codigo': 'ARG', 'ddi': '+54'},
        {'nome': 'Uruguai', 'codigo': 'URY', 'ddi': '+598'},
        {'nome': 'Chile', 'codigo': 'CHL', 'ddi': '+56'},
        {'nome': 'Austrália', 'codigo': 'AUS', 'ddi': '+61'},
        {'nome': 'Japão', 'codigo': 'JPN', 'ddi': '+81'},
        {'nome': 'México', 'codigo': 'MEX', 'ddi': '+52'},
    ]

    # Dicionário com estados brasileiros e suas principais cidades
    ESTADOS_CIDADES_BRASIL = {
        'AC': {
            'nome': 'Acre',
            'cidades': ['Rio Branco', 'Cruzeiro do Sul', 'Sena Madureira', 'Tarauacá']
        },
        'AL': {
            'nome': 'Alagoas',
            'cidades': ['Maceió', 'Arapiraca', 'Palmeira dos Índios', 'Rio Largo', 'Penedo']
        },
        'AP': {
            'nome': 'Amapá',
            'cidades': ['Macapá', 'Santana', 'Laranjal do Jari', 'Oiapoque']
        },
        'AM': {
            'nome': 'Amazonas',
            'cidades': ['Manaus', 'Parintins', 'Itacoatiara', 'Manacapuru', 'Coari', 'Tefé']
        },
        'BA': {
            'nome': 'Bahia',
            'cidades': [
                'Salvador', 'Feira de Santana', 'Vitória da Conquista', 'Camaçari', 
                'Itabuna', 'Juazeiro', 'Lauro de Freitas', 'Ilhéus', 'Jequié', 
                'Teixeira de Freitas', 'Porto Seguro', 'Barreiras'
            ]
        },
        'CE': {
            'nome': 'Ceará',
            'cidades': [
                'Fortaleza', 'Caucaia', 'Juazeiro do Norte', 'Maracanaú', 'Sobral', 
                'Crato', 'Itapipoca', 'Maranguape', 'Iguatu', 'Quixadá'
            ]
        },
        'DF': {
            'nome': 'Distrito Federal',
            'cidades': [
                'Brasília', 'Taguatinga', 'Ceilândia', 'Samambaia', 'Planaltina', 
                'Águas Claras', 'Gama', 'Santa Maria'
            ]
        },
        'ES': {
            'nome': 'Espírito Santo',
            'cidades': [
                'Vitória', 'Vila Velha', 'Serra', 'Cariacica', 'Cachoeiro de Itapemirim', 
                'Linhares', 'Guarapari', 'Colatina'
            ]
        },
        'GO': {
            'nome': 'Goiás',
            'cidades': [
                'Goiânia', 'Aparecida de Goiânia', 'Anápolis', 'Rio Verde', 'Luziânia', 
                'Águas Lindas de Goiás', 'Valparaíso de Goiás', 'Trindade', 'Formosa'
            ]
        },
        'MA': {
            'nome': 'Maranhão',
            'cidades': [
                'São Luís', 'Imperatriz', 'São José de Ribamar', 'Timon', 'Caxias', 
                'Codó', 'Paço do Lumiar', 'Açailândia'
            ]
        },
        'MT': {
            'nome': 'Mato Grosso',
            'cidades': [
                'Cuiabá', 'Várzea Grande', 'Rondonópolis', 'Sinop', 'Tangará da Serra', 
                'Cáceres', 'Sorriso', 'Lucas do Rio Verde'
            ]
        },
        'MS': {
            'nome': 'Mato Grosso do Sul',
            'cidades': [
                'Campo Grande', 'Dourados', 'Três Lagoas', 'Corumbá', 'Ponta Porã', 
                'Naviraí', 'Nova Andradina', 'Sidrolândia'
            ]
        },
        'MG': {
            'nome': 'Minas Gerais',
            'cidades': [
                'Belo Horizonte', 'Uberlândia', 'Contagem', 'Juiz de Fora', 'Betim', 
                'Montes Claros', 'Ribeirão das Neves', 'Uberaba', 'Governador Valadares', 
                'Ipatinga', 'Sete Lagoas', 'Divinópolis', 'Santa Luzia', 'Poços de Caldas', 
                'Patos de Minas', 'Pouso Alegre', 'Teófilo Otoni', 'Varginha'
            ]
        },
        'PA': {
            'nome': 'Pará',
            'cidades': [
                'Belém', 'Ananindeua', 'Santarém', 'Marabá', 'Castanhal', 'Parauapebas', 
                'Itaituba', 'Cametá', 'Bragança', 'Abaetetuba'
            ]
        },
        'PB': {
            'nome': 'Paraíba',
            'cidades': [
                'João Pessoa', 'Campina Grande', 'Santa Rita', 'Patos', 'Bayeux', 
                'Sousa', 'Cajazeiras', 'Guarabira'
            ]
        },
        'PR': {
            'nome': 'Paraná',
            'cidades': [
                'Curitiba', 'Londrina', 'Maringá', 'Ponta Grossa', 'Cascavel', 
                'São José dos Pinhais', 'Foz do Iguaçu', 'Colombo', 'Guarapuava', 
                'Paranaguá', 'Araucária', 'Toledo', 'Apucarana', 'Pinhais'
            ]
        },
        'PE': {
            'nome': 'Pernambuco',
            'cidades': [
                'Recife', 'Jaboatão dos Guararapes', 'Olinda', 'Caruaru', 'Petrolina', 
                'Paulista', 'Cabo de Santo Agostinho', 'Camaragibe', 'Garanhuns', 'Vitória de Santo Antão'
            ]
        },
        'PI': {
            'nome': 'Piauí',
            'cidades': [
                'Teresina', 'Parnaíba', 'Picos', 'Piripiri', 'Floriano', 
                'Campo Maior', 'Barras', 'Altos'
            ]
        },
        'RJ': {
            'nome': 'Rio de Janeiro',
            'cidades': [
                'Rio de Janeiro', 'São Gonçalo', 'Duque de Caxias', 'Nova Iguaçu', 
                'Niterói', 'Belford Roxo', 'Campos dos Goytacazes', 'São João de Meriti', 
                'Petrópolis', 'Volta Redonda', 'Magé', 'Itaboraí', 'Macaé', 
                'Cabo Frio', 'Nova Friburgo', 'Barra Mansa', 'Angra dos Reis', 'Teresópolis'
            ]
        },
        'RN': {
            'nome': 'Rio Grande do Norte',
            'cidades': [
                'Natal', 'Mossoró', 'Parnamirim', 'São Gonçalo do Amarante', 'Macaíba', 
                'Ceará-Mirim', 'Caicó', 'Assu'
            ]
        },
        'RS': {
            'nome': 'Rio Grande do Sul',
            'cidades': [
                'Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas', 'Santa Maria', 
                'Gravataí', 'Viamão', 'Novo Hamburgo', 'São Leopoldo', 'Rio Grande', 
                'Alvorada', 'Passo Fundo', 'Sapucaia do Sul', 'Uruguaiana', 'Santa Cruz do Sul'
            ]
        },
        'RO': {
            'nome': 'Rondônia',
            'cidades': [
                'Porto Velho', 'Ji-Paraná', 'Ariquemes', 'Vilhena', 'Cacoal', 
                'Jaru', 'Rolim de Moura', 'Guajará-Mirim'
            ]
        },
        'RR': {
            'nome': 'Roraima',
            'cidades': ['Boa Vista', 'Rorainópolis', 'Caracaraí', 'Alto Alegre']
        },
        'SC': {
            'nome': 'Santa Catarina',
            'cidades': [
                'Florianópolis', 'Joinville', 'Blumenau', 'São José', 'Criciúma', 
                'Chapecó', 'Itajaí', 'Jaraguá do Sul', 'Lages', 'Palhoça', 
                'Balneário Camboriú', 'Brusque', 'Tubarão', 'Concórdia'
            ]
        },
        'SP': {
            'nome': 'São Paulo',
            'cidades': [
                'São Paulo', 'Guarulhos', 'Campinas', 'São Bernardo do Campo', 'Santo André', 
                'Osasco', 'São José dos Campos', 'Ribeirão Preto', 'Sorocaba', 'Mauá', 
                'São José do Rio Preto', 'Santos', 'Diadema', 'Jundiaí', 'Carapicuíba', 
                'Piracicaba', 'Bauru', 'São Vicente', 'Itaquaquecetuba', 'Franca', 
                'Guarujá', 'Taubaté', 'Limeira', 'Suzano', 'Taboão da Serra', 
                'Sumaré', 'Barueri', 'Embu das Artes', 'São Carlos', 'Marília'
            ]
        },
        'SE': {
            'nome': 'Sergipe',
            'cidades': [
                'Aracaju', 'Nossa Senhora do Socorro', 'Lagarto', 'Itabaiana', 'São Cristóvão', 
                'Estância', 'Tobias Barreto', 'Simão Dias'
            ]
        },
        'TO': {
            'nome': 'Tocantins',
            'cidades': [
                'Palmas', 'Araguaína', 'Gurupi', 'Porto Nacional', 'Paraíso do Tocantins', 
                'Colinas do Tocantins', 'Guaraí', 'Miracema do Tocantins'
            ]
        },
    }

    def handle(self, *args, **options):
        """
        Método principal que executa o comando.
        Cria países, estados e cidades.
        """
        
        self.stdout.write(self.style.WARNING('🌎 Iniciando população de Localização Internacional...'))
        
        try:
            with transaction.atomic():
                # Contadores
                paises_criados = 0
                estados_criados = 0
                cidades_criadas = 0
                
                # ===== CRIAR PAÍSES =====
                self.stdout.write(self.style.SUCCESS('\n🌍 Criando Países...'))
                
                for pais_data in self.PAISES:
                    pais, created = Pais.objects.get_or_create(
                        codigo=pais_data['codigo'],
                        defaults={
                            'nome': pais_data['nome'],
                            'ddi': pais_data['ddi']
                        }
                    )
                    
                    if created:
                        paises_criados += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✅ País criado: {pais.nome} ({pais.codigo})')
                        )
                
                # ===== CRIAR ESTADOS GENÉRICOS PARA PAÍSES SEM DIVISÃO =====
                self.stdout.write(self.style.SUCCESS('\n🌍 Criando estados genéricos para países...'))
                
                # Portugal - principais distritos
                portugal = Pais.objects.get(codigo='PRT')
                estados_portugal = [
                    {'nome': 'Lisboa', 'sigla': 'LIS'},
                    {'nome': 'Porto', 'sigla': 'PRT'},
                    {'nome': 'Faro', 'sigla': 'FAR'},
                    {'nome': 'Coimbra', 'sigla': 'CBR'},
                    {'nome': 'Braga', 'sigla': 'BRG'},
                ]
                
                for est_data in estados_portugal:
                    estado, created = Estado.objects.get_or_create(
                        sigla=est_data['sigla'],
                        pais=portugal,
                        defaults={'nome': est_data['nome']}
                    )
                    if created:
                        self.stdout.write(f'  ✅ Estado criado: {estado.nome} - Portugal')
                
                # Estados Unidos - principais estados
                usa = Pais.objects.get(codigo='USA')
                estados_usa = [
                    {'nome': 'California', 'sigla': 'CA'},
                    {'nome': 'New York', 'sigla': 'NY'},
                    {'nome': 'Florida', 'sigla': 'FL'},
                    {'nome': 'Texas', 'sigla': 'TX'},
                    {'nome': 'Massachusetts', 'sigla': 'MA'},
                ]
                
                for est_data in estados_usa:
                    estado, created = Estado.objects.get_or_create(
                        sigla=est_data['sigla'],
                        pais=usa,
                        defaults={'nome': est_data['nome']}
                    )
                    if created:
                        self.stdout.write(f'  ✅ Estado criado: {estado.nome} - EUA')
                
                # Para países menores, criar estado genérico
                paises_genericos = [
                    ('URY', 'Uruguai'),
                    ('ARG', 'Argentina - BA'),  # Buenos Aires
                    ('CHL', 'Chile - RM'),  # Región Metropolitana
                ]
                
                for codigo_pais, nome_estado in paises_genericos:
                    try:
                        pais_obj = Pais.objects.get(codigo=codigo_pais)
                        estado, created = Estado.objects.get_or_create(
                            sigla=codigo_pais,
                            pais=pais_obj,
                            defaults={'nome': nome_estado}
                        )
                        if created:
                            self.stdout.write(f'  ✅ Estado genérico criado: {estado.nome}')
                    except Pais.DoesNotExist:
                        pass

                # Pegar o Brasil para criar estados
                brasil = Pais.objects.get(codigo='BRA')
                
                # ===== ATUALIZAR ESTADOS EXISTENTES COM PAÍS =====
                self.stdout.write(self.style.SUCCESS('\n📍 Vinculando Estados existentes ao Brasil...'))
                
                estados_sem_pais = Estado.objects.filter(pais__isnull=True)
                for estado in estados_sem_pais:
                    estado.pais = brasil
                    estado.save()
                    self.stdout.write(f'  ✅ Estado atualizado: {estado.nome}')
                
                # ===== CRIAR ESTADOS BRASILEIROS (se não existirem) =====
                self.stdout.write(self.style.SUCCESS('\n🗺️  Verificando Estados Brasileiros...'))
                
                for sigla, dados in self.ESTADOS_CIDADES_BRASIL.items():
                    estado, created = Estado.objects.get_or_create(
                        sigla=sigla,
                        pais=brasil,
                        defaults={'nome': dados['nome']}
                    )
                    
                    if created:
                        estados_criados += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✅ Estado criado: {estado.nome} ({sigla})')
                        )
                    
                    # Criar cidades
                    for nome_cidade in dados['cidades']:
                        cidade, created = Cidade.objects.get_or_create(
                            nome=nome_cidade,
                            estado=estado
                        )
                        
                        if created:
                            cidades_criadas += 1
                
                # ===== RESUMO =====
                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('📊 RESUMO DA OPERAÇÃO'))
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write(f'  Países criados: {paises_criados}')
                self.stdout.write(f'  Total de países: {Pais.objects.count()}')
                self.stdout.write(f'  Estados criados: {estados_criados}')
                self.stdout.write(f'  Total de estados: {Estado.objects.count()}')
                self.stdout.write(f'  Cidades criadas: {cidades_criadas}')
                self.stdout.write(f'  Total de cidades: {Cidade.objects.count()}')
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write(
                    self.style.SUCCESS('\n✅ População de localizações concluída com sucesso!\n')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Erro ao popular localizações: {str(e)}\n')
            )
            raise