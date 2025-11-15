# ===============================================================
# Título: Views de Autenticação Customizadas - Espaço Vital
# Descrição: Views personalizadas para login/logout com controle
#            de redirecionamento e mensagens
# Autor: Will
# Data: 15/11/2025
# ===============================================================

from django.shortcuts import redirect
from django.contrib import messages
from allauth.account.views import LoginView, LogoutView


class CustomLoginView(LoginView):
    """
    View customizada de login
    Descrição:
    - Redireciona usuários já autenticados para dashboard/home
    - Evita acesso à página de login quando já está logado
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Intercepta requisição antes de processar
        Se usuário já logado, redireciona para destino apropriado
        """
        # ===== VERIFICAR SE JÁ ESTÁ LOGADO =====
        if request.user.is_authenticated:
            # Usuário já logado - redireciona para dashboard ou home
            if hasattr(request.user, 'terapeuta'):
                # É terapeuta - vai para dashboard
                return redirect('terapeutas:dashboard')
            else:
                # Usuário comum - vai para home
                return redirect('core:home')
        
        # ===== USUÁRIO NÃO LOGADO - CONTINUA NORMAL =====
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona contexto extra para template
        Limpa mensagens de logout antiga se necessário
        """
        context = super().get_context_data(**kwargs)
        
        # ===== GERENCIAR MENSAGENS =====
        # Verifica se tem mensagem de logout na sessão
        # e garante que só aparece se foi logout recente
        storage = messages.get_messages(self.request)
        storage.used = False  # Permite re-leitura das mensagens
        
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