# ===============================================================
# Título: URLs do App Terapeutas - Espaço Vital
# Descrição: Configuração de rotas para busca, perfil e dashboard de terapeutas
# ===============================================================

from django.urls import path
from . import views

# Nome do app para namespace das URLs
app_name = 'terapeutas'

urlpatterns = [
    # ============================================
    # PÁGINAS PRINCIPAIS
    # ============================================
    
    # Busca avançada de terapeutas (página principal)
    # URL: /terapeutas/
    # Baseada no layout da busca avançada compartilhado
    path(
        '', 
        views.TerapeutaListView.as_view(), 
        name='listagem_resultados'
    ),
    
    # Busca avançada com parâmetros específicos
    # URL: /terapeutas/buscar/
    path(
        'buscar/', 
        views.TerapeutaListView.as_view(), 
        name='buscar'
    ),
    
    # Listagem simples sem filtros
    # URL: /terapeutas/lista/
    # Baseada no layout sem filtro compartilhado
    # path(
    #     'lista/', 
    #     views.terapeutas_sem_filtro, 
    #     name='listagem_simples'
    # ),
    
    # Listagem por especialidade (sem filtros)
    # URL: /terapeutas/especialidade/massoterapia/
    path(
        'especialidade/<slug:especialidade_slug>/', 
        views.terapeutas_sem_filtro, 
        name='por_especialidade'
    ),
    
    # ============================================
    # DASHBOARD PRIVADO (requer autenticação)
    # ============================================
    
    # Dashboard principal do terapeuta
    # URL: /terapeutas/dashboard/
    # Área privada com estatísticas e visão geral
    path(
        'dashboard/',
        views.DashboardView.as_view(),
        name='dashboard'
    ),
    
    # Editar perfil do terapeuta
    # URL: /terapeutas/dashboard/perfil/
    # Formulário completo para edição de dados profissionais
    path(
        'dashboard/perfil/',
        views.DashboardEditarPerfilView.as_view(),
        name='dashboard_editar_perfil'
    ),
    
    # Estatísticas detalhadas
    # URL: /terapeutas/dashboard/estatisticas/
    # Métricas de visualizações, contatos e avaliações
    path(
        'dashboard/estatisticas/',
        views.DashboardEstatisticasView.as_view(),
        name='dashboard_estatisticas'
    ),
    
    # Gerenciar espaços vinculados
    # URL: /terapeutas/dashboard/espacos/
    # Listar e vincular-se a espaços terapêuticos
    path(
        'dashboard/espacos/',
        views.DashboardEspacosVinculadosView.as_view(),
        name='dashboard_espacos'
    ),
    
    # Gerenciar assinatura/plano
    # URL: /terapeutas/dashboard/assinatura/
    # Ver plano atual e opções de upgrade (Free/Premium)
    path(
        'dashboard/assinatura/',
        views.DashboardAssinaturaView.as_view(),
        name='dashboard_assinatura'
    ),

    # ============================================
    # SISTEMA DE AGENDAMENTOS (FASE 3)
    # ============================================

    # Listar agendamentos
    # URL: /terapeutas/dashboard/agendamentos/
    # Lista todos os agendamentos do terapeuta com filtros
    path(
        'dashboard/agendamentos/',
        views.DashboardAgendamentosView.as_view(),
        name='dashboard_agendamentos'
    ),

    # Espaços vinculados ao terapeuta
    # URL: /terapeutas/dashboard/espacos/
    path(
        'dashboard/espacos/',
        views.DashboardEspacosVinculadosView.as_view(),
        name='dashboard_espacos_vinculados'
    ),

    # Espaços disponíveis para agendamento
    # URL: /terapeutas/dashboard/espacos/agendamentos/
    path(
        'dashboard/espacos/agendamentos/',
        views.DashboardEspacosVinculadosAgendamentosView.as_view(),
        name='dashboard_espacos_agendamentos'
    ),

    # Solicitar vínculo com um espaço
    # URL: /terapeutas/dashboard/espacos/<id>/solicitar/
    path(
        'dashboard/espacos/<int:espaco_id>/solicitar/',
        views.SolicitarVinculoEspacoView.as_view(),
        name='solicitar_vinculo_espaco'
    ),

    # Cancelar vínculo com um espaço
    # URL: /terapeutas/dashboard/espacos/<int:vinculo_id>/cancelar/
    path(
        'dashboard/espacos/<int:vinculo_id>/cancelar/',
        views.CancelarVinculoEspacoView.as_view(),
        name='cancelar_vinculo_espaco'
    ),

    # Aceitar convite de vínculo de um espaço
    # URL: /terapeutas/dashboard/espacos/convites/<id>/aceitar/
    path(
        'dashboard/espacos/convites/<int:vinculo_id>/aceitar/',
        views.AceitarConviteEspacoView.as_view(),
        name='aceitar_convite_espaco'
    ),

    # Recusar convite de vínculo de um espaço
    # URL: /terapeutas/dashboard/espacos/convites/<id>/recusar/
    path(
        'dashboard/espacos/convites/<int:vinculo_id>/recusar/',
        views.RecusarConviteEspacoView.as_view(),
        name='recusar_convite_espaco'
    ),

    # Criar novo agendamento
    # URL: /terapeutas/dashboard/agendamentos/novo/
    # Formulário para agendar sala em espaço vinculado
    path(
        'dashboard/agendamentos/novo/',
        views.DashboardAgendamentoCriarView.as_view(),
        name='dashboard_agendamento_criar'
    ),

    # Ver detalhes do agendamento
    # URL: /terapeutas/dashboard/agendamentos/<id>/
    # Exibe informações completas e opção de cancelar
    path(
        'dashboard/agendamentos/<int:pk>/',
        views.DashboardAgendamentoDetalheView.as_view(),
        name='dashboard_agendamento_detalhe'
    ),

    # Cancelar agendamento
    # URL: /terapeutas/dashboard/agendamentos/<id>/cancelar/
    # Cancela agendamento e aplica multa se necessário
    path(
        'dashboard/agendamentos/<int:pk>/cancelar/',
        views.DashboardAgendamentoCancelarView.as_view(),
        name='dashboard_agendamento_cancelar'
    ),

    # Espaços vinculados (para agendamentos)
    # URL: /terapeutas/dashboard/espacos-vinculados/
    # Lista espaços onde o terapeuta pode agendar salas
    path(
        'dashboard/espacos-vinculados/',
        views.DashboardEspacosVinculadosAgendamentosView.as_view(),
        name='dashboard_espacos_vinculados_agendamentos'
    ),

    # ============================================
    # PERFIL DO TERAPEUTA (público)
    # ============================================
    
    # Perfil completo do terapeuta
    # URL: /terapeutas/perfil/ana-silva/
    # IMPORTANTE: Deve ficar depois das rotas do dashboard para evitar conflitos
    path(
        'perfil/<slug:slug>/',
        views.TerapeutaDetailView.as_view(),
        name='perfil'
    ),
    
    # Formulário de contato com terapeuta
    # URL: /terapeutas/contatar/ana-silva/
    path(
        'contatar/<slug:terapeuta_slug>/', 
        views.contatar_terapeuta, 
        name='contatar'
    ),
    
    # ============================================
    # APIS AJAX
    # ============================================
    
    # API para buscar cidades por estado
    # URL: /terapeutas/api/cidades-por-estado/
    # Para filtro de localização dinâmico
    path(
        'api/cidades-por-estado/', 
        views.cidades_por_estado_ajax, 
        name='cidades_por_estado_ajax'
    ),
    
    # API para busca de terapeutas (autocomplete)
    # URL: /terapeutas/api/buscar/
    # Para o campo de busca do hero section
    path(
        'api/buscar/', 
        views.busca_terapeutas_ajax, 
        name='busca_ajax'
    ),
    
    # ============================================
    # URLs DE LOCALIZAÇÃO (para SEO)
    # ============================================
    
    # Terapeutas por cidade
    # URL: /terapeutas/rio-de-janeiro-rj/
    # Futura implementação para SEO local
    # path(
    #     '<slug:cidade_slug>-<slug:estado_slug>/',
    #     views.terapeutas_por_cidade,
    #     name='por_cidade'
    # ),
    
    # ============================================
    # URLs PARA CATEGORIAS/FILTROS ESPECÍFICOS
    # ============================================
    
    # Terapeutas em destaque (para home)
    # URL: /terapeutas/destaques/
    # path(
    #     'destaques/',
    #     views.terapeutas_destaque,
    #     name='destaques'
    # ),
    
    # Terapeutas premium/VIP
    # URL: /terapeutas/premium/
    # path(
    #     'premium/',
    #     views.terapeutas_premium,
    #     name='premium'
    # ),
    
    # ============================================
    # URLs DE AVALIAÇÃO (futuras)
    # ============================================
    
    # Avaliar terapeuta (apenas usuários logados)
    # URL: /terapeutas/avaliar/ana-silva/
    # path(
    #     'avaliar/<slug:terapeuta_slug>/',
    #     views.avaliar_terapeuta,
    #     name='avaliar'
    # ),
]

# ============================================
# COMENTÁRIOS SOBRE AS URLs
# ============================================

"""
ESTRUTURA DAS URLs DO APP TERAPEUTAS:

1. PÁGINAS PRINCIPAIS:
   - '' → Busca avançada (página principal)
   - 'buscar/' → Mesma busca avançada (URL alternativa)
   - 'lista/' → Listagem simples sem filtros
   - 'especialidade/<slug>/' → Filtro por especialidade

2. DASHBOARD PRIVADO (NOVO - TAREFA 8):
   - 'dashboard/' → Dashboard principal com estatísticas
   - 'dashboard/perfil/' → Editar perfil completo
   - 'dashboard/estatisticas/' → Métricas detalhadas
   - 'dashboard/espacos/' → Gerenciar espaços vinculados
   - 'dashboard/assinatura/' → Gerenciar plano (Free/Premium)

3. PERFIL PÚBLICO:
   - 'perfil/<slug>/' → Perfil completo
   - 'contatar/<slug>/' → Formulário de contato

4. APIs AJAX:
   - 'api/cidades-por-estado/' → Filtro dinâmico
   - 'api/buscar/' → Autocomplete do hero

5. FUTURAS IMPLEMENTAÇÕES (comentadas):
   - URLs por localização (SEO)
   - Categorias específicas (destaque, premium)
   - Sistema de avaliações

EXEMPLOS DE USO:
- Busca geral: /terapeutas/
- Com filtros: /terapeutas/?cidade=1&especialidades=1,2&acessibilidade=sim
- Por especialidade: /terapeutas/especialidade/massoterapia/
- Dashboard: /terapeutas/dashboard/
- Editar perfil: /terapeutas/dashboard/perfil/
- Estatísticas: /terapeutas/dashboard/estatisticas/
- Perfil público: /terapeutas/perfil/ana-silva/
- Contato: /terapeutas/contatar/ana-silva/
- AJAX cidades: /terapeutas/api/cidades-por-estado/?estado_id=1
- AJAX busca: /terapeutas/api/buscar/?q=ana

SEGURANÇA DO DASHBOARD:
- Todas as views do dashboard utilizam TerapeutaRequiredMixin
- Verifica se usuário está autenticado
- Verifica se usuário tem perfil de terapeuta
- Redireciona para home caso não atenda os requisitos

INTEGRAÇÃO COM URLS PRINCIPAIS:
No arquivo espacovital/urls.py, adicionar:
path('terapeutas/', include('terapeutas.urls')),
"""