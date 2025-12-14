"""
Título: Formulários de Onboarding
Descrição: Formulários simplificados para criação de perfis durante o onboarding
Autor: Will
Data: 2024-12-13
"""

from django import forms
from django.core.validators import RegexValidator
from terapeutas.models import Terapeuta
from espacos.models import Espaco
from core.models import Pais, Estado, Cidade, Especialidade


# ===== VALIDADORES =====

telefone_validator = RegexValidator(
    regex=r'^\d{10,11}$',
    message='Telefone deve ter 10 ou 11 dígitos (com DDD)'
)


# ===== FORMULÁRIO BASE (campos compartilhados) =====

class DadosCompartilhadosForm(forms.Form):
    """
    Campos que são compartilhados entre Terapeuta e Espaço
    quando o usuário escolhe criar ambos os perfis
    """
    
    whatsapp = forms.CharField(
        label='WhatsApp',
        max_length=20,
        validators=[telefone_validator],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': '21987654321',
            'id': 'id_whatsapp_compartilhado'
        }),
        help_text='Telefone com DDD (somente números). Ex: 21987654321'
    )
    
    whatsapp_ativo = forms.BooleanField(
        label='Este número é WhatsApp?',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary',
            'id': 'id_whatsapp_ativo_compartilhado'
        })
    )
    
    # Localização
    pais = forms.ModelChoiceField(
    label='País',
    queryset=Pais.objects.filter(ativo=True),
    initial=1,  # Brasil
    widget=forms.Select(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
        'id': 'id_pais_compartilhado'
    })
    )

    estado = forms.ModelChoiceField(
        label='Estado',
        queryset=Estado.objects.filter(ativo=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'id': 'id_estado_compartilhado',
            'hx-get': '/core/cidades-por-estado/',
            'hx-target': '#id_cidade_principal_compartilhado',
            'hx-swap': 'outerHTML'
        })
    )
    
    cidade_principal = forms.ModelChoiceField(
        label='Cidade Principal',
        queryset=Cidade.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'id': 'id_cidade_principal_compartilhado'
        })
    )
    
    cidade_texto = forms.CharField(
        label='Cidade (outros países)',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Digite a cidade',
            'id': 'id_cidade_texto_compartilhado'
        })
    )


# ===== FORMULÁRIO DE TERAPEUTA =====

class TerapeutaOnboardingForm(forms.ModelForm):
    """
    Formulário simplificado para criar perfil de Terapeuta no onboarding
    """
    
    # Campos customizados para JSONField
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
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        help_text='Selecione pelo menos um tipo de sessão'
    )
    
    para_quem = forms.MultipleChoiceField(
        label='Para Quem é a Terapia?',
        choices=PARA_QUEM_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        help_text='Selecione o público-alvo'
    )
    
    # Campos do model
    class Meta:
        model = Terapeuta
        fields = [
            'nome_completo', 'nome_exibicao', 'email_profissional',
            'whatsapp', 'whatsapp_ativo',
            'pais', 'estado', 'cidade_principal', 'cidade_texto',
            'bio_curta', 'foto_perfil',
            'acessibilidade'
        ]
        widgets = {
            'nome_completo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nome completo para exibição pública'
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
                'placeholder': '21987654321',
                'id': 'id_whatsapp_terapeuta'
            }),
            'bio_curta': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descreva brevemente sua atuação (máx. 200 caracteres)',
                'rows': 3,
                'maxlength': 200
            }),
            'foto_perfil': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
        }
    
    # Especialidades (campo adicional)
    especialidades = forms.ModelMultipleChoiceField(
        label='Especialidades/Terapias',
        queryset=Especialidade.objects.filter(is_active=True),
        required=True,
        widget=forms.CheckboxSelectMultiple(),
        help_text='Selecione pelo menos uma especialidade'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pré-popular querysets
        if self.data.get('estado'):
            try:
                estado_id = int(self.data.get('estado'))
                self.fields['cidade_principal'].queryset = Cidade.objects.filter(
                    estado_id=estado_id,
                    ativo=True
                ).order_by('nome')
            except (ValueError, TypeError):
                pass
    
    def save(self, commit=True):
        """
        Sobrescrever save para converter os campos MultipleChoice em JSON
        """
        terapeuta = super().save(commit=False)
        
        # Converter tipos_sessao e para_quem para listas (JSON)
        terapeuta.tipos_sessao = list(self.cleaned_data.get('tipos_sessao', []))
        terapeuta.para_quem = list(self.cleaned_data.get('para_quem', []))
        
        if commit:
            terapeuta.save()
            self.save_m2m()  # Salvar especialidades
        
        return terapeuta


# ===== FORMULÁRIO DE ESPAÇO =====

class EspacoOnboardingForm(forms.ModelForm):
    """
    Formulário simplificado para criar perfil de Espaço no onboarding
    """
    
    class Meta:
        model = Espaco
        fields = [
            'nome', 'descricao_breve', 'descricao_completa', 'email',
            'whatsapp', 'whatsapp_ativo',
            'pais', 'estado', 'cidade', 'cidade_texto',
            'bairro', 'endereco', 'cep',
            'foto_principal', 'aceita_locacao'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nome do espaço terapêutico'
            }),
            'descricao_breve': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descrição breve (máx. 300 caracteres)',
                'rows': 3,
                'maxlength': 300
            }),
            'descricao_completa': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descrição completa do seu espaço',
                'rows': 5
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'contato@seuespaco.com'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '21987654321',
                'id': 'id_whatsapp_espaco'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Bairro'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Rua, número, complemento'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '00000-000'
            }),
            'foto_principal': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pré-popular querysets
        if self.data.get('estado'):
            try:
                estado_id = int(self.data.get('estado'))
                self.fields['cidade'].queryset = Cidade.objects.filter(
                    estado_id=estado_id,
                    is_active=True
                ).order_by('nome')
            except (ValueError, TypeError):
                pass