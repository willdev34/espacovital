# ===============================================================
# Título: Adapter customizado para Allauth - Espaço Vital
# Descrição: Controla redirecionamento após login baseado no usuário
# Autor: Will
# Data: 13/11/2025
# ===============================================================

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adapter: Redirecionar usuário após login
    Descrição: 
    - Terapeutas → Dashboard de Terapeutas
    - Gestores de Espaços → Dashboard de Espaços (quando implementado)
    - Usuários comuns sem perfil → Home (sem acesso a dashboards)
    """
    
    def get_login_redirect_url(self, request):
        """
        Redireciona baseado no tipo de usuário:
        - Tem perfil de terapeuta → Dashboard de Terapeutas
        - Tem perfil de gestor de espaço → Dashboard de Espaços (futuro)
        - Não tem perfil → Home (usuário comum sem acesso)
        """
        user = request.user
        
        # ===== VERIFICAR SE É TERAPEUTA =====
        if hasattr(user, 'terapeuta'):
            return '/terapeutas/dashboard/'
        
        # ===== VERIFICAR SE É GESTOR DE ESPAÇO =====
        try:
            from espacos.models import Espaco
            # Verificar se usuário é responsável por algum espaço
            if Espaco.objects.filter(responsavel=user, is_active=True).exists():
                # TODO: Quando implementar dashboard de espaços, descomentar:
                # return '/espacos/dashboard/'
                
                # Por enquanto, redireciona para home com mensagem
                return '/terapeutas/dashboard/'  # Temporário
        except Exception:
            pass  # Campo 'responsavel' ainda não existe no modelo
        
        # ===== USUÁRIO COMUM SEM PERFIL =====
        # Redireciona para home
        # Se quiser criar página explicando como se tornar terapeuta:
        # return '/seja-terapeuta/'
        return '/'