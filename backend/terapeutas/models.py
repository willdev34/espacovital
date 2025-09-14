# ===============================================================
# Título: Models do App Terapeutas - Espaço Vital
# Descrição: Models para gerenciar terapeutas, especialidades e avaliações
# Autor: Will | Empresa: Espaço VItal
# Data: 13/09/2025
# ===============================================================

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinLengthValidator, EmailValidator, RegexValidator
from django.utils.text import slugify
from core.models import TimeStampedModel, BaseModel


# ===============================================================
# CHOICES PARA OS MODELS
# ===============================================================

class SessionType(models.TextChoices):
    """
    Tipos de sessão que o terapeuta oferece
    Baseado no layout da busca avançada
    """
    PRESENCIAL = 'presencial', 'Presencial'
    ONLINE = 'online', 'On-line'
    DOMICILIO = 'domicilio', 'Domicílio'


class ProfileType(models.TextChoices):
    """
    Tipo de perfil profissional
    Baseado no layout da busca avançada
    """
    INDIVIDUAL = 'individual', 'Individual'
    ESPACOS = 'espacos', 'Espaços'


class ClientType(models.TextChoices):
    """
    Para quem é direcionada a terapia
    Baseado no layout da busca avançada
    """
    QUALQUER_UM = 'qualquer_um', 'Qualquer um'
    ADULTOS = 'adultos', 'Adultos'
    CRIANCAS = 'criancas', 'Crianças'
    IDOSOS = 'idosos', 'Idosos'
    CASAIS = 'casais', 'Casais'
    GRUPOS = 'grupos', 'Grupos'


# ===============================================================
# MODELS PRINCIPAIS
# ===============================================================

class Estado(models.Model):
    """
    Modelo para Estados brasileiros
    """
    nome = models.CharField(
        'Nome do Estado',
        max_length=100
    )
    sigla = models.CharField(
        'Sigla',
        max_length=2,
        unique=True
    )
    
    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['nome']
    
    def __str__(self):
        return f'{self.nome} ({self.sigla})'


class Cidade(models.Model):
    """
    Modelo para Cidades brasileiras
    """
    nome = models.CharField(
        'Nome da Cidade',
        max_length=100
    )
    estado = models.ForeignKey(
        Estado,
        on_delete=models.CASCADE,
        related_name='cidades',
        verbose_name='Estado'
    )
    
    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        ordering = ['nome']
        unique_together = ['nome', 'estado']
    
    def __str__(self):
        return f'{self.nome} - {self.estado.sigla}'


class Especialidade(BaseModel):
    """
    Modelo para Especialidades/Terapias
    Baseado nos layouts compartilhados
    """
    nome = models.CharField(
        'Nome da Especialidade',
        max_length=100,
        unique=True,
        help_text='Nome da terapia/especialidade (ex: Massoterapia, Reiki)'
    )
    
    slug = models.SlugField(
        'Slug',
        max_length=120,
        unique=True,
        blank=True,
        help_text='URL amigável (será gerado automaticamente)'
    )
    
    descricao_curta = models.TextField(
        'Descrição Curta',
        max_length=200,
        help_text='Descrição breve para exibição em cards'
    )
    
    descricao_completa = models.TextField(
        'Descrição Completa',
        help_text='Descrição detalhada da terapia'
    )
    
    icone = models.ImageField(
        'Ícone',
        upload_to='especialidades/icones/',
        blank=True,
        null=True,
        help_text='Ícone da especialidade (64x64px recomendado)'
    )
    
    cor_destaque = models.CharField(
        'Cor de Destaque',
        max_length=7,
        default='#0B5259',
        help_text='Cor hex para cards e destaques'
    )
    
    ordem = models.PositiveIntegerField(
        'Ordem de Exibição',
        default=0,
        help_text='Ordem de exibição nas listagens'
    )
    
    destaque = models.BooleanField(
        'Em Destaque',
        default=False,
        help_text='Exibir na página principal'
    )
    
    class Meta:
        verbose_name = 'Especialidade'
        verbose_name_plural = 'Especialidades'
        ordering = ['ordem', 'nome']
        indexes = [
            models.Index(fields=['destaque', 'is_active']),
            models.Index(fields=['ordem']),
        ]
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('terapias:detail', kwargs={'slug': self.slug})


class Terapeuta(BaseModel):
    """
    Modelo principal para Terapeutas
    Baseado nos layouts da busca avançada
    """
    # Informações básicas
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuário',
        help_text='Usuário Django relacionado'
    )
    
    nome_completo = models.CharField(
        'Nome Completo',
        max_length=150,
        validators=[MinLengthValidator(2)],
        help_text='Nome completo do terapeuta'
    )
    
    nome_exibicao = models.CharField(
        'Nome de Exibição',
        max_length=100,
        help_text='Nome para exibição pública (ex: Ana Silva)'
    )
    
    slug = models.SlugField(
        'Slug',
        max_length=120,
        unique=True,
        blank=True,
        help_text='URL amigável do perfil'
    )
    
    # Informações de contato
    email_profissional = models.EmailField(
        'E-mail Profissional',
        validators=[EmailValidator()],
        help_text='E-mail para contato profissional'
    )
    
    telefone = models.CharField(
        'Telefone',
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Formato: '+999999999'. Até 15 dígitos."
        )],
        help_text='Telefone para contato'
    )
    
    whatsapp = models.CharField(
        'WhatsApp',
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Formato: '+999999999'. Até 15 dígitos."
        )],
        help_text='Número do WhatsApp (opcional)'
    )
    
    # Localização
    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Cidade',
        help_text='Cidade onde atua'
    )
    
    bairro = models.CharField(
        'Bairro',
        max_length=100,
        blank=True,
        help_text='Bairro onde atua'
    )
    
    endereco = models.TextField(
        'Endereço',
        blank=True,
        help_text='Endereço completo (opcional para privacidade)'
    )
    
    # Informações profissionais
    especialidades = models.ManyToManyField(
        Especialidade,
        through='TerapeutaEspecialidade',
        verbose_name='Especialidades',
        help_text='Especialidades que o terapeuta oferece'
    )
    
    registro_profissional = models.CharField(
        'Registro Profissional',
        max_length=50,
        blank=True,
        help_text='Número do registro profissional (CRT, etc.)'
    )
    
    formacao = models.TextField(
        'Formação',
        help_text='Formação acadêmica e cursos'
    )
    
    experiencia_anos = models.PositiveIntegerField(
        'Anos de Experiência',
        default=0,
        help_text='Anos de experiência profissional'
    )
    
    # Configurações de atendimento - Baseado no layout
    tipos_sessao = models.JSONField(
        'Tipos de Sessão',
        default=list,
        help_text='Lista de tipos: presencial, online, domicilio'
    )
    
    tipo_perfil = models.CharField(
        'Tipo de Perfil',
        max_length=20,
        choices=ProfileType.choices,
        default=ProfileType.INDIVIDUAL,
        help_text='Individual ou Espaços'
    )
    
    para_quem = models.CharField(
        'Para Quem',
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.QUALQUER_UM,
        help_text='Público-alvo dos atendimentos'
    )
    
    acessibilidade = models.BooleanField(
        'Acessibilidade',
        default=False,
        help_text='Local/atendimento com acessibilidade'
    )
    
    # Descrições
    bio_curta = models.TextField(
        'Bio Curta',
        max_length=300,
        help_text='Descrição breve para listagens (máx 300 chars)'
    )
    
    bio_completa = models.TextField(
        'Bio Completa',
        help_text='Descrição detalhada do perfil profissional'
    )
    
    metodologia = models.TextField(
        'Metodologia',
        blank=True,
        help_text='Descrição da metodologia de trabalho'
    )
    
    # Mídia
    foto_perfil = models.ImageField(
        'Foto de Perfil',
        upload_to='terapeutas/fotos/',
        blank=True,
        null=True,
        help_text='Foto profissional (400x400px recomendado)'
    )
    
    foto_capa = models.ImageField(
        'Foto de Capa',
        upload_to='terapeutas/capas/',
        blank=True,
        null=True,
        help_text='Foto para capa do perfil (1200x400px)'
    )
    
    # Status e verificação
    verificado = models.BooleanField(
        'Verificado',
        default=False,
        help_text='Terapeuta verificado pela plataforma'
    )
    
    destaque = models.BooleanField(
        'Em Destaque',
        default=False,
        help_text='Exibir na home como destaque'
    )
    
    premium = models.BooleanField(
        'Premium',
        default=False,
        help_text='Conta premium com benefícios'
    )
    
    data_verificacao = models.DateTimeField(
        'Data de Verificação',
        null=True,
        blank=True,
        help_text='Quando foi verificado'
    )
    
    # Métricas
    visualizacoes = models.PositiveIntegerField(
        'Visualizações',
        default=0,
        help_text='Número de visualizações do perfil'
    )
    
    total_contatos = models.PositiveIntegerField(
        'Total de Contatos',
        default=0,
        help_text='Número de contatos recebidos'
    )
    
    class Meta:
        verbose_name = 'Terapeuta'
        verbose_name_plural = 'Terapeutas'
        ordering = ['-destaque', '-premium', '-verificado', 'nome_exibicao']
        indexes = [
            models.Index(fields=['verificado', 'is_active']),
            models.Index(fields=['destaque', 'is_active']),
            models.Index(fields=['premium', 'is_active']),
            models.Index(fields=['cidade', 'is_active']),
        ]
    
    def __str__(self):
        return self.nome_exibicao
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome_exibicao)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('terapeutas:profile', kwargs={'slug': self.slug})
    
    @property
    def rating_medio(self):
        """
        Calcula a média das avaliações
        """
        avaliacoes = self.avaliacoes.filter(is_active=True)
        if avaliacoes.exists():
            return round(avaliacoes.aggregate(
                media=models.Avg('nota')
            )['media'], 1)
        return 0.0
    
    @property
    def total_avaliacoes(self):
        """
        Total de avaliações ativas
        """
        return self.avaliacoes.filter(is_active=True).count()
    
    @property
    def especialidades_nomes(self):
        """
        Lista dos nomes das especialidades
        """
        return [esp.nome for esp in self.especialidades.filter(is_active=True)]
    
    def incrementar_visualizacoes(self):
        """
        Incrementa contador de visualizações
        """
        self.visualizacoes += 1
        self.save(update_fields=['visualizacoes'])


class TerapeutaEspecialidade(BaseModel):
    """
    Relacionamento entre Terapeuta e Especialidade
    Permite informações específicas da especialidade para cada terapeuta
    """
    terapeuta = models.ForeignKey(
        Terapeuta,
        on_delete=models.CASCADE,
        verbose_name='Terapeuta'
    )
    
    especialidade = models.ForeignKey(
        Especialidade,
        on_delete=models.CASCADE,
        verbose_name='Especialidade'
    )
    
    preco_sessao = models.DecimalField(
        'Preço por Sessão',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Preço em reais (opcional)'
    )
    
    duracao_sessao = models.PositiveIntegerField(
        'Duração da Sessão (min)',
        null=True,
        blank=True,
        help_text='Duração em minutos'
    )
    
    certificacao = models.CharField(
        'Certificação',
        max_length=200,
        blank=True,
        help_text='Certificações específicas nesta especialidade'
    )
    
    anos_experiencia = models.PositiveIntegerField(
        'Anos de Experiência',
        default=0,
        help_text='Anos de experiência nesta especialidade'
    )
    
    observacoes = models.TextField(
        'Observações',
        blank=True,
        help_text='Observações específicas sobre esta especialidade'
    )
    
    principal = models.BooleanField(
        'Especialidade Principal',
        default=False,
        help_text='Esta é a especialidade principal do terapeuta'
    )
    
    class Meta:
        verbose_name = 'Especialidade do Terapeuta'
        verbose_name_plural = 'Especialidades dos Terapeutas'
        unique_together = ['terapeuta', 'especialidade']
        ordering = ['-principal', 'especialidade__nome']
    
    def __str__(self):
        return f'{self.terapeuta.nome_exibicao} - {self.especialidade.nome}'


class Avaliacao(BaseModel):
    """
    Avaliações dos terapeutas pelos clientes
    """
    terapeuta = models.ForeignKey(
        Terapeuta,
        on_delete=models.CASCADE,
        related_name='avaliacoes',
        verbose_name='Terapeuta'
    )
    
    cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Cliente',
        help_text='Cliente que fez a avaliação'
    )
    
    nota = models.PositiveIntegerField(
        'Nota',
        choices=[(i, i) for i in range(1, 6)],
        help_text='Nota de 1 a 5'
    )
    
    comentario = models.TextField(
        'Comentário',
        blank=True,
        help_text='Comentário opcional sobre o atendimento'
    )
    
    data_sessao = models.DateField(
        'Data da Sessão',
        null=True,
        blank=True,
        help_text='Data da sessão avaliada'
    )
    
    recomenda = models.BooleanField(
        'Recomenda',
        default=True,
        help_text='Cliente recomendaria este terapeuta'
    )
    
    verificada = models.BooleanField(
        'Avaliação Verificada',
        default=False,
        help_text='Avaliação verificada pela plataforma'
    )
    
    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-created_at']
        unique_together = ['terapeuta', 'cliente']
        indexes = [
            models.Index(fields=['terapeuta', 'is_active']),
            models.Index(fields=['nota', 'is_active']),
        ]
    
    def __str__(self):
        return f'{self.cliente.get_full_name()} → {self.terapeuta.nome_exibicao} ({self.nota}/5)'


class Contato(TimeStampedModel):
    """
    Contatos enviados para terapeutas
    """
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('lido', 'Lido'),
        ('respondido', 'Respondido'),
        ('arquivado', 'Arquivado'),
    ]
    
    terapeuta = models.ForeignKey(
        Terapeuta,
        on_delete=models.CASCADE,
        related_name='contatos_recebidos',
        verbose_name='Terapeuta'
    )
    
    nome = models.CharField(
        'Nome',
        max_length=100,
        help_text='Nome de quem está entrando em contato'
    )
    
    email = models.EmailField(
        'E-mail',
        help_text='E-mail para resposta'
    )
    
    telefone = models.CharField(
        'Telefone',
        max_length=20,
        blank=True,
        help_text='Telefone para contato'
    )
    
    assunto = models.CharField(
        'Assunto',
        max_length=150,
        help_text='Assunto da mensagem'
    )
    
    mensagem = models.TextField(
        'Mensagem',
        help_text='Mensagem detalhada'
    )
    
    especialidade_interesse = models.ForeignKey(
        Especialidade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Especialidade de Interesse',
        help_text='Especialidade que despertou interesse'
    )
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='enviado',
        help_text='Status do contato'
    )
    
    ip_origem = models.GenericIPAddressField(
        'IP de Origem',
        null=True,
        blank=True,
        help_text='IP de onde foi enviado'
    )
    
    class Meta:
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['terapeuta', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.nome} → {self.terapeuta.nome_exibicao}'