# ===============================================================
# Título: Views de Autenticação Customizadas - Espaço Vital
# Descrição: Views personalizadas para login/logout com controle
#            de redirecionamento e mensagens
# Autor: Will
# Data: 15/11/2025
# ===============================================================

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from allauth.account.views import LoginView, LogoutView


class CustomLoginView(LoginView):
    """
    View customizada de login
    """
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'terapeuta'):
                return redirect('terapeutas:dashboard')
            else:
                return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """
        Sobrescreve para forçar redirecionamento correto após login
        """
        # ===== REALIZAR LOGIN =====
        self.user = form.user
        auth_login(self.request, self.user)
        
        # ===== REDIRECIONAR BASEADO NO TIPO DE USUÁRIO =====
        if hasattr(self.user, 'terapeuta'):
            return redirect('terapeutas:dashboard')
        else:
            return redirect('core:home')
    
    def get_success_url(self):
        if hasattr(self.request.user, 'terapeuta'):
            return '/terapeutas/dashboard/'
        else:
            return '/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        storage = messages.get_messages(self.request)
        storage.used = False
        return context


class CustomLogoutView(LogoutView):
    """
    View customizada de logout
    Descrição:
    - Adiciona mensagem de logout
    - Marca na sessão que foi logout recente
    - Redireciona para página de login após logout
    """
    
    def post(self, request, *args, **kwargs):
        """
        Processa logout e redireciona para login
        """
        # ===== MARCAR QUE FOI LOGOUT RECENTE =====
        # Isso será usado para mostrar mensagem apenas uma vez
        request.session['recent_logout'] = True
        
        # ===== CHAMAR LOGOUT ORIGINAL =====
        response = super().post(request, *args, **kwargs)
        
        return response
    
    def get_redirect_url(self):
        """
        Sobrescreve URL de redirecionamento após logout
        Força redirecionamento para página de login
        """
        # ===== FORÇAR REDIRECIONAMENTO PARA LOGIN =====
        return '/accounts/login/'