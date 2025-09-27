# ===============================================================
# Título: Models do App Espacos - Espaço Vital
# Descrição: Models para gerenciar espaços terapêuticos, comodidades e avaliações
# Autor: Will | Empresa: Espaço Vital
# Data: 14/09/2025
# ===============================================================

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinLengthValidator, EmailValidator, RegexValidator
from django.utils.text import slugify
from core.models import TimeStampedModel, BaseModel


# ===============================================================
# CHOICES PARA OS MODELS DE ESPACOS
# ===============================================================

class TipoEspaco(models.TextChoices):
    """
    Tipos de espaço terapêutico disponíveis
    Baseado no layout da busca avançada de espaços
    """
    CLINICA = 'clinica', 'Clínica'
    CENTRO_HOLISTICO = 'centro_holistico', 'Centro Holístico'
    ESTUDIO = 'estudio', 'Estúdio'
    SPA = 'spa', 'Spa'
    CONSULTORIO = 'consultorio', 'Consultório'
    ESPACO_COMPARTILHADO = 'espaco_compartilhado', 'Espaço Compartilhado'
    OUTROS = 'outros', 'Outros'


class DisponibilidadePeriodo(models.TextChoices):
    """
    Períodos de disponibilidade do espaço
    Baseado no layout da busca avançada
    """
    MANHA = 'manha', 'Manhã'
    TARDE = 'tarde', 'Tarde'
    NOITE = 'noite', 'Noite'
    FINAIS_DE_SEMANA = 'finais_de_semana', 'Finais de semana'


# ===============================================================
# MODELS DE LOCALIZACAO (REAPROVEITADOS DE TERAPEUTAS)
# ===============================================================

class Estado(BaseModel):
    """
    Model para estados brasileiros
    Reutilizado do app terapeutas para consistência
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text="Nome completo do estado"
    )
    sigla = models.CharField(
        max_length=2,
        unique=True,
        help_text="Sigla do estado (ex: RJ, SP)"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        help_text="Slug para URLs amigáveis"
    )

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.sigla})"

    def save(self, *args, **kwargs):
        """
        Gera slug automático baseado no nome
        """
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Cidade(BaseModel):
    """
    Model para cidades brasileiras
    Reutilizado do app terapeutas para consistência
    """
    nome = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Nome da cidade"
    )
    estado = models.ForeignKey(
        Estado,
        on_delete=models.CASCADE,
        related_name='cidades_espacos',
        help_text="Estado ao qual a cidade pertence"
    )
    slug = models.SlugField(
        max_length=120,
        blank=True,
        help_text="Slug para URLs amigáveis"
    )

    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        unique_together = ['nome', 'estado']
        ordering = ['estado__nome', 'nome']

    def __str__(self):
        return f"{self.nome} - {self.estado.sigla}"

    def save(self, *args, **kwargs):
        """
        Gera slug automático baseado no nome e estado
        """
        if not self.slug:
            self.slug = slugify(f"{self.nome}-{self.estado.sigla}")
        super().save(*args, **kwargs)


# ===============================================================
# MODELS DE COMODIDADES E ESPECIALIDADES
# ===============================================================

class Comodidade(BaseModel):
    """
    Model para comodidades disponíveis nos espaços
    Baseado no layout de filtros com checkboxes
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome da comodidade (ex: Ar-condicionado, Maca)"
    )
    icone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nome do ícone (ex: 'air-conditioning', 'bed')"
    )
    descricao = models.TextField(
        blank=True,
        help_text="Descrição detalhada da comodidade"
    )
    is_destaque = models.BooleanField(
        default=False,
        help_text="Comodidade aparece em destaque nos filtros"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        help_text="Slug para URLs amigáveis"
    )

    class Meta:
        verbose_name = 'Comodidade'
        verbose_name_plural = 'Comodidades'
        ordering = ['-is_destaque', 'nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        """
        Gera slug automático baseado no nome
        """
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Especialidade(BaseModel):
    """
    Model para especialidades/terapias oferecidas no espaço
    Conecta com as terapias disponíveis na plataforma
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome da especialidade/terapia"
    )
    descricao = models.TextField(
        blank=True,
        help_text="Descrição da especialidade"
    )
    categoria = models.CharField(
        max_length=50,
        blank=True,
        help_text="Categoria da terapia (ex: Massagem, Energética)"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        help_text="Slug para URLs amigáveis"
    )

    class Meta:
        verbose_name = 'Especialidade'
        verbose_name_plural = 'Especialidades'
        ordering = ['categoria', 'nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        """
        Gera slug automático baseado no nome
        """
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


# ===============================================================
# MODEL PRINCIPAL - ESPACO
# ===============================================================

class Espaco(TimeStampedModel):
    """
    Model principal para espaços terapêuticos
    Baseado nos campos do layout de busca avançada
    """
    # Informações básicas
    nome = models.CharField(
        max_length=200,
        help_text="Nome do espaço terapêutico"
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text="Slug para URLs amigáveis"
    )
    descricao_breve = models.TextField(
        max_length=300,
        help_text="Descrição breve para cards (máx 300 caracteres)"
    )
    descricao_completa = models.TextField(
        blank=True,
        help_text="Descrição completa do espaço"
    )

    # Localização
    endereco = models.CharField(
        max_length=255,
        help_text="Endereço completo do espaço"
    )
    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.CASCADE,
        related_name='espacos',
        help_text="Cidade onde está localizado"
    )
    cep = models.CharField(
        max_length=10,
        validators=[RegexValidator(
            regex=r'^\d{5}-?\d{3}$',
            message='CEP deve estar no formato 12345-678'
        )],
        help_text="CEP do espaço"
    )
    bairro = models.CharField(
        max_length=100,
        help_text="Bairro do espaço"
    )

    # Características do espaço (filtros do layout)
    tipo_espaco = models.CharField(
        max_length=50,
        choices=TipoEspaco.choices,
        default=TipoEspaco.CENTRO_HOLISTICO,
        help_text="Tipo de espaço terapêutico"
    )
    aceita_locacao = models.BooleanField(
        default=False,
        help_text="Aceita locação por outros terapeutas"
    )
    tem_acessibilidade = models.BooleanField(
        default=False,
        help_text="Espaço possui acessibilidade"
    )

    # Disponibilidade
    disponibilidade = models.JSONField(
        default=list,
        blank=True,
        help_text="Períodos de disponibilidade (lista de períodos)"
    )

    # Relacionamentos Many-to-Many
    comodidades = models.ManyToManyField(
        Comodidade,
        blank=True,
        related_name='espacos',
        help_text="Comodidades disponíveis no espaço"
    )
    especialidades = models.ManyToManyField(
        Especialidade,
        blank=True,
        related_name='espacos',
        help_text="Terapias oferecidas no espaço"
    )

    # Contato
    telefone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
            message='Telefone deve estar no formato (11) 99999-9999'
        )],
        help_text="Telefone para contato"
    )
    email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Email para contato"
    )
    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
            message='WhatsApp deve estar no formato (11) 99999-9999'
        )],
        help_text="WhatsApp para contato"
    )
    website = models.URLField(
        blank=True,
        help_text="Site oficial do espaço"
    )
    instagram = models.CharField(
        max_length=50,
        blank=True,
        help_text="Usuário do Instagram (sem @)"
    )

    # Sistema de verificação e destaque
    is_verificado = models.BooleanField(
        default=False,
        help_text="Espaço foi verificado pela equipe"
    )
    is_premium = models.BooleanField(
        default=False,
        help_text="Espaço possui plano premium"
    )
    is_destaque = models.BooleanField(
        default=False,
        help_text="Espaço aparece em destaque na home"
    )
    data_verificacao = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data da verificação"
    )

    # Controle de status
    is_active = models.BooleanField(
        default=True,
        help_text="Espaço está ativo na plataforma"
    )

    # Imagens
    foto_principal = models.ImageField(
        upload_to='espacos/fotos/',
        blank=True,
        null=True,
        help_text="Foto principal do espaço"
    )
    foto_galeria = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de URLs das fotos da galeria"
    )

    # Proprietário/Responsável
    responsavel = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='espacos_gerenciados',
        help_text="Usuário responsável pelo espaço"
    )

    class Meta:
        verbose_name = 'Espaço Terapêutico'
        verbose_name_plural = 'Espaços Terapêuticos'
        ordering = ['-is_destaque', '-is_premium', '-is_verificado', 'nome']
        indexes = [
            models.Index(fields=['cidade', 'is_active']),
            models.Index(fields=['tipo_espaco', 'is_active']),
            models.Index(fields=['is_destaque', 'is_premium']),
        ]

    def __str__(self):
        return f"{self.nome} - {self.cidade}"

    def save(self, *args, **kwargs):
        """
        Gera slug automático e validações personalizadas
        """
        if not self.slug:
            base_slug = slugify(f"{self.nome}-{self.cidade.nome}")
            slug = base_slug
            counter = 1
            while Espaco.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        URL para página de detalhes do espaço
        """
        return reverse('espacos:detalhe', kwargs={'slug': self.slug})

    @property
    def nome_completo(self):
        """
        Nome completo com localização
        """
        return f"{self.nome} - {self.cidade}"

    @property
    def media_avaliacoes(self):
        """
        Média das avaliações do espaço
        """
        if self.avaliacoes.exists():
            return self.avaliacoes.aggregate(
                models.Avg('nota')
            )['nota__avg']
        return 0

    @property
    def total_avaliacoes(self):
        """
        Total de avaliações ativas
        """
        return self.avaliacoes.filter(is_active=True).count()

    @property
    def especialidades_lista(self):
        """
        Lista das especialidades como string
        """
        return ", ".join([esp.nome for esp in self.especialidades.all()[:3]])

    @property
    def comodidades_destaque(self):
        """
        Comodidades em destaque (máximo 4)
        """
        return self.comodidades.filter(is_destaque=True)[:4]

    def get_status_badges(self):
        """
        Retorna lista de badges do espaço
        """
        badges = []
        if self.is_verificado:
            badges.append({'tipo': 'verificado', 'texto': 'Verificado'})
        if self.is_premium:
            badges.append({'tipo': 'premium', 'texto': 'Premium'})
        if self.is_destaque:
            badges.append({'tipo': 'destaque', 'texto': 'Destaque'})
        return badges


# ===============================================================
# MODELS DE AVALIACAO E CONTATO
# ===============================================================

class AvaliacaoEspaco(TimeStampedModel):
    """
    Model para avaliações dos espaços
    Baseado no sistema de avaliações dos terapeutas
    """
    espaco = models.ForeignKey(
        Espaco,
        on_delete=models.CASCADE,
        related_name='avaliacoes',
        help_text="Espaço avaliado"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avaliacoes_espacos',
        help_text="Usuário que fez a avaliação"
    )
    nota = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Nota de 1 a 5 estrelas"
    )
    comentario = models.TextField(
        max_length=500,
        help_text="Comentário sobre o espaço (máx 500 caracteres)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Avaliação está ativa"
    )

    class Meta:
        verbose_name = 'Avaliação de Espaço'
        verbose_name_plural = 'Avaliações de Espaços'
        unique_together = ['espaco', 'usuario']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.usuario.first_name} - {self.espaco.nome} ({self.nota}★)"


class ContatoEspaco(TimeStampedModel):
    """
    Model para contatos/mensagens enviadas aos espaços
    """
    espaco = models.ForeignKey(
        Espaco,
        on_delete=models.CASCADE,
        related_name='contatos',
        help_text="Espaço contatado"
    )
    nome = models.CharField(
        max_length=100,
        help_text="Nome da pessoa que está entrando em contato"
    )
    email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Email para resposta"
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
            message='Telefone deve estar no formato (11) 99999-9999'
        )],
        help_text="Telefone para contato"
    )
    assunto = models.CharField(
        max_length=200,
        help_text="Assunto da mensagem"
    )
    mensagem = models.TextField(
        help_text="Mensagem para o espaço"
    )
    is_respondido = models.BooleanField(
        default=False,
        help_text="Contato foi respondido"
    )

    class Meta:
        verbose_name = 'Contato de Espaço'
        verbose_name_plural = 'Contatos de Espaços'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nome} - {self.espaco.nome} ({self.assunto})"


# ===============================================================
# MODEL DE RELACIONAMENTO ESPACO-ESPECIALIDADE
# ===============================================================

class EspacoEspecialidade(TimeStampedModel):
    """
    Model intermediário para relacionamento Espaço-Especialidade
    Permite adicionar informações específicas sobre cada especialidade no espaço
    """
    espaco = models.ForeignKey(
        Espaco,
        on_delete=models.CASCADE,
        related_name='especialidades_detalhadas'
    )
    especialidade = models.ForeignKey(
        Especialidade,
        on_delete=models.CASCADE,
        related_name='espacos_detalhados'
    )
    preco_sessao = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Preço da sessão desta especialidade"
    )
    duracao_sessao = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duração da sessão em minutos"
    )
    observacoes = models.TextField(
        blank=True,
        help_text="Observações específicas sobre esta especialidade no espaço"
    )
    is_destaque = models.BooleanField(
        default=False,
        help_text="Especialidade em destaque neste espaço"
    )

    class Meta:
        verbose_name = 'Especialidade do Espaço'
        verbose_name_plural = 'Especialidades dos Espaços'
        unique_together = ['espaco', 'especialidade']
        ordering = ['-is_destaque', 'especialidade__nome']

    def __str__(self):
        return f"{self.espaco.nome} - {self.especialidade.nome}"