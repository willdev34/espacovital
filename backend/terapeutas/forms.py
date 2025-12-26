# ===============================================================
# Título: Forms do App Terapeutas - Espaço Vital
# Descrição: Formulários para cadastro e edição de terapeutas
# Autor: Will
# Data: 14/12/2025
# ===============================================================

from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import Terapeuta, FotoGaleriaTerapeuta
from core.models import Pais, Estado, Cidade, Especialidade
import re
from ckeditor.widgets import CKEditorWidget


class TerapeutaEditarPerfilForm(forms.ModelForm):
    """
    Formulário completo para edição de perfil do terapeuta
    Usado no dashboard privado
    """
    
    # ===== Campos customizados para JSONField =====
    
    TIPOS_SESSAO_CHOICES = [
        ('presencial', 'Presencial'),
        ('online', 'On-line'),
        ('domicilio', 'Domicílio'),
    ]
    
    PARA_QUEM_CHOICES = [
        ('qualquer_um', 'Qualquer um'),
        ('adultos', 'Adultos'),
        ('criancas', 'Crianças'),
        ('idosos', 'Idosos'),
        ('casais', 'Casais'),
        ('grupos', 'Grupos'),
    ]
    
    tipos_sessao = forms.MultipleChoiceField(
        label='Tipos de Sessão',
        choices=TIPOS_SESSAO_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-primary'
        }),
        required=False,
        help_text='Selecione os tipos de sessão que você oferece'
    )
    
    para_quem = forms.MultipleChoiceField(
        label='Para Quem é a Terapia?',
        choices=PARA_QUEM_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-primary'
        }),
        required=False,
        help_text='Selecione o público-alvo dos seus atendimentos'
    )
    
    # ===== Campo CPF/CNPJ =====
    
    cpf_cnpj = forms.CharField(
        label='CPF ou CNPJ',
        max_length=18,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': '000.000.000-00 ou 00.000.000/0000-00',
            'id': 'id_cpf_cnpj'
        }),
        help_text='Digite apenas números. Será formatado automaticamente.'
    )
    
    # ===== Especialidades (ManyToMany) =====
    
    especialidades = forms.ModelMultipleChoiceField(
        label='Especialidades/Terapias',
        queryset=Especialidade.objects.filter(is_active=True).order_by('nome'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-primary'
        }),
        required=False,
        help_text='Selecione suas especialidades'
    )
    
    # ===== Cidades de Atendimento (ManyToMany) =====
    
    cidades_atendimento = forms.ModelMultipleChoiceField(
        label='Cidades de Atendimento',
        queryset=Cidade.objects.filter(ativo=True).order_by('nome'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-primary'
        }),
        required=False,
        help_text='Selecione as cidades onde você atende'
    )
    
    class Meta:
        model = Terapeuta
        fields = [
            # Informações Básicas
            'nome_completo', 'nome_exibicao', 
            'email_profissional', 'whatsapp', 'whatsapp_ativo',
            
            # Localização
            'pais', 'estado', 'cidade_principal', 'cidade_texto',
            'bairro', 'endereco',
            
            # Informações Profissionais
            'registro_profissional', 'formacao', 'experiencia_anos',
            
            # Descrições
            'bio_curta', 'bio_completa', 'metodologia',
            
            # Redes Sociais
            'instagram', 'facebook', 'tiktok', 'youtube',
            
            # Configurações
            'acessibilidade',
            
            # Fotos
            'foto_perfil', 'foto_capa',
        ]
        
        widgets = {
            # Informações Básicas
            'nome_completo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Seu nome completo'
            }),
            'nome_exibicao': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Como prefere ser chamado'
            }),
            'email_profissional': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'seuemail@exemplo.com'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '(21) 98765-4321',
                'id': 'id_whatsapp'
            }),
            
            # Localização
            'pais': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'id': 'id_pais'
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'id': 'id_estado',
                'hx-get': '/core/cidades-por-estado/',
                'hx-target': '#id_cidade_principal',
                'hx-swap': 'outerHTML'
            }),
            'cidade_principal': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'id': 'id_cidade_principal'
            }),
            'cidade_texto': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Digite o nome da cidade'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Bairro onde atende'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Endereço completo (opcional)'
            }),
            
            # Profissional
            'registro_profissional': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Ex: CRP 12345/06 (opcional)'
            }),
            'formacao': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descreva sua formação acadêmica e cursos',
                'rows': 4
            }),
            'experiencia_anos': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '0',
                'min': '0',
                'max': '80'
            }),
            
            # Descrições
            'bio_curta': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descrição breve (máx. 200 caracteres)',
                'rows': 3,
                'maxlength': 200,
                'id': 'id_bio_curta'
            }),
            'bio_completa': CKEditorWidget(config_name='terapeuta_bio'),
            'metodologia': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descreva sua metodologia de trabalho',
                'rows': 4
            }),
            
            # Redes Sociais
            'instagram': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://instagram.com/seu_usuario'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://facebook.com/seu_perfil'
            }),
            'tiktok': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://tiktok.com/@seu_usuario'
            }),
            'youtube': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://youtube.com/@seu_canal'
            }),
            
            # Fotos
            'foto_perfil': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'id': 'id_foto_perfil'
            }),
            'foto_capa': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'id': 'id_foto_capa'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pré-popular valores de JSONField
        if self.instance and self.instance.pk:
            self.fields['tipos_sessao'].initial = self.instance.tipos_sessao or []
            self.fields['para_quem'].initial = self.instance.para_quem or []
            
            # Pré-popular CPF/CNPJ se existir
            if hasattr(self.instance, 'cpf_cnpj'):
                self.fields['cpf_cnpj'].initial = self.instance.cpf_cnpj
            
            # Pré-selecionar especialidades
            especialidades_ids = self.instance.especialidades.values_list('id', flat=True)
            self.fields['especialidades'].initial = list(especialidades_ids)

            # Pré-selecionar cidades de atendimento
            cidades_ids = self.instance.cidades_atendimento.values_list('id', flat=True)
            self.fields['cidades_atendimento'].initial = list(cidades_ids)
        
        # Filtrar cidades pelo estado selecionado
        if self.data.get('estado'):
            try:
                estado_id = int(self.data.get('estado'))
                self.fields['cidade_principal'].queryset = Cidade.objects.filter(
                    estado_id=estado_id,
                    ativo=True
                ).order_by('nome')
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk and self.instance.estado:
            self.fields['cidade_principal'].queryset = Cidade.objects.filter(
                estado=self.instance.estado,
                ativo=True
            ).order_by('nome')

    def clean_cpf_cnpj(self):
        """
        Valida CPF ou CNPJ
        """
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj', '')
        
        if not cpf_cnpj:
            return ''
        
        # Remover formatação
        numeros = re.sub(r'[^0-9]', '', cpf_cnpj)
        
        if len(numeros) == 11:
            # Validar CPF
            if not self._validar_cpf(numeros):
                raise ValidationError('CPF inválido.')
            return self._formatar_cpf(numeros)
        elif len(numeros) == 14:
            # Validar CNPJ
            if not self._validar_cnpj(numeros):
                raise ValidationError('CNPJ inválido.')
            return self._formatar_cnpj(numeros)
        else:
            raise ValidationError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.')
    
    def _validar_cpf(self, cpf):
        """
        Valida dígitos verificadores do CPF
        """
        if cpf == cpf[0] * 11:  # CPF com todos dígitos iguais
            return False
        
        # Validar primeiro dígito
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        
        if int(cpf[9]) != digito1:
            return False
        
        # Validar segundo dígito
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        
        return int(cpf[10]) == digito2
    
    def _validar_cnpj(self, cnpj):
        """
        Valida dígitos verificadores do CNPJ
        """
        if cnpj == cnpj[0] * 14:  # CNPJ com todos dígitos iguais
            return False
        
        # Validar primeiro dígito
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(12))
        digito1 = (soma % 11)
        digito1 = 0 if digito1 < 2 else 11 - digito1
        
        if int(cnpj[12]) != digito1:
            return False
        
        # Validar segundo dígito
        pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(13))
        digito2 = (soma % 11)
        digito2 = 0 if digito2 < 2 else 11 - digito2
        
        return int(cnpj[13]) == digito2
    
    def _formatar_cpf(self, cpf):
        """
        Formata CPF: 000.000.000-00
        """
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    
    def _formatar_cnpj(self, cnpj):
        """
        Formata CNPJ: 00.000.000/0000-00
        """
        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'
    
    def clean_bio_curta(self):
        """
        Valida tamanho da bio curta
        """
        bio_curta = self.cleaned_data.get('bio_curta', '')
        
        if len(bio_curta) > 200:
            raise ValidationError('A bio curta deve ter no máximo 200 caracteres.')
        
        return bio_curta
    
    def save(self, commit=True):
        """
        Sobrescrever save para converter campos MultipleChoice em JSON
        e salvar relacionamentos ManyToMany
        """
        terapeuta = super().save(commit=False)
        
        # Converter tipos_sessao e para_quem para listas (JSON)
        terapeuta.tipos_sessao = list(self.cleaned_data.get('tipos_sessao', []))
        terapeuta.para_quem = list(self.cleaned_data.get('para_quem', []))
        
        # Salvar CPF/CNPJ (se o campo existir no model)
        if hasattr(terapeuta, 'cpf_cnpj'):
            terapeuta.cpf_cnpj = self.cleaned_data.get('cpf_cnpj', '')
        
        if commit:
            terapeuta.save()
            
            # ===== SALVAR CAMPOS MANYTOMANY =====
            
            # Salvar especialidades
            if 'especialidades' in self.cleaned_data:
                terapeuta.especialidades.set(self.cleaned_data['especialidades'])
            
            # Salvar cidades de atendimento
            if 'cidades_atendimento' in self.cleaned_data:
                terapeuta.cidades_atendimento.set(self.cleaned_data['cidades_atendimento'])
        
        return terapeuta