# ===============================================================
# Título: Forms do App Core - Espaço Vital
# Descrição: Formulários customizados incluindo signup expandido
# Autor: Will
# Data: Dezembro 2025
# ===============================================================

from django import forms
from django.db import models
from django.core.validators import RegexValidator
from allauth.account.forms import SignupForm
from .models import Voucher


class TipoPerfilChoices(models.TextChoices):
    """
    Choices para tipo de perfil no cadastro
    """
    TERAPEUTA = 'terapeuta', 'Terapeuta'
    ESPACO = 'espaco', 'Proprietário de Espaço'
    AMBOS = 'ambos', 'Ambos (Terapeuta + Espaço)'


class CustomSignupForm(SignupForm):
    """
    Título: Formulário de Cadastro Expandido
    Descrição: Formulário customizado para cadastro com seleção de tipo de perfil
    Autor: Will
    Data: Dezembro 2025
    """
    
    # Validador de telefone brasileiro
    phone_validator = RegexValidator(
        regex=r'^\(\d{2}\)\s?\d{4,5}-\d{4}$',
        message='Telefone deve estar no formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX'
    )
    
    # Campo: Nome Completo
    first_name = forms.CharField(
        label='Nome',
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Seu nome',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
        })
    )
    
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Seu sobrenome',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
        })
    )
    
    # Campo: Telefone
    phone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=True,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'placeholder': '(XX) XXXXX-XXXX',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
            'data-mask': 'phone'  # Para aplicar máscara via JS
        }),
        help_text='Formato: (XX) XXXXX-XXXX'
    )
    
    # Campo: Tipo de Perfil
    tipo_perfil = forms.ChoiceField(
        label='Quero me cadastrar como',
        choices=TipoPerfilChoices.choices,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
        })
    )
    
    # Campo: Aceite de Termos
    aceite_termos = forms.BooleanField(
        label='Li e aceito os Termos de Uso e Política de Privacidade',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
        }),
        error_messages={
            'required': 'Você precisa aceitar os termos para continuar.'
        }
    )
    
    # Campo: Código de Voucher (opcional)
    voucher_code = forms.CharField(
        label='Código de Voucher (Opcional)',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Possui um cupom? Digite aqui',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all uppercase',
            'style': 'text-transform: uppercase;'
        }),
        help_text='Se você tem um código de desconto, digite aqui'
    )
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa o formulário e aplica tipo de perfil via GET
        """
        super().__init__(*args, **kwargs)
        
        # Customizar campos padrão do allauth
        self.fields['email'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
            'placeholder': 'seu@email.com'
        })
        
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
            'placeholder': 'Crie uma senha forte'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
            'placeholder': 'Confirme sua senha'
        })
        
        # Pré-selecionar tipo de perfil se vier do GET
        request = kwargs.get('request')
        if request:
            tipo_get = request.GET.get('tipo')
            if tipo_get in ['terapeuta', 'espaco']:
                self.fields['tipo_perfil'].initial = tipo_get
    
    def clean_phone(self):
        """
        Valida e formata o telefone
        """
        phone = self.cleaned_data.get('phone')
        
        # Remove caracteres especiais
        phone_clean = ''.join(filter(str.isdigit, phone))
        
        # Valida quantidade de dígitos
        if len(phone_clean) not in [10, 11]:
            raise forms.ValidationError('Telefone deve ter 10 ou 11 dígitos.')
        
        # Formata o telefone
        if len(phone_clean) == 11:
            phone_formatted = f'({phone_clean[:2]}) {phone_clean[2:7]}-{phone_clean[7:]}'
        else:
            phone_formatted = f'({phone_clean[:2]}) {phone_clean[2:6]}-{phone_clean[6:]}'
        
        return phone_formatted
    
    def clean_voucher_code(self):
        """
        Valida o código de voucher se fornecido
        """
        voucher_code = self.cleaned_data.get('voucher_code', '').strip().upper()
        
        if not voucher_code:
            return None
        
        try:
            voucher = Voucher.objects.get(codigo=voucher_code, is_active=True)
            
            # Verifica se o voucher está válido
            if not voucher.esta_valido:
                raise forms.ValidationError(
                    'Este voucher expirou ou já atingiu o limite de usos.'
                )
            
            return voucher
            
        except Voucher.DoesNotExist:
            raise forms.ValidationError(
                'Código de voucher inválido. Verifique e tente novamente.'
            )
    
    def save(self, request):
        """
        Salva o usuário e armazena dados extras na sessão
        """
        user = super().save(request)
        
        # Salvar nome completo
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        
        # Armazenar dados extras na sessão para usar após confirmação de email
        request.session['signup_data'] = {
            'phone': self.cleaned_data['phone'],
            'tipo_perfil': self.cleaned_data['tipo_perfil'],
            'voucher': self.cleaned_data.get('voucher_code').id if self.cleaned_data.get('voucher_code') else None
        }
        
        return user


class VoucherValidationForm(forms.Form):
    """
    Formulário para validar voucher durante onboarding
    """
    voucher_code = forms.CharField(
        label='Código do Voucher',
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite o código do voucher',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all uppercase text-center text-2xl font-bold tracking-widest',
            'style': 'text-transform: uppercase; letter-spacing: 0.2em;',
            'autocomplete': 'off'
        })
    )
    
    def clean_voucher_code(self):
        """
        Valida o código de voucher
        """
        voucher_code = self.cleaned_data.get('voucher_code', '').strip().upper()
        
        try:
            voucher = Voucher.objects.get(codigo=voucher_code, is_active=True)
            
            # Verifica se o voucher está válido
            if not voucher.esta_valido:
                raise forms.ValidationError(
                    '😔 Este voucher expirou ou já atingiu o limite de usos.'
                )
            
            return voucher
            
        except Voucher.DoesNotExist:
            raise forms.ValidationError(
                '❌ Código inválido. Verifique e tente novamente.'
            )