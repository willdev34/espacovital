# ===============================================================
# Título: Adapter customizado para Allauth - Espaço Vital
# Descrição: Controla redirecionamento após login baseado no usuário
#            e gerencia mensagens de forma inteligente
# Autor: Will
# Data: 13/11/2025
# Atualizado: 15/11/2025 - Correção de mensagens duplicadas
# ===============================================================

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from django.contrib import messages

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adapter: Redirecionar usuário após login
    Descrição: 
    - Terapeutas → Dashboard de Terapeutas
    - Gestores de Espaços → Dashboard de Espaços (quando implementado)
    - Usuários comuns sem perfil → Home (sem acesso a dashboards)
    - Gerencia mensagens para evitar duplicação
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
    
    def add_message(self, request, level, message_template, message_context=None, extra_tags=''):
        """
        Sobrescreve método para limpar mensagens antigas antes de adicionar novas
        Evita acúmulo de mensagens de logout + login
        """
        # ===== LIMPAR MENSAGENS ANTERIORES DE LOGOUT =====
        # Quando faz login, não queremos ver mensagem de logout anterior
        if 'logged' in message_template.lower() or 'signed' in message_template.lower():
            # Limpa todas as mensagens pendentes para evitar duplicação
            storage = messages.get_messages(request)
            # Consume as mensagens existentes para limpá-las
            list(storage)
        
        # ===== CHAMAR MÉTODO ORIGINAL =====
        super().add_message(request, level, message_template, message_context, extra_tags)