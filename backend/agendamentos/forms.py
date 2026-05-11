# ===============================================================
# Título: Forms do Sistema de Agendamento
# Descrição: Formulários para agendamento de salas por terapeutas
# Autor: Will
# Data: 03/01/2026
# ===============================================================

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Agendamento, Sala, VinculoTerapeutaEspaco
from espacos.models import Espaco


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
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'min': timezone.now().date().isoformat()
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
        
        # ===== VALIDAÇÃO 1: Data não pode ser no passado =====
        hoje = timezone.now().date()
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
        
        if hora_inicio >= sala.horario_fechamento:
            raise ValidationError(
                f'A sala fecha às {sala.horario_fechamento.strftime("%H:%M")}. '
                f'Escolha um horário anterior.'
            )
        
        # ===== VALIDAÇÃO 4: Calcular hora_fim =====
        hora_inicio_dt = datetime.combine(data, hora_inicio)
        hora_fim_dt = hora_inicio_dt + timedelta(minutes=sala.duracao_sessao)
        cleaned_data['hora_fim'] = hora_fim_dt.time()
        
        # Verificar se hora_fim não ultrapassa horário de fechamento
        if cleaned_data['hora_fim'] > sala.horario_fechamento:
            raise ValidationError(
                f'A sessão terminaria às {cleaned_data["hora_fim"].strftime("%H:%M")}, '
                f'após o horário de fechamento da sala ({sala.horario_fechamento.strftime("%H:%M")}). '
                f'Escolha um horário mais cedo ou uma sala com horário estendido.'
            )
        
        # ===== VALIDAÇÃO 5: Verificar conflito de horários =====
        conflitos = Agendamento.objects.filter(
            sala=sala,
            data=data,
            status__in=['PENDENTE', 'CONFIRMADO']
        ).exclude(pk=self.instance.pk if self.instance else None)
        
        for agendamento in conflitos:
            # Verificar sobreposição de horários
            # Há conflito se: (novo_inicio < existente_fim) E (novo_fim > existente_inicio)
            if not (cleaned_data['hora_fim'] <= agendamento.hora_inicio or 
                    hora_inicio >= agendamento.hora_fim):
                raise ValidationError(
                    f'❌ Conflito de horário! Já existe um agendamento das '
                    f'{agendamento.hora_inicio.strftime("%H:%M")} às '
                    f'{agendamento.hora_fim.strftime("%H:%M")} nesta sala. '
                    f'Escolha outro horário ou outra sala.'
                )
        
        # ===== VALIDAÇÃO 6: Calcular valor =====
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