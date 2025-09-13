# ===============================================================
# Título: Models do App Core - Espaço Vital
# Descrição: Modelos base e utilitários do sistema
# Autor: Will
# Data: 07/09/2025
# ===============================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinLengthValidator, EmailValidator
from django.utils.text import slugify


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