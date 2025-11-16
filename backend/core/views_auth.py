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
        """
        Verifica se usuário já está autenticado e redireciona adequadamente
        
        Atualizado: 16/11/2025 - Suporte a múltiplos perfis
        """
        if request.user.is_authenticated:
            # Verificar perfis disponíveis
            tem_terapeuta = hasattr(request.user, 'terapeuta')
            tem_espaco = False
            
            if hasattr(request.user, 'espacos_gerenciados'):
                tem_espaco = request.user.espacos_gerenciados.filter(is_active=True).exists()
            
            # Redirecionar baseado nos perfis
            if tem_terapeuta and tem_espaco:
                return redirect('core:selecionar_perfil')
            elif tem_terapeuta:
                return redirect('terapeutas:dashboard')
            elif tem_espaco:
                return redirect('espacos:dashboard')
            else:
                return redirect('core:home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """
        Sobrescreve para forçar redirecionamento correto após login
        Verifica se usuário tem múltiplos perfis (terapeuta E espaço)
        
        Atualizado: 16/11/2025 - Suporte a múltiplos perfis
        """
        # ===== REALIZAR LOGIN =====
        self.user = form.user
        auth_login(self.request, self.user)
        
        # ===== VERIFICAR PERFIS DISPONÍVEIS =====
        tem_terapeuta = hasattr(self.user, 'terapeuta')
        tem_espaco = False
        
        # Verificar se usuário gerencia algum espaço ativo
        if hasattr(self.user, 'espacos_gerenciados'):
            tem_espaco = self.user.espacos_gerenciados.filter(is_active=True).exists()
        
        # ===== REDIRECIONAR BASEADO NO TIPO DE USUÁRIO =====
        
        # Caso 1: Tem AMBOS os perfis → Página de seleção
        if tem_terapeuta and tem_espaco:
            return redirect('core:selecionar_perfil')
        
        # Caso 2: Apenas terapeuta → Dashboard do terapeuta
        if tem_terapeuta:
            return redirect('terapeutas:dashboard')
        
        # Caso 3: Apenas espaço → Dashboard do espaço
        if tem_espaco:
            return redirect('espacos:dashboard')
        
        # Caso 4: Usuário comum → Home
        return redirect('core:home')

    def get_success_url(self):
        """
        Fallback de redirecionamento (caso form_valid não seja chamado)
        
        Atualizado: 16/11/2025 - Suporte a múltiplos perfis
        """
        user = self.request.user
        
        # Verificar perfis disponíveis
        tem_terapeuta = hasattr(user, 'terapeuta')
        tem_espaco = False
        
        if hasattr(user, 'espacos_gerenciados'):
            tem_espaco = user.espacos_gerenciados.filter(is_active=True).exists()
        
        # Decidir redirecionamento
        if tem_terapeuta and tem_espaco:
            return '/selecionar-perfil/'
        elif tem_terapeuta:
            return '/terapeutas/dashboard/'
        elif tem_espaco:
            return '/espacos/dashboard/'
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