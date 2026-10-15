# ===============================================================
# Título: Forms do Sistema de Agendamento
# Descrição: Formulários para agendamento de salas por terapeutas
# ===============================================================

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta
from .models import Agendamento, Sala, VinculoTerapeutaEspaco
from espacos.models import Espaco


def validar_horario_agendamento(sala, data, hora_inicio, ignorar_pk=None):
    """
    Regras de horário compartilhadas entre a criação e a edição.

    Valida, nesta ordem: data no passado, antecedência mínima de 30
    minutos, horário de funcionamento da sala, sessão que passa do
    fechamento (inclusive virando a meia-noite) e conflito com outro
    agendamento. Devolve a hora_fim calculada pela duração da sala.

    ignorar_pk: pk do próprio agendamento na edição, para que ele não
    conflite consigo mesmo.
    """
    # ===== VALIDAÇÃO 1: Data não pode ser no passado =====
    # Usa o dia local (America/Sao_Paulo), não o dia em UTC
    hoje = timezone.localdate()
    if data < hoje:
        raise ValidationError('A data do agendamento não pode ser no passado.')

    # ===== VALIDAÇÃO 2: Antecedência mínima de 30 minutos =====
    agora = timezone.now()
    data_hora_agendamento = timezone.make_aware(
        datetime.combine(data, hora_inicio)
    )

    diferenca = data_hora_agendamento - agora

    if diferenca.total_seconds() < 1800:  # 1800 segundos = 30 minutos
        raise ValidationError(
            'Agendamentos devem ser feitos com pelo menos 30 minutos de antecedência. '
            'Para agendamentos urgentes, entre em contato diretamente com o espaço.'
        )

    # ===== VALIDAÇÃO 3: Horário dentro do funcionamento da sala =====
    if hora_inicio < sala.horario_abertura:
        raise ValidationError(
            f'A sala só abre às {sala.horario_abertura.strftime("%H:%M")}. '
            f'Escolha um horário a partir deste.'
        )

    # Compara datetimes completos: uma sessão que cruza a meia-noite
    # volta para 00:xx como time e parecia estar "antes" do fechamento
    # O fechamento vem em minutos desde 00:00 do dia; 00:00 vale 24:00
    # (fim do dia), então uma sala que fecha à meia-noite continua usável
    hora_inicio_dt = datetime.combine(data, hora_inicio)
    fechamento_dt = datetime.combine(data, time.min) + timedelta(
        minutes=sala.fechamento_em_minutos
    )

    if hora_inicio_dt >= fechamento_dt:
        raise ValidationError(
            f'A sala fecha às {sala.horario_fechamento.strftime("%H:%M")}. '
            f'Escolha um horário anterior.'
        )

    # ===== VALIDAÇÃO 4: Calcular hora_fim =====
    hora_fim_dt = hora_inicio_dt + timedelta(minutes=sala.duracao_sessao)
    hora_fim = hora_fim_dt.time()

    # Sessão que passa do fechamento (inclusive virando o dia) é barrada
    if hora_fim_dt > fechamento_dt:
        raise ValidationError(
            f'A sessão terminaria às {hora_fim.strftime("%H:%M")}, '
            f'após o horário de fechamento da sala ({sala.horario_fechamento.strftime("%H:%M")}). '
            f'Escolha um horário mais cedo ou uma sala com horário estendido.'
        )

    # ===== VALIDAÇÃO 5: Verificar conflito de horários =====
    conflitos = Agendamento.objects.filter(
        sala=sala,
        data=data,
        status__in=['PENDENTE', 'CONFIRMADO']
    ).exclude(pk=ignorar_pk)

    # Compara em minutos desde 00:00. Uma sessão que termina à meia-noite
    # tem hora_fim 00:00, que como time parece "antes" do início; por isso
    # o fim que não passa do início conta como o fim do dia (+24h)
    novo_inicio = hora_inicio.hour * 60 + hora_inicio.minute
    novo_fim = novo_inicio + sala.duracao_sessao

    for agendamento in conflitos:
        # Verificar sobreposição de horários
        # Há conflito se: (novo_inicio < existente_fim) E (novo_fim > existente_inicio)
        existente_inicio = agendamento.hora_inicio.hour * 60 + agendamento.hora_inicio.minute
        existente_fim = agendamento.hora_fim.hour * 60 + agendamento.hora_fim.minute
        if existente_fim <= existente_inicio:
            existente_fim += 24 * 60

        if not (novo_fim <= existente_inicio or
                novo_inicio >= existente_fim):
            raise ValidationError(
                f'❌ Conflito de horário! Já existe um agendamento das '
                f'{agendamento.hora_inicio.strftime("%H:%M")} às '
                f'{agendamento.hora_fim.strftime("%H:%M")} nesta sala. '
                f'Escolha outro horário ou outra sala.'
            )

    return hora_fim


class AgendamentoForm(forms.ModelForm):
    """
    Formulário para criar novo agendamento de sala.
    
    Regras:
    - Terapeuta DEVE estar vinculado ao espaço
    - Sala deve estar ativa
    - Data não pode ser no passado
    - Horário deve estar dentro do funcionamento da sala
    - Não pode ter conflito com outros agendamentos
    """
    
    # Campo extra para selecionar o espaço primeiro
    espaco = forms.ModelChoiceField(
        queryset=Espaco.objects.none(),  # Será preenchido no __init__
        empty_label="Selecione o espaço",
        label="Espaço Terapêutico",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'onchange': 'atualizarSalas(this.value)'
        }),
        help_text='Apenas espaços onde você está vinculado'
    )
    
    class Meta:
        model = Agendamento
        fields = ['sala', 'data', 'hora_inicio', 'observacoes']
        widgets = {
            'sala': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'data': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Ex: Cliente João Silva - Sessão de Reiki'
            })
        }
        labels = {
            'sala': 'Sala',
            'data': 'Data do Agendamento',
            'hora_inicio': 'Horário de Início',
            'observacoes': 'Observações (Cliente, tipo de atendimento)'
        }
        help_texts = {
            'observacoes': 'Descreva o tipo de atendimento e cliente (opcional)'
        }
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa o formulário filtrando espaços e salas baseado no terapeuta
        """
        self.terapeuta = kwargs.pop('terapeuta', None)
        super().__init__(*args, **kwargs)

        # Data mínima calculada a cada criação do formulário (dia local),
        # e não na importação do módulo, para não ficar velha no servidor
        self.fields['data'].widget.attrs['min'] = timezone.localdate().isoformat()
        
        if not self.terapeuta:
            raise ValueError('O formulário requer um terapeuta')
        
        # ===== FILTRAR APENAS ESPAÇOS VINCULADOS AO TERAPEUTA =====
        espacos_vinculados = VinculoTerapeutaEspaco.objects.filter(
            terapeuta=self.terapeuta,
            status='APROVADO',
            is_active=True
        ).values_list('espaco_id', flat=True)
        
        self.fields['espaco'].queryset = Espaco.objects.filter(
            id__in=espacos_vinculados,
            is_active=True
        ).order_by('nome')
        
        # Se estiver editando, preencher o campo espaco
        if self.instance and self.instance.pk:
            self.fields['espaco'].initial = self.instance.sala.espaco
            self.fields['sala'].queryset = Sala.objects.filter(
                espaco=self.instance.sala.espaco,
                is_active=True
            ).order_by('nome')
        else:
            # Ao criar, inicialmente não mostrar salas
            self.fields['sala'].queryset = Sala.objects.none()
        
        # Se vier espaco_id no data (POST/GET), filtrar salas
        if 'espaco' in self.data:
            try:
                espaco_id = int(self.data.get('espaco'))
                
                # Verificar se terapeuta tem vínculo com este espaço
                vinculo = VinculoTerapeutaEspaco.objects.filter(
                    terapeuta=self.terapeuta,
                    espaco_id=espaco_id,
                    status='APROVADO',
                    is_active=True
                ).first()
                
                if vinculo:
                    self.fields['sala'].queryset = Sala.objects.filter(
                        espaco_id=espaco_id,
                        is_active=True
                    ).order_by('nome')
                else:
                    self.fields['sala'].queryset = Sala.objects.none()
                    
            except (ValueError, TypeError):
                pass
    
    def clean_espaco(self):
        """
        Valida se o terapeuta está vinculado ao espaço
        """
        espaco = self.cleaned_data.get('espaco')
        
        if not espaco:
            return espaco
        
        # Verificar vínculo
        vinculo = VinculoTerapeutaEspaco.objects.filter(
            terapeuta=self.terapeuta,
            espaco=espaco,
            status='APROVADO',
            is_active=True
        ).first()
        
        if not vinculo:
            raise ValidationError(
                f'Você não está vinculado ao espaço "{espaco.nome}". '
                f'Entre em contato com o espaço para solicitar vínculo.'
            )
        
        return espaco
    
    def clean_sala(self):
        """
        Valida se a sala está ativa e pertence ao espaço selecionado
        """
        sala = self.cleaned_data.get('sala')
        espaco = self.cleaned_data.get('espaco')
        
        if not sala:
            return sala
        
        # Verificar se sala pertence ao espaço
        if espaco and sala.espaco != espaco:
            raise ValidationError('A sala selecionada não pertence ao espaço escolhido.')
        
        # Verificar se sala está ativa
        if not sala.is_active:
            raise ValidationError('Esta sala não está disponível para agendamentos no momento.')
        
        return sala
    
    def clean(self):
        """
        Validações customizadas gerais
        """
        cleaned_data = super().clean()
        sala = cleaned_data.get('sala')
        data = cleaned_data.get('data')
        hora_inicio = cleaned_data.get('hora_inicio')
        
        if not all([sala, data, hora_inicio]):
            return cleaned_data
        
        # Regras de horário compartilhadas com a edição (passado,
        # antecedência, funcionamento da sala, meia-noite e conflito)
        cleaned_data['hora_fim'] = validar_horario_agendamento(
            sala, data, hora_inicio, ignorar_pk=self.instance.pk
        )
        
        # ===== Calcular valor =====
        cleaned_data['valor_cobrado'] = sala.valor_sessao
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Salva o agendamento com dados calculados
        """
        agendamento = super().save(commit=False)
        
        # Definir terapeuta
        agendamento.terapeuta = self.terapeuta
        
        # Definir espaço
        agendamento.espaco = agendamento.sala.espaco
        
        # Definir hora_fim (já calculada no clean)
        agendamento.hora_fim = self.cleaned_data['hora_fim']
        
        # Definir valor (já calculado no clean)
        agendamento.valor_cobrado = self.cleaned_data['valor_cobrado']
        
        # Status inicial: PENDENTE (aguardando pagamento)
        agendamento.status = 'PENDENTE'
        agendamento.pago = False
        
        if commit:
            agendamento.save()
        
        return agendamento


class AgendamentoEditarForm(forms.ModelForm):
    """
    Formulário para editar um agendamento PENDENTE existente.

    Só data, hora_inicio e observacoes mudam pela tela. Sala, espaço,
    terapeuta, status, pago e valor_cobrado nunca mudam, e hora_fim é
    recalculada pela duração da sala. Valem as mesmas regras de horário
    da criação, sem conflitar com o próprio agendamento.

    Se data e hora_inicio não mudaram (só observações), a validação de
    horário é pulada: o terapeuta pode ajustar o texto de um agendamento
    que já está dentro dos 30 minutos ou que ficou no passado.
    """

    class Meta:
        model = Agendamento
        fields = ['data', 'hora_inicio', 'observacoes']
        widgets = {
            'data': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'block w-full min-h-[44px] rounded-md border-gray-300 shadow-sm focus:border-[#1E5C5C] focus:ring-[#1E5C5C]',
                },
            ),
            'hora_inicio': forms.TimeInput(
                format='%H:%M',
                attrs={
                    'type': 'time',
                    'class': 'block w-full min-h-[44px] rounded-md border-gray-300 shadow-sm focus:border-[#1E5C5C] focus:ring-[#1E5C5C]',
                },
            ),
            'observacoes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Ex: tipo de atendimento, necessidades especiais...',
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-[#1E5C5C] focus:ring-[#1E5C5C]',
            }),
        }

    def clean(self):
        """
        Valida o horário pelas mesmas regras da criação, usando a sala
        do próprio agendamento (a sala nunca vem do POST)
        """
        cleaned_data = super().clean()
        data = cleaned_data.get('data')
        hora_inicio = cleaned_data.get('hora_inicio')

        if not all([data, hora_inicio]):
            return cleaned_data

        horario_mudou = (
            'data' in self.changed_data or 'hora_inicio' in self.changed_data
        )

        if horario_mudou:
            self._hora_fim = validar_horario_agendamento(
                self.instance.sala, data, hora_inicio,
                ignorar_pk=self.instance.pk,
            )
        else:
            # Só observações: mantém o horário que já estava gravado
            self._hora_fim = self.instance.hora_fim

        return cleaned_data

    def save(self, commit=True):
        """
        Grava só os campos editáveis. O update_fields impede que uma
        tela aberta há tempo reverta status ou pago alterados depois.
        """
        agendamento = super().save(commit=False)
        agendamento.hora_fim = self._hora_fim

        if commit:
            agendamento.save(update_fields=[
                'data', 'hora_inicio', 'hora_fim', 'observacoes', 'updated_at',
            ])

        return agendamento
