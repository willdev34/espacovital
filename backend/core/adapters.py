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
        - Tem perfil de terapeuta E espaço → Página de seleção de perfil
        - Tem apenas terapeuta → Dashboard de Terapeutas
        - Tem apenas espaço → Dashboard de Espaços
        - Não tem perfil → Home (usuário comum sem acesso)
        
        Atualizado: 16/11/2025 - Suporte a múltiplos perfis
        """
        user = request.user
        
        # ===== VERIFICAR PERFIS DISPONÍVEIS =====
        tem_terapeuta = hasattr(user, 'terapeuta')
        tem_espaco = False
        
        try:
            from espacos.models import Espaco
            # Verificar se usuário é responsável por algum espaço
            tem_espaco = Espaco.objects.filter(responsavel=user, is_active=True).exists()
        except Exception:
            pass  # Campo 'responsavel' ainda não existe no modelo
        
        # ===== DECISÃO DE REDIRECIONAMENTO =====
        
        # Caso 1: Tem AMBOS os perfis → Página de seleção
        if tem_terapeuta and tem_espaco:
            return reverse('core:selecionar_perfil')
        
        # Caso 2: Apenas terapeuta → Dashboard do terapeuta
        if tem_terapeuta:
            return reverse('terapeutas:dashboard')
        
        # Caso 3: Apenas espaço → Dashboard do espaço
        if tem_espaco:
            return reverse('espacos:dashboard')
        
        # Caso 4: Nenhum perfil → Home
        return reverse('core:home')
    
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