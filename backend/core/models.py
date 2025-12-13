# ===============================================================
# Título: Models do App Core - Espaço Vital
# Descrição: Modelos base e utilitários do sistema
# Autor: Will | Empresa: Espaço VItal
# Data: 07/09/2025
# ===============================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinLengthValidator, EmailValidator
from django.utils.text import slugify
from ckeditor.fields import RichTextField


class TimeStampedModel(models.Model):
    """
    Modelo abstrato que adiciona campos de timestamp
    Para ser herdado por outros modelos
    """
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True,
        help_text='Data e hora de criação do registro'
    )
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True,
        help_text='Data e hora da última atualização'
    )
    
    class Meta:
        abstract = True


class ActiveManager(models.Manager):
    """
    Manager personalizado para retornar apenas registros ativos
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseModel(TimeStampedModel):
    """
    Modelo base com campos comuns
    Para ser herdado por modelos principais
    """
    is_active = models.BooleanField(
        'Ativo',
        default=True,
        help_text='Indica se o registro está ativo no sistema'
    )
    
    # Managers
    objects = models.Manager()  # Manager padrão
    active = ActiveManager()    # Manager para registros ativos
    
    class Meta:
        abstract = True


class Contact(BaseModel):
    """
    Modelo para formulários de contato
    """
    SUBJECT_CHOICES = [
        ('general', 'Informações Gerais'),
        ('therapist', 'Sou Terapeuta'),
        ('space', 'Tenho um Espaço'),
        ('partnership', 'Parceria'),
        ('support', 'Suporte Técnico'),
        ('complaint', 'Reclamação'),
        ('suggestion', 'Sugestão'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('in_progress', 'Em Andamento'),
        ('resolved', 'Resolvido'),
        ('closed', 'Fechado'),
    ]
    
    name = models.CharField(
        'Nome',
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text='Nome completo do remetente'
    )
    
    email = models.EmailField(
        'E-mail',
        validators=[EmailValidator()],
        help_text='E-mail para resposta'
    )
    
    phone = models.CharField(
        'Telefone',
        max_length=20,
        blank=True,
        help_text='Telefone para contato (opcional)'
    )
    
    subject = models.CharField(
        'Assunto',
        max_length=20,
        choices=SUBJECT_CHOICES,
        default='general',
        help_text='Tipo da mensagem'
    )
    
    message = models.TextField(
        'Mensagem',
        validators=[MinLengthValidator(10)],
        help_text='Descrição detalhada da mensagem'
    )
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Status atual da mensagem'
    )
    
    responded_at = models.DateTimeField(
        'Respondido em',
        null=True,
        blank=True,
        help_text='Data e hora da resposta'
    )
    
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Respondido por',
        help_text='Usuário que respondeu a mensagem'
    )
    
    internal_notes = models.TextField(
        'Notas internas',
        blank=True,
        help_text='Anotações internas da equipe'
    )
    
    class Meta:
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['subject', 'status']),
        ]
    
    def __str__(self):
        return f'{self.name} - {self.get_subject_display()}'
    
    def get_absolute_url(self):
        return reverse('admin:core_contact_change', args=[self.pk])
    
    def mark_as_resolved(self, user=None):
        """
        Marca a mensagem como resolvida
        """
        self.status = 'resolved'
        self.responded_at = timezone.now()
        if user:
            self.responded_by = user
        self.save()


class Newsletter(TimeStampedModel):
    """
    Modelo para inscrições na newsletter
    """
    email = models.EmailField(
        'E-mail',
        unique=True,
        validators=[EmailValidator()],
        help_text='E-mail para receber novidades'
    )
    
    name = models.CharField(
        'Nome',
        max_length=100,
        blank=True,
        help_text='Nome do inscrito (opcional)'
    )
    
    is_active = models.BooleanField(
        'Ativo',
        default=True,
        help_text='Recebendo newsletter'
    )
    
    confirmed_at = models.DateTimeField(
        'Confirmado em',
        null=True,
        blank=True,
        help_text='Data de confirmação do e-mail'
    )
    
    unsubscribed_at = models.DateTimeField(
        'Cancelado em',
        null=True,
        blank=True,
        help_text='Data do cancelamento'
    )
    
    source = models.CharField(
        'Origem',
        max_length=50,
        default='website',
        help_text='Onde se inscreveu'
    )
    
    class Meta:
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletter'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'confirmed_at']),
        ]
    
    def __str__(self):
        return f'{self.email} ({self.name or "Sem nome"})'
    
    def confirm_subscription(self):
        """
        Confirma a inscrição na newsletter
        """
        self.confirmed_at = timezone.now()
        self.is_active = True
        self.save()
    
    def unsubscribe(self):
        """
        Cancela a inscrição na newsletter
        """
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()


class FAQ(BaseModel):
    """
    Modelo para Perguntas Frequentes
    """
    CATEGORY_CHOICES = [
        ('general', 'Geral'),
        ('therapists', 'Para Terapeutas'),
        ('clients', 'Para Clientes'),
        ('spaces', 'Espaços Terapêuticos'),
        ('payments', 'Pagamentos'),
        ('technical', 'Técnico'),
    ]
    
    question = models.CharField(
        'Pergunta',
        max_length=200,
        help_text='Pergunta frequente'
    )
    
    answer = models.TextField(
        'Resposta',
        help_text='Resposta detalhada'
    )
    
    category = models.CharField(
        'Categoria',
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        help_text='Categoria da pergunta'
    )
    
    order = models.PositiveIntegerField(
        'Ordem',
        default=0,
        help_text='Ordem de exibição'
    )
    
    views_count = models.PositiveIntegerField(
        'Visualizações',
        default=0,
        help_text='Número de visualizações'
    )
    
    helpful_count = models.PositiveIntegerField(
        'Útil',
        default=0,
        help_text='Quantas pessoas acharam útil'
    )
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['category', 'order', 'question']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f'{self.question} ({self.get_category_display()})'
    
    def increment_views(self):
        """
        Incrementa o contador de visualizações
        """
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def mark_as_helpful(self):
        """
        Incrementa o contador de "útil"
        """
        self.helpful_count += 1
        self.save(update_fields=['helpful_count'])


class SiteConfiguration(models.Model):
    """
    Modelo para configurações gerais do site
    Singleton pattern - apenas um registro
    """
    site_name = models.CharField(
        'Nome do Site',
        max_length=100,
        default='Espaço Vital'
    )
    
    site_description = models.TextField(
        'Descrição do Site',
        default='Conectando você ao cuidado terapêutico que transforma'
    )
    
    contact_email = models.EmailField(
        'E-mail de Contato',
        default='contato@espacovital.com.br'
    )
    
    contact_phone = models.CharField(
        'Telefone de Contato',
        max_length=20,
        default='+55 (21) 99999-9999'
    )
    
    maintenance_mode = models.BooleanField(
        'Modo Manutenção',
        default=False,
        help_text='Ativa o modo de manutenção do site'
    )
    
    maintenance_message = models.TextField(
        'Mensagem de Manutenção',
        blank=True,
        help_text='Mensagem exibida durante a manutenção'
    )
    
    google_analytics_id = models.CharField(
        'Google Analytics ID',
        max_length=20,
        blank=True,
        help_text='ID do Google Analytics (ex: GA-XXXXXXXXX)'
    )
    
    facebook_pixel_id = models.CharField(
        'Facebook Pixel ID',
        max_length=20,
        blank=True,
        help_text='ID do Facebook Pixel'
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração do Site'
        verbose_name_plural = 'Configurações do Site'
    
    def __str__(self):
        return f'Configurações - {self.site_name}'
    
    def save(self, *args, **kwargs):
        # Garantir que só existe um registro
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValueError('Só pode existir uma configuração do site')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """
        Retorna a configuração atual ou cria uma padrão
        """
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
# ===============================================================
# MODELS DE LOCALIZAÇÃO (COMPARTILHADOS)
# ===============================================================

class Pais(models.Model):
    """
    Modelo para Países
    Sistema preparado para terapeutas em qualquer país
    """
    nome = models.CharField(
        'Nome do País',
        max_length=100,
        unique=True
    )
    codigo = models.CharField(
        'Código ISO',
        max_length=3,
        unique=True,
        help_text='Código ISO do país (ex: BRA, USA, PRT)'
    )
    ddi = models.CharField(
        'DDI',
        max_length=5,
        blank=True,
        help_text='Código de discagem internacional (ex: +55, +1, +351)'
    )
    ativo = models.BooleanField(
        'Ativo',
        default=True,
        help_text='País ativo no sistema'
    )
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Estado(models.Model):
    """
    Modelo para Estados/Províncias/Regiões
    Compartilhado entre Terapeutas, Espaços e outros apps
    """
    nome = models.CharField(
        'Nome do Estado',
        max_length=100
    )
    sigla = models.CharField(
        'Sigla/Código',
        max_length=10,
        help_text='Sigla do estado (ex: RJ, SP, CA, NY)'
    )
    pais = models.ForeignKey(
        Pais,
        on_delete=models.CASCADE,
        related_name='estados',
        verbose_name='País',
        null=True,  # Temporário para migration
        blank=True
    )
    ativo = models.BooleanField(
        'Ativo',
        default=True,
        help_text='Estado ativo no sistema'
    )
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['nome']  # Temporário - vamos ajustar depois
    
    def __str__(self):
        return f'{self.nome} ({self.sigla}) - {self.pais.nome}'


class Cidade(models.Model):
    """
    Modelo para Cidades
    Compartilhado entre Terapeutas, Espaços e outros apps
    Suporta cidades com ou sem estado (país direto)
    """
    nome = models.CharField(
        'Nome da Cidade',
        max_length=100
    )
    estado = models.ForeignKey(
        Estado,
        on_delete=models.CASCADE,
        related_name='cidades',
        verbose_name='Estado',
        null=True,  # Permite cidade sem estado
        blank=True
    )
    pais = models.ForeignKey(
        Pais,
        on_delete=models.CASCADE,
        related_name='cidades_diretas',
        verbose_name='País',
        null=True,  # Obrigatório se não tiver estado
        blank=True,
        help_text='Para países sem estados, vincule a cidade direto ao país'
    )
    ativo = models.BooleanField(
        'Ativo',
        default=True,
        help_text='Cidade ativa no sistema'
    )
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        ordering = ['nome']
    
    def __str__(self):
        if self.estado:
            return f'{self.nome} - {self.estado.sigla}, {self.estado.pais.codigo}'
        elif self.pais:
            return f'{self.nome} - {self.pais.codigo}'
        return self.nome
    
    def get_localizacao_completa(self):
        """Retorna localização completa: Cidade - Estado, País ou Cidade - País"""
        if self.estado:
            return f'{self.nome} - {self.estado.sigla}, {self.estado.pais.nome}'
        elif self.pais:
            return f'{self.nome} - {self.pais.nome}'
        return self.nome
    
    def get_pais(self):
        """Retorna o país da cidade (via estado ou direto)"""
        if self.estado:
            return self.estado.pais
        return self.pais
    
    def clean(self):
        """Validação: cidade deve ter estado OU país"""
        from django.core.exceptions import ValidationError
        
        if not self.estado and not self.pais:
            raise ValidationError('Cidade deve ter um Estado ou um País vinculado.')
        
        if self.estado and self.pais:
            # Se tem estado, o país deve ser o mesmo do estado
            if self.estado.pais != self.pais:
                self.pais = self.estado.pais

# ===============================================================
# MODEL DE ESPECIALIDADE (COMPARTILHADO)
# ===============================================================

class Especialidade(BaseModel):
    """
    Título: Model Especialidade (Terapias)
    Descrição: Model para especialidades/terapias oferecidas
              COMPARTILHADO entre apps: terapeutas, espacos e terapias
              Centralizado no core para evitar duplicação
    Autor: Will
    Data: 2024
    Última Atualização: Novembro 2025 - Adicionado campo foto e beneficios
    """
    # Identificação básica
    nome = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome da especialidade/terapia"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        help_text="Slug para URLs amigáveis"
    )
    
    # Imagem da terapia (NOVO - para página de terapias)
    foto = models.ImageField(
        upload_to='terapias/',
        null=True,
        blank=True,
        help_text="Imagem representativa da terapia (ideal: 800x600px)"
    )
    
    # Descrições
    descricao_curta = models.CharField(
        max_length=700,
        blank=True,
        help_text="Descrição resumida da especialidade (para cards)"
    )
    descricao_completa = models.TextField(
        blank=True,
        help_text="Descrição detalhada da especialidade (para página individual)"
    )
    
    # Benefícios (NOVO - para página de terapias)
    beneficios = models.TextField(
        blank=True,
        help_text="Lista de benefícios da terapia (use marcadores • para listar)"
    )
    
    # Categorização
    categoria = models.CharField(
        max_length=50,
        blank=True,
        help_text="Categoria da terapia (ex: Massagem, Energética)"
    )
    
    # Customização visual
    cor_destaque = models.CharField(
        max_length=7,
        blank=True,
        default='#6C63FF',
        help_text="Cor em hexadecimal para destaque (#RRGGBB)"
    )
    
    # Ordenação e destaque
    ordem = models.IntegerField(
        default=0,
        help_text="Ordem de exibição (menor aparece primeiro)"
    )
    destaque = models.BooleanField(
        default=False,
        help_text="Aparece nas 10 terapias em destaque na página de Terapias"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Especialidade está ativa no sistema"
    )

    # ===============================================================
    # NOVO CAMPO: Conteúdo Extenso com Editor Rico
    # ===============================================================
    conteudo_completo = RichTextField(
        verbose_name="Conteúdo Completo (Editor Rico)",
        blank=True,
        null=True,
        help_text="""
        Conteúdo detalhado da terapia com seções estruturadas:
        - Introdução
        - O que é a terapia
        - Em que a terapia pode ajudar
        - O que esperar numa sessão
        - O que sentirá após uma sessão
        - Quantas sessões são necessárias
        - Como escolher um terapeuta
        """
    )
    
    # Sites de referência (opcional)
    sites_referencia = models.TextField(
        verbose_name="Sites de Referência",
        blank=True,
        null=True,
        help_text="URLs de sites de referência sobre a terapia (uma por linha)"
    )

    class Meta:
        verbose_name = 'Especialidade / Terapia'
        verbose_name_plural = 'Especialidades / Terapias'
        ordering = ['-destaque', 'ordem', 'nome']
        indexes = [
            models.Index(fields=['destaque', 'is_active']),
            models.Index(fields=['ordem']),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        """
        Gera slug automático baseado no nome se não existir
        """
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """
        Retorna URL da página individual da terapia
        """
        from django.urls import reverse
        return reverse('terapias:detalhe', kwargs={'slug': self.slug})
    
class SugestaoTerapia(BaseModel):
    """
    Model para armazenar sugestões de terapias dos usuários
    Autor: Will
    Data: 08/11/2025
    """
    nome = models.CharField(
        'Nome',
        max_length=200,
        help_text='Nome completo do usuário'
    )
    
    email = models.EmailField(
        'E-mail',
        help_text='E-mail para contato'
    )
    
    nome_terapia = models.CharField(
        'Nome da Terapia',
        max_length=200,
        help_text='Nome da terapia sugerida'
    )
    
    descricao = models.TextField(
        'Descrição',
        help_text='Breve descrição sobre a terapia'
    )
    
    lida = models.BooleanField(
        'Lida',
        default=False,
        help_text='Indica se a sugestão foi lida pela equipe'
    )
    
    class Meta:
        verbose_name = 'Sugestão de Terapia'
        verbose_name_plural = 'Sugestões de Terapias'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.nome_terapia} - {self.nome}'
    
# ===============================================================
# MODELS DE SISTEMA DE ASSINATURAS E VOUCHERS
# ===============================================================

class PlanoChoices(models.TextChoices):
    """
    Choices para tipos de plano de assinatura
    Baseado no sistema de planos já definido
    """
    GRATUITO_FILIADO = 'gratuito_filiado', 'Gratuito Filiado a Espaço'
    BASIC = 'basic', 'Basic'
    PREMIUM_A = 'premium_a', 'Premium A (Terapeuta)'
    PREMIUM_S = 'premium_s', 'Premium S (Espaço)'
    PREMIUM_S_PLUS = 'premium_s_plus', 'Premium S+ (Espaço com Gerenciamento)'
    COMBO_A_S = 'combo_a_s', 'Combo Premium A + S'
    COMBO_A_S_PLUS = 'combo_a_s_plus', 'Combo Premium A + S+'


class StatusAssinaturaChoices(models.TextChoices):
    """
    Status de uma assinatura
    """
    TRIAL = 'trial', 'Período de Teste'
    ACTIVE = 'active', 'Ativa'
    SUSPENDED = 'suspended', 'Suspensa'
    CANCELLED = 'cancelled', 'Cancelada'
    EXPIRED = 'expired', 'Expirada'


class TipoDescontoVoucher(models.TextChoices):
    """
    Tipo de desconto do voucher
    """
    PERCENTUAL = 'percentual', 'Percentual'
    VALOR_FIXO = 'valor_fixo', 'Valor Fixo'
    GRATUIDADE = 'gratuidade', 'Período de Gratuidade'


class Plano(BaseModel):
    """
    Model para Planos de Assinatura
    Define os planos disponíveis no sistema
    """
    nome = models.CharField(
        'Nome do Plano',
        max_length=100,
        choices=PlanoChoices.choices,
        unique=True
    )
    nome_exibicao = models.CharField(
        'Nome para Exibição',
        max_length=100,
        help_text='Nome que aparece na interface'
    )
    descricao = models.TextField(
        'Descrição',
        help_text='Descrição resumida do plano'
    )
    valor = models.DecimalField(
        'Valor Mensal',
        max_digits=10,
        decimal_places=2,
        help_text='Valor mensal em R$'
    )
    dias_trial = models.PositiveIntegerField(
        'Dias de Trial',
        default=15,
        help_text='Quantidade de dias gratuitos de teste'
    )
    
    # Funcionalidades do plano
    destaque_busca = models.BooleanField(
        'Destaque nas Buscas',
        default=False,
        help_text='Perfil aparece em destaque nas buscas'
    )
    badge_verificado = models.BooleanField(
        'Badge Verificado',
        default=False,
        help_text='Exibe badge de verificado no perfil'
    )
    estatisticas_avancadas = models.BooleanField(
        'Estatísticas Avançadas',
        default=False,
        help_text='Acesso a estatísticas avançadas'
    )
    suporte_prioritario = models.BooleanField(
        'Suporte Prioritário',
        default=False,
        help_text='Atendimento prioritário'
    )
    limite_fotos = models.PositiveIntegerField(
        'Limite de Fotos',
        default=5,
        help_text='Quantidade máxima de fotos no perfil'
    )
    vinculos_espacos = models.PositiveIntegerField(
        'Vínculos com Espaços',
        default=1,
        help_text='Quantidade de espaços que pode se vincular'
    )
    gerenciamento_salas = models.BooleanField(
        'Gerenciamento de Salas',
        default=False,
        help_text='Permite gerenciar salas (para espaços)'
    )
    divulgacao_perfil = models.BooleanField(
        'Divulgação de Perfil',
        default=True,
        help_text='Perfil aparece publicamente no site'
    )
    
    # Controle de disponibilidade
    max_usuarios = models.PositiveIntegerField(
        'Máximo de Usuários',
        null=True,
        blank=True,
        help_text='Limite de usuários neste plano (null = ilimitado)'
    )
    ordem_exibicao = models.PositiveIntegerField(
        'Ordem de Exibição',
        default=0,
        help_text='Ordem de exibição na página de planos'
    )
    recomendado = models.BooleanField(
        'Plano Recomendado',
        default=False,
        help_text='Destacar como plano recomendado'
    )
    
    class Meta:
        verbose_name = 'Plano de Assinatura'
        verbose_name_plural = 'Planos de Assinatura'
        ordering = ['ordem_exibicao', 'valor']
    
    def __str__(self):
        return f"{self.nome_exibicao} - R$ {self.valor}"
    
    @property
    def total_assinantes(self):
        """
        Retorna total de assinantes ativos neste plano
        """
        return self.assinaturas.filter(
            status__in=[StatusAssinaturaChoices.ACTIVE, StatusAssinaturaChoices.TRIAL]
        ).count()
    
    @property
    def vagas_disponiveis(self):
        """
        Retorna quantidade de vagas disponíveis
        """
        if self.max_usuarios is None:
            return None  # Ilimitado
        return max(0, self.max_usuarios - self.total_assinantes)
    
    @property
    def tem_vagas(self):
        """
        Verifica se ainda há vagas disponíveis
        """
        if self.max_usuarios is None:
            return True
        return self.total_assinantes < self.max_usuarios


class Voucher(BaseModel):
    """
    Model para Vouchers/Cupons de Desconto
    Gerenciado pelo admin para dar descontos/gratuidade
    """
    codigo = models.CharField(
        'Código do Voucher',
        max_length=50,
        unique=True,
        help_text='Código único do voucher (ex: BEMVINDO2024)'
    )
    descricao = models.CharField(
        'Descrição',
        max_length=200,
        help_text='Descrição interna do voucher'
    )
    
    # Tipo de desconto
    tipo_desconto = models.CharField(
        'Tipo de Desconto',
        max_length=20,
        choices=TipoDescontoVoucher.choices,
        default=TipoDescontoVoucher.PERCENTUAL
    )
    valor_desconto = models.DecimalField(
        'Valor do Desconto',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Valor em R$ (se fixo) ou % (se percentual)'
    )
    dias_gratuidade = models.PositiveIntegerField(
        'Dias de Gratuidade',
        default=15,
        help_text='Quantidade de dias grátis (15 a 90)'
    )
    
    # Validade
    data_inicio = models.DateField(
        'Data de Início',
        help_text='Data a partir da qual o voucher é válido'
    )
    data_expiracao = models.DateField(
        'Data de Expiração',
        help_text='Data até quando o voucher é válido'
    )
    
    # Limites de uso
    limite_usos = models.PositiveIntegerField(
        'Limite de Usos',
        null=True,
        blank=True,
        help_text='Quantidade máxima de usos (null = ilimitado)'
    )
    usos_realizados = models.PositiveIntegerField(
        'Usos Realizados',
        default=0,
        editable=False
    )
    
    # Planos aplicáveis
    planos_aplicaveis = models.ManyToManyField(
        Plano,
        related_name='vouchers',
        verbose_name='Planos Aplicáveis',
        help_text='Planos em que o voucher pode ser usado'
    )
    
    # Controle
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vouchers_criados',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Voucher'
        verbose_name_plural = 'Vouchers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.codigo} ({self.get_tipo_desconto_display()})"
    
    @property
    def esta_valido(self):
        """
        Verifica se o voucher está válido (data e limite de usos)
        """
        from django.utils import timezone
        hoje = timezone.now().date()
        
        # Verifica data
        if hoje < self.data_inicio or hoje > self.data_expiracao:
            return False
        
        # Verifica limite de usos
        if self.limite_usos is not None and self.usos_realizados >= self.limite_usos:
            return False
        
        return self.is_active
    
    def calcular_desconto(self, valor_plano):
        """
        Calcula o valor do desconto sobre um valor de plano
        """
        if self.tipo_desconto == TipoDescontoVoucher.PERCENTUAL:
            return (valor_plano * self.valor_desconto) / 100
        elif self.tipo_desconto == TipoDescontoVoucher.VALOR_FIXO:
            return min(self.valor_desconto, valor_plano)
        else:  # GRATUIDADE
            return valor_plano  # Desconto total durante período
    
    def registrar_uso(self):
        """
        Registra um uso do voucher
        """
        self.usos_realizados += 1
        self.save(update_fields=['usos_realizados'])


class Assinatura(BaseModel):
    """
    Model para Assinaturas dos Usuários
    Relaciona usuário com plano escolhido
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assinaturas',
        verbose_name='Usuário'
    )
    plano = models.ForeignKey(
        Plano,
        on_delete=models.PROTECT,
        related_name='assinaturas',
        verbose_name='Plano'
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusAssinaturaChoices.choices,
        default=StatusAssinaturaChoices.TRIAL
    )
    
    # Datas
    data_inicio = models.DateField(
        'Data de Início',
        help_text='Data de início da assinatura'
    )
    data_fim_trial = models.DateField(
        'Data Fim do Trial',
        null=True,
        blank=True,
        help_text='Data de término do período de teste'
    )
    data_proxima_cobranca = models.DateField(
        'Data Próxima Cobrança',
        null=True,
        blank=True,
        help_text='Data da próxima cobrança'
    )
    data_cancelamento = models.DateField(
        'Data de Cancelamento',
        null=True,
        blank=True,
        help_text='Data em que a assinatura foi cancelada'
    )
    
    # Voucher utilizado
    voucher_utilizado = models.ForeignKey(
        Voucher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assinaturas',
        verbose_name='Voucher Utilizado'
    )
    
    # Observações
    observacoes = models.TextField(
        'Observações',
        blank=True,
        help_text='Observações sobre a assinatura'
    )
    
    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.plano.nome_exibicao} ({self.get_status_display()})"
    
    @property
    def esta_ativa(self):
        """
        Verifica se a assinatura está ativa
        """
        return self.status in [StatusAssinaturaChoices.ACTIVE, StatusAssinaturaChoices.TRIAL]
    
    @property
    def em_trial(self):
        """
        Verifica se está em período de teste
        """
        from django.utils import timezone
        if self.status == StatusAssinaturaChoices.TRIAL and self.data_fim_trial:
            return timezone.now().date() <= self.data_fim_trial
        return False
    
    def cancelar(self):
        """
        Cancela a assinatura
        """
        from django.utils import timezone
        self.status = StatusAssinaturaChoices.CANCELLED
        self.data_cancelamento = timezone.now().date()
        self.save(update_fields=['status', 'data_cancelamento'])
    
    def ativar(self):
        """
        Ativa a assinatura
        """
        self.status = StatusAssinaturaChoices.ACTIVE
        self.save(update_fields=['status'])


class HistoricoAssinatura(TimeStampedModel):
    """
    Model para Histórico de Alterações nas Assinaturas
    Registra mudanças de plano, status, etc.
    """
    assinatura = models.ForeignKey(
        Assinatura,
        on_delete=models.CASCADE,
        related_name='historico',
        verbose_name='Assinatura'
    )
    acao = models.CharField(
        'Ação',
        max_length=100,
        help_text='Descrição da ação realizada'
    )
    detalhes = models.TextField(
        'Detalhes',
        blank=True,
        help_text='Detalhes adicionais da ação'
    )
    plano_anterior = models.ForeignKey(
        Plano,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_anterior',
        verbose_name='Plano Anterior'
    )
    plano_novo = models.ForeignKey(
        Plano,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_novo',
        verbose_name='Plano Novo'
    )
    realizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='acoes_assinatura',
        verbose_name='Realizado por'
    )
    
    class Meta:
        verbose_name = 'Histórico de Assinatura'
        verbose_name_plural = 'Históricos de Assinaturas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.assinatura.usuario.get_full_name()} - {self.acao} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"