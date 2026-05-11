"""
Título: Models do Sistema de Agendamento de Salas
Descrição: Models para gerenciamento de salas, agendamentos, multas e configurações PIX
Autor: Will
Data: 29/12/2024
"""

from django.db import models
from django.contrib.auth.models import User
from espacos.models import Espaco
from terapeutas.models import Terapeuta
from django.core.validators import MinValueValidator
from decimal import Decimal


# ==========================================
# MODEL: SALA
# ==========================================
class Sala(models.Model):
    """
    Representa uma sala/salão disponível para agendamento em um espaço terapêutico.
    Cada sala possui configurações de horários, valores e comodidades.
    """
    
    # Relacionamento com o espaço
    espaco = models.ForeignKey(
        Espaco,
        on_delete=models.CASCADE,
        related_name='salas',
        verbose_name='Espaço'
    )
    
    # Informações básicas da sala
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome da Sala',
        help_text='Ex: Sala Mandala, Sala Kali, Salão Principal'
    )
    
    capacidade = models.PositiveIntegerField(
        verbose_name='Capacidade',
        help_text='Número máximo de pessoas'
    )
    
    # Configurações financeiras
    valor_sessao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor por Sessão',
        help_text='Valor em R$ para uma sessão'
    )
    
    # Configurações de tempo
    duracao_sessao = models.PositiveIntegerField(
        verbose_name='Duração da Sessão (minutos)',
        help_text='Duração padrão em minutos (ex: 60 para 1 hora)',
        default=60
    )
    
    horario_abertura = models.TimeField(
        verbose_name='Horário de Abertura',
        help_text='Horário em que a sala abre (ex: 08:00)'
    )
    
    horario_fechamento = models.TimeField(
        verbose_name='Horário de Fechamento',
        help_text='Horário em que a sala fecha (ex: 20:00)'
    )
    
    # Mídia
    foto = models.ImageField(
        upload_to='salas/',
        blank=True,
        null=True,
        verbose_name='Foto da Sala'
    )
    
    # Comodidades (mesma estrutura do Espaço)
    comodidades = models.ManyToManyField(
        'espacos.Comodidade',
        blank=True,
        verbose_name='Comodidades',
        help_text='Comodidades disponíveis na sala'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Sala Ativa',
        help_text='Desmarque para desativar a sala temporariamente'
    )

    # Regras de cancelamento
    valor_multa_cancelamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        verbose_name='Valor da Multa por Cancelamento',
        help_text='Multa cobrada se cancelar com menos de 1 hora de antecedência'
    )
    
    prazo_cancelamento_sem_multa = models.PositiveIntegerField(
        default=60,
        verbose_name='Prazo para Cancelamento Sem Multa (minutos)',
        help_text='Tempo mínimo de antecedência para cancelar sem multa (padrão: 60 minutos)'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'
        ordering = ['espaco', 'nome']
        unique_together = ['espaco', 'nome']  # Evita salas duplicadas no mesmo espaço
    
    def __str__(self):
        return f"{self.espaco.nome} - {self.nome}"


# ==========================================
# MODEL: AGENDAMENTO
# ==========================================
class Agendamento(models.Model):
    """
    Representa um agendamento de sala por um terapeuta.
    Controla horários, pagamentos e status do agendamento.
    """
    
    # Choices para status do agendamento
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONFIRMADO', 'Confirmado'),
        ('CANCELADO', 'Cancelado'),
        ('CONCLUIDO', 'Concluído'),
    ]
    
    # Relacionamentos
    sala = models.ForeignKey(
        Sala,
        on_delete=models.CASCADE,
        related_name='agendamentos',
        verbose_name='Sala'
    )
    
    terapeuta = models.ForeignKey(
        Terapeuta,
        on_delete=models.CASCADE,
        related_name='agendamentos',
        verbose_name='Terapeuta'
    )
    
    espaco = models.ForeignKey(
        Espaco,
        on_delete=models.CASCADE,
        related_name='agendamentos',
        verbose_name='Espaço'
    )
    
    # Informações de data e hora
    data = models.DateField(
        verbose_name='Data do Agendamento'
    )
    
    hora_inicio = models.TimeField(
        verbose_name='Hora de Início'
    )
    
    hora_fim = models.TimeField(
        verbose_name='Hora de Término'
    )
    
    # Informações financeiras
    valor_cobrado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor Cobrado',
        help_text='Valor cobrado por este agendamento'
    )
    
    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        verbose_name='Status'
    )
    
    pago = models.BooleanField(
        default=False,
        verbose_name='Pago',
        help_text='Indica se o pagamento foi confirmado'
    )
    
    data_pagamento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data do Pagamento',
        help_text='Data e hora em que o pagamento foi confirmado'
    )
    
    # Informações adicionais
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações',
        help_text='Observações sobre o agendamento (cliente, tipo de atendimento, etc.)'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['-data', '-hora_inicio']
        indexes = [
            models.Index(fields=['data', 'sala']),
            models.Index(fields=['terapeuta', 'status']),
            models.Index(fields=['espaco', 'data']),
        ]
    
    def __str__(self):
        return f"{self.sala.nome} - {self.terapeuta.nome_completo} - {self.data} {self.hora_inicio}"
    
    def pode_cancelar_sem_multa(self):
        """
        Verifica se o agendamento pode ser cancelado sem multa.
        
        Regra: Pode cancelar sem multa se faltar mais tempo que o prazo configurado na sala.
        Padrão: 60 minutos de antecedência
        
        Returns:
            tuple: (pode_cancelar_sem_multa: bool, tempo_restante_minutos: int)
        """
        from django.utils import timezone
        from datetime import datetime
        
        # Criar datetime do agendamento
        data_hora_agendamento = timezone.make_aware(
            datetime.combine(self.data, self.hora_inicio)
        )
        
        # Calcular diferença
        agora = timezone.now()
        diferenca = data_hora_agendamento - agora
        
        # Converter para minutos
        minutos_restantes = int(diferenca.total_seconds() / 60)
        
        # Verificar se ainda falta tempo suficiente
        prazo_minimo = self.sala.prazo_cancelamento_sem_multa
        pode_cancelar = minutos_restantes >= prazo_minimo
        
        return pode_cancelar, minutos_restantes
    
    def calcular_multa_cancelamento(self):
        """
        Calcula o valor da multa caso o cancelamento seja feito fora do prazo.
        
        Returns:
            Decimal: Valor da multa (0.00 se ainda está no prazo)
        """
        pode_cancelar_sem_multa, _ = self.pode_cancelar_sem_multa()
        
        if pode_cancelar_sem_multa:
            return Decimal('0.00')
        
        return self.sala.valor_multa_cancelamento
    
    def cancelar(self, usuario, motivo=''):
        """
        Cancela o agendamento e aplica multa se necessário.
        
        Args:
            usuario: Usuário que está cancelando
            motivo: Motivo do cancelamento
        
        Returns:
            tuple: (sucesso: bool, mensagem: str, valor_multa: Decimal)
        """
        from django.utils import timezone
        
        # Verificar se já está cancelado
        if self.status == 'CANCELADO':
            return False, 'Este agendamento já está cancelado.', Decimal('0.00')
        
        # Verificar se já foi concluído
        if self.status == 'CONCLUIDO':
            return False, 'Não é possível cancelar um agendamento já concluído.', Decimal('0.00')
        
        # Verificar se precisa aplicar multa
        pode_cancelar_sem_multa, minutos_restantes = self.pode_cancelar_sem_multa()
        valor_multa = self.calcular_multa_cancelamento()
        
        # Cancelar o agendamento
        self.status = 'CANCELADO'
        self.save()
        
        # Se houver multa, criar registro
        if valor_multa > 0:
            Multa.objects.create(
                terapeuta=self.terapeuta,
                espaco=self.espaco,
                agendamento=self,
                valor=valor_multa,
                motivo=f'Cancelamento com menos de {self.sala.prazo_cancelamento_sem_multa} minutos de antecedência. '
                       f'Faltavam apenas {minutos_restantes} minutos. Motivo: {motivo}',
                status='PENDENTE'
            )
            
            mensagem = f'Agendamento cancelado. Multa de R$ {valor_multa} aplicada (cancelamento com menos de 1 hora de antecedência).'
        else:
            mensagem = 'Agendamento cancelado com sucesso!'
        
        return True, mensagem, valor_multa


# ==========================================
# MODEL: MULTA
# ==========================================
class Multa(models.Model):
    """
    Representa uma multa aplicada a um terapeuta por descumprimento de regras.
    Ex: sala deixada suja, atraso no pagamento, cancelamento em cima da hora.
    """
    
    # Relacionamentos
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.CASCADE,
        related_name='multas',
        verbose_name='Agendamento Relacionado'
    )
    
    terapeuta = models.ForeignKey(
        Terapeuta,
        on_delete=models.CASCADE,
        related_name='multas',
        verbose_name='Terapeuta'
    )
    
    espaco = models.ForeignKey(
        Espaco,
        on_delete=models.CASCADE,
        related_name='multas_aplicadas',
        verbose_name='Espaço'
    )
    
    # Informações da multa
    motivo = models.CharField(
        max_length=255,
        verbose_name='Motivo da Multa',
        help_text='Ex: Sala deixada suja, Atraso no pagamento, Cancelamento tardio'
    )
    
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor da Multa'
    )
    
    data_aplicacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Aplicação',
        help_text='Data e hora em que a multa foi aplicada'
    )
    
    # Controle de pagamento
    pago = models.BooleanField(
        default=False,
        verbose_name='Pago',
        help_text='Indica se a multa foi paga'
    )
    
    data_pagamento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data do Pagamento',
        help_text='Data e hora em que a multa foi paga'
    )
    
    # Evidência
    foto_evidencia = models.ImageField(
        upload_to='multas/',
        blank=True,
        null=True,
        verbose_name='Foto de Evidência',
        help_text='Foto que comprova o motivo da multa'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Multa'
        verbose_name_plural = 'Multas'
        ordering = ['-data_aplicacao']
    
    def __str__(self):
        return f"Multa - {self.terapeuta.nome_completo} - R$ {self.valor} - {self.motivo}"


# ==========================================
# MODEL: CONFIGURAÇÃO PIX
# ==========================================
class PIXConfig(models.Model):
    """
    Armazena as configurações de chave PIX do espaço para recebimento de pagamentos.
    Cada espaço pode ter apenas uma configuração PIX ativa.
    """
    
    # Tipos de chave PIX
    TIPO_CHAVE_CHOICES = [
        ('CPF', 'CPF'),
        ('CNPJ', 'CNPJ'),
        ('EMAIL', 'E-mail'),
        ('TELEFONE', 'Telefone'),
        ('ALEATORIA', 'Chave Aleatória'),
    ]
    
    # Relacionamento
    espaco = models.OneToOneField(
        Espaco,
        on_delete=models.CASCADE,
        related_name='pix_config',
        verbose_name='Espaço'
    )
    
    # Informações da chave PIX
    tipo_chave = models.CharField(
        max_length=20,
        choices=TIPO_CHAVE_CHOICES,
        verbose_name='Tipo de Chave PIX'
    )
    
    chave_pix = models.CharField(
        max_length=255,
        verbose_name='Chave PIX',
        help_text='Chave PIX para recebimento dos pagamentos'
    )
    
    nome_recebedor = models.CharField(
        max_length=255,
        verbose_name='Nome do Recebedor',
        help_text='Nome que aparecerá no PIX'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Configuração Ativa',
        help_text='Indica se esta configuração está ativa'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Configuração PIX'
        verbose_name_plural = 'Configurações PIX'
    
    def __str__(self):
        return f"PIX - {self.espaco.nome_fantasia} - {self.tipo_chave}"
    
# ===============================================================
# MODEL: VÍNCULO TERAPEUTA ↔ ESPAÇO
# ===============================================================
class VinculoTerapeutaEspaco(models.Model):
    """
    Título: Vínculo entre Terapeuta e Espaço
    Descrição: Controla quais terapeutas podem agendar salas em quais espaços.
               Apenas terapeutas vinculados podem fazer agendamentos.
    
    Regra de Negócio:
    - Terapeuta SÓ pode agendar sala se estiver vinculado ao espaço
    - Vínculo pode ser criado por:
      1. Convite do espaço (futuro)
      2. Solicitação do terapeuta (futuro)
      3. Voucher gratuito (futuro)
      4. Manualmente pelo admin (atual)
    """
    
    # Tipos de vínculo
    TIPO_CHOICES = [
        ('MANUAL', 'Criado Manualmente'),
        ('CONVITE', 'Convite do Espaço'),
        ('SOLICITACAO', 'Solicitação do Terapeuta'),
        ('VOUCHER', 'Voucher Gratuito'),
    ]
    
    # Status do vínculo
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADO', 'Aprovado'),
        ('RECUSADO', 'Recusado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    # Relacionamentos
    espaco = models.ForeignKey(
        'espacos.Espaco',
        on_delete=models.CASCADE,
        related_name='vinculos_terapeutas',
        verbose_name='Espaço'
    )
    
    terapeuta = models.ForeignKey(
        'terapeutas.Terapeuta',
        on_delete=models.CASCADE,
        related_name='vinculos_espacos',
        verbose_name='Terapeuta'
    )
    
    # Tipo e status do vínculo
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='MANUAL',
        verbose_name='Tipo de Vínculo'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='APROVADO',
        verbose_name='Status'
    )
    
    # Datas de controle
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )
    
    data_aprovacao = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data de Aprovação',
        help_text='Data em que o vínculo foi aprovado'
    )
    
    data_cancelamento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data de Cancelamento'
    )
    
    # Voucher (futuro)
    voucher = models.ForeignKey(
        'core.Voucher',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='vinculos',
        verbose_name='Voucher Utilizado',
        help_text='Voucher usado para criar este vínculo (se aplicável)'
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações',
        help_text='Informações adicionais sobre o vínculo'
    )
    
    # Controle de ativação
    is_active = models.BooleanField(
        default=True,
        verbose_name='Vínculo Ativo',
        help_text='Desmarque para desativar o vínculo sem deletar'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Vínculo Terapeuta-Espaço'
        verbose_name_plural = 'Vínculos Terapeuta-Espaço'
        ordering = ['-created_at']
        unique_together = ['espaco', 'terapeuta']  # Evita vínculos duplicados
        indexes = [
            models.Index(fields=['espaco', 'terapeuta', 'status']),
            models.Index(fields=['status', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.terapeuta.nome_completo} → {self.espaco.nome}"
    
    def save(self, *args, **kwargs):
        """
        Ao aprovar o vínculo, registra a data de aprovação
        """
        if self.status == 'APROVADO' and not self.data_aprovacao:
            self.data_aprovacao = timezone.now()
        
        if self.status == 'CANCELADO' and not self.data_cancelamento:
            self.data_cancelamento = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def pode_agendar(self):
        """
        Verifica se o terapeuta pode agendar neste espaço
        """
        return self.status == 'APROVADO' and self.is_active