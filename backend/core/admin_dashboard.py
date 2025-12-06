# ===============================================================
# Título: Dashboard Administrativo Customizado - Espaço Vital
# Descrição: View customizada para estatísticas e gestão do painel admin
# Autor: Will
# Data: 06/12/2025
# ===============================================================

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

@staff_member_required
def admin_dashboard(request):
    """
    Dashboard administrativo com estatísticas gerais do sistema
    """
    # ===============================================================
    # ESTATÍSTICAS DE USUÁRIOS
    # ===============================================================
    
    # Total de usuários por tipo
    total_usuarios = User.objects.count()
    usuarios_ativos = User.objects.filter(is_active=True).count()
    superusuarios = User.objects.filter(is_superuser=True).count()
    
    # Grupos
    administradores = User.objects.filter(groups__name='Administradores').count()
    terapeutas_group = User.objects.filter(groups__name='Terapeutas').count()
    
    # ===============================================================
    # ESTATÍSTICAS DE TERAPEUTAS
    # ===============================================================
    
    from terapeutas.models import Terapeuta
    
    total_terapeutas = Terapeuta.objects.count()
    terapeutas_verificados = Terapeuta.objects.filter(verificado=True).count()
    terapeutas_pendentes = Terapeuta.objects.filter(verificado=False).count()
    terapeutas_destaque = Terapeuta.objects.filter(destaque=True).count()
    terapeutas_premium = Terapeuta.objects.filter(plano='premium').count()
    
    # Terapeutas novos (últimos 7 dias)
    data_limite = timezone.now() - timedelta(days=7)
    terapeutas_novos = Terapeuta.objects.filter(created_at__gte=data_limite).count()
    
    # ===============================================================
    # ESTATÍSTICAS DE ESPAÇOS
    # ===============================================================
    
    from espacos.models import Espaco
    
    total_espacos = Espaco.objects.count()
    espacos_verificados = Espaco.objects.filter(is_verificado=True).count()
    espacos_pendentes = Espaco.objects.filter(is_verificado=False).count()
    espacos_destaque = Espaco.objects.filter(is_destaque=True).count()
    espacos_premium = Espaco.objects.filter(is_premium=True).count()
    
    # Espaços novos (últimos 7 dias)
    espacos_novos = Espaco.objects.filter(created_at__gte=data_limite).count()
    
    # ===============================================================
    # ESTATÍSTICAS DE TERAPIAS
    # ===============================================================
    
    from core.models import Especialidade
    
    total_especialidades = Especialidade.objects.count()
    especialidades_ativas = Especialidade.objects.filter(is_active=True).count()
    
    # Especialidades mais populares (com mais terapeutas)
    especialidades_populares = Especialidade.objects.annotate(
        total_terapeutas=Count('terapeutaespecialidade')
    ).order_by('-total_terapeutas')[:5]
    
    # ===============================================================
    # ESTATÍSTICAS DE AVALIAÇÕES
    # ===============================================================
    
    from terapeutas.models import Avaliacao
    from espacos.models import AvaliacaoEspaco
    
    total_avaliacoes_terapeutas = Avaliacao.objects.count()
    total_avaliacoes_espacos = AvaliacaoEspaco.objects.count()
    
    # Média geral de avaliações
    media_avaliacoes_terapeutas = Avaliacao.objects.aggregate(
        media=Avg('nota')
    )['media'] or 0
    
    media_avaliacoes_espacos = AvaliacaoEspaco.objects.aggregate(
        media=Avg('nota')
    )['media'] or 0
    
    # ===============================================================
    # ESTATÍSTICAS DE CONTATOS E MENSAGENS
    # ===============================================================
    
    from terapeutas.models import Contato
    from core.models import Contact
    
    total_contatos_terapeutas = Contato.objects.count()
    contatos_pendentes = Contato.objects.filter(
        status='enviado'
    ).count()
    
    mensagens_gerais = Contact.objects.count()
    mensagens_nao_lidas = Contact.objects.filter(
        status='pending'
    ).count()
    
    # ===============================================================
    # AÇÕES PENDENTES (ALERTAS)
    # ===============================================================
    
    alertas = []
    
    # Alertas de verificação pendente
    if espacos_pendentes > 0:
        alertas.append({
            'tipo': 'warning',
            'icone': '🏢',
            'titulo': f'{espacos_pendentes} espaço(s) aguardando verificação',
            'link': '/admin/espacos/espaco/?is_verificado__exact=0',
            'acao': 'Verificar agora'
        })
    
    if espacos_pendentes > 0:
        alertas.append({
            'tipo': 'warning',
            'icone': '🏢',
            'titulo': f'{espacos_pendentes} espaço(s) aguardando verificação',
            'link': '/admin/espacos/espaco/?verificado__exact=0',
            'acao': 'Verificar agora'
        })
    
    if mensagens_nao_lidas > 0:
        alertas.append({
            'tipo': 'info',
            'icone': '📧',
            'titulo': f'{mensagens_nao_lidas} mensagem(ns) não lida(s)',
            'link': '/admin/core/contato/?status__exact=new',
            'acao': 'Ver mensagens'
        })
    
    if contatos_pendentes > 0:
        alertas.append({
            'tipo': 'info',
            'icone': '💬',
            'titulo': f'{contatos_pendentes} contato(s) de terapeuta pendente(s)',
            'link': '/admin/terapeutas/contato/?status__exact=enviado',
            'acao': 'Ver contatos'
        })
    
    # ===============================================================
    # CONTEXTO DO TEMPLATE
    # ===============================================================
    
    context = {
        'title': 'Dashboard Administrativo',
        
        # Usuários
        'total_usuarios': total_usuarios,
        'usuarios_ativos': usuarios_ativos,
        'superusuarios': superusuarios,
        'administradores': administradores,
        'terapeutas_group': terapeutas_group,
        
        # Terapeutas
        'total_terapeutas': total_terapeutas,
        'terapeutas_verificados': terapeutas_verificados,
        'terapeutas_pendentes': terapeutas_pendentes,
        'terapeutas_destaque': terapeutas_destaque,
        'terapeutas_premium': terapeutas_premium,
        'terapeutas_novos': terapeutas_novos,
        
        # Espaços
        'total_espacos': total_espacos,
        'espacos_verificados': espacos_verificados,
        'espacos_pendentes': espacos_pendentes,
        'espacos_destaque': espacos_destaque,
        'espacos_premium': espacos_premium,
        'espacos_novos': espacos_novos,
        
        # Terapias
        'total_especialidades': total_especialidades,
        'especialidades_ativas': especialidades_ativas,
        'especialidades_populares': especialidades_populares,
        
        # Avaliações
        'total_avaliacoes_terapeutas': total_avaliacoes_terapeutas,
        'total_avaliacoes_espacos': total_avaliacoes_espacos,
        'media_avaliacoes_terapeutas': round(media_avaliacoes_terapeutas, 2),
        'media_avaliacoes_espacos': round(media_avaliacoes_espacos, 2),
        
        # Contatos
        'total_contatos_terapeutas': total_contatos_terapeutas,
        'contatos_pendentes': contatos_pendentes,
        'mensagens_gerais': mensagens_gerais,
        'mensagens_nao_lidas': mensagens_nao_lidas,
        
        # Alertas
        'alertas': alertas,
    }
    
    return render(request, 'admin/dashboard.html', context)