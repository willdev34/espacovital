# ===============================================================
# Título: Adapter customizado para Allauth - Espaço Vital
# Descrição: Controla redirecionamento após login baseado no usuário
# e gerencia mensagens de forma inteligente
# ===============================================================

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from django.contrib import messages

from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adapter customizado para django-allauth
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Salva dados adicionais do usuário durante o signup
        """
        # Salvar first_name e last_name
        user.first_name = form.cleaned_data.get('first_name', '')
        user.last_name = form.cleaned_data.get('last_name', '')
        
        if commit:
            user.save()
        
        # Salvar dados extras na sessão para uso posterior
        request.session['signup_data'] = {
            'phone': form.cleaned_data.get('phone', ''),
            'tipo_perfil': form.cleaned_data.get('tipo_perfil', 'terapeuta'),
        }
        
        # Se um voucher foi usado, salvar o ID
        voucher = form.cleaned_data.get('voucher')
        if voucher:
            request.session['signup_data']['voucher_id'] = voucher.id
        
        return user
    
    def get_email_confirmation_redirect_url(self, request):
        """
        Redireciona para tela de boas-vindas do onboarding após confirmar email
        """
        return reverse('core:onboarding_welcome')
def save_user(self, request, user, form, commit=True):
        """
        Salva dados extras do formulário customizado de signup
        Armazena informações na sessão para usar após confirmação de email
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Salvar dados do formulário customizado se existirem
        if hasattr(form, 'cleaned_data'):
            # Nome completo
            if 'first_name' in form.cleaned_data:
                user.first_name = form.cleaned_data.get('first_name', '')
            if 'last_name' in form.cleaned_data:
                user.last_name = form.cleaned_data.get('last_name', '')
        
        if commit:
            user.save()
            
            # Armazenar dados extras na sessão para usar no onboarding
            if hasattr(form, 'cleaned_data'):
                signup_data = {}
                
                # Telefone
                if 'phone' in form.cleaned_data:
                    signup_data['phone'] = form.cleaned_data.get('phone')
                
                # Tipo de perfil
                if 'tipo_perfil' in form.cleaned_data:
                    signup_data['tipo_perfil'] = form.cleaned_data.get('tipo_perfil')
                
                # Voucher (se validado)
                voucher = form.cleaned_data.get('voucher_code')
                if voucher and hasattr(voucher, 'id'):
                    signup_data['voucher_id'] = voucher.id
                
                # Salvar na sessão
                if signup_data:
                    request.session['signup_data'] = signup_data
        
        return user