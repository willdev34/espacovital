# ===============================================================
# Título: Adapter customizado para Allauth - Espaço Vital
# Descrição: Controla redirecionamento após login baseado no usuário
#            e gerencia dados extras durante o signup
# ===============================================================

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adapter customizado para django-allauth
    """

    def save_user(self, request, user, form, commit=True):
        """
        Salva dados adicionais do usuário durante o signup.
        Chama o super() para garantir que username e email sejam salvos.
        """
        # Chama o super para salvar username, email, password corretamente
        user = super().save_user(request, user, form, commit=False)

        # Salvar first_name e last_name se existirem
        if hasattr(form, 'cleaned_data'):
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')

        if commit:
            user.save()

            # Armazena dados extras na sessão para usar no onboarding
            signup_data = {}

            if hasattr(form, 'cleaned_data'):
                # Telefone
                if 'phone' in form.cleaned_data:
                    signup_data['phone'] = form.cleaned_data.get('phone', '')

                # Tipo de perfil
                if 'tipo_perfil' in form.cleaned_data:
                    signup_data['tipo_perfil'] = form.cleaned_data.get('tipo_perfil', 'terapeuta')

                # Voucher
                voucher = form.cleaned_data.get('voucher_code')
                if voucher and hasattr(voucher, 'id'):
                    signup_data['voucher_id'] = voucher.id

                # Salva na sessão
                if signup_data:
                    request.session['signup_data'] = signup_data

        return user

    def get_email_confirmation_redirect_url(self, request):
        """
        Redireciona para tela de boas-vindas do onboarding após confirmar email
        """
        return reverse('core:onboarding_welcome')