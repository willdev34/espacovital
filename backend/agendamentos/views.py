"""
Título: Views do Sistema de Agendamento de Salas
Descrição: Views para gerenciar agendamentos, AJAX e dashboard
"""

from django.http import JsonResponse
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from espacos.models import Espaco
from .models import Agendamento, Sala


# ==========================================
# VIEWS AJAX
# ==========================================
class GetComodidadesEspacoView(View):
    """
    View AJAX para retornar comodidades de um espaço específico.
    Usada no admin para popular o campo de comodidades da sala.
    """
    
    def get(self, request):
        espaco_id = request.GET.get('espaco_id')
        
        if not espaco_id:
            return JsonResponse({'comodidades': []})
        
        try:
            espaco = Espaco.objects.get(pk=espaco_id)
            comodidades = espaco.comodidades.all().values('id', 'nome')
            return JsonResponse({
                'comodidades': list(comodidades)
            })
        except Espaco.DoesNotExist:
            return JsonResponse({'comodidades': []})
        
# ==========================================
# CRIAR AGENDAMENTO
# ==========================================
class AgendamentoCriarView(LoginRequiredMixin, CreateView):
    """
    Descrição: Formulário para o terapeuta criar um novo agendamento de sala
    """
    model = Agendamento
    template_name = 'agendamentos/agendamento_form.html'
    fields = ['sala', 'data', 'hora_inicio', 'hora_fim', 'observacoes']
    success_url = reverse_lazy('terapeutas:dashboard_agendamentos')

    def get_form(self, form_class=None):
        """
        Lista salas ativas disponíveis para agendamento.

        TODO [FASE VÍNCULO]: Substituir o filtro abaixo para retornar
        apenas salas de espaços onde o terapeuta está APROVADO.
        Depende da implementação do model VinculoTerapeutaEspaco.

        Exemplo futuro:
            vinculos_aprovados = VinculoTerapeutaEspaco.objects.filter(
                terapeuta=self.request.user.terapeuta,
                status='APROVADO'
            ).values_list('espaco_id', flat=True)

            form.fields['sala'].queryset = Sala.objects.filter(
                is_active=True,
                espaco_id__in=vinculos_aprovados
            ).select_related('espaco').order_by('espaco__nome', 'nome')
        """
        form = super().get_form(form_class)

        # Temporário: lista todas as salas ativas
        # Será substituído quando o sistema de vínculos for implementado
        form.fields['sala'].queryset = Sala.objects.filter(
            is_active=True
        ).select_related('espaco').order_by('espaco__nome', 'nome')

        return form

    def form_valid(self, form):
        """
        Associa o terapeuta e o espaço ao agendamento antes de salvar
        """
        agendamento = form.save(commit=False)

        # Vincula o terapeuta logado
        agendamento.terapeuta = self.request.user.terapeuta

        # Vincula o espaço a partir da sala escolhida
        agendamento.espaco = agendamento.sala.espaco

        # Define valor cobrado a partir da sala
        agendamento.valor_cobrado = agendamento.sala.valor_sessao

        agendamento.save()

        messages.success(
            self.request,
            '✅ Agendamento criado com sucesso!'
        )
        return redirect(self.success_url)

    def form_invalid(self, form):
        """
        Retorna mensagem de erro se o formulário for inválido
        """
        messages.error(
            self.request,
            '❌ Erro ao criar agendamento. Verifique os dados e tente novamente.'
        )
        return super().form_invalid(form)


# ==========================================
# DETALHES DO AGENDAMENTO
# ==========================================
class AgendamentoDetalheView(LoginRequiredMixin, DetailView):
    """
    Descrição: Exibe todos os dados de um agendamento específico
    """
    model = Agendamento
    template_name = 'agendamentos/agendamento_detail.html'
    context_object_name = 'agendamento'

    def get_queryset(self):
        """
        Garante que o terapeuta só veja seus próprios agendamentos
        """
        return Agendamento.objects.filter(
            terapeuta=self.request.user.terapeuta
        ).select_related('sala', 'sala__espaco', 'espaco')


# ==========================================
# EDITAR AGENDAMENTO
# ==========================================
class AgendamentoEditarView(LoginRequiredMixin, UpdateView):
    """
    Descrição: Formulário para editar um agendamento existente
               Só permite editar agendamentos PENDENTE ou CONFIRMADO
    """
    model = Agendamento
    template_name = 'agendamentos/agendamento_form.html'
    fields = ['data', 'hora_inicio', 'hora_fim', 'observacoes', 'valor_cobrado']
    success_url = reverse_lazy('terapeutas:dashboard_agendamentos')

    def get_queryset(self):
        """
        Só permite editar agendamentos do próprio terapeuta
        e que ainda estejam pendentes ou confirmados
        """
        return Agendamento.objects.filter(
            terapeuta=self.request.user.terapeuta,
            status__in=['PENDENTE', 'CONFIRMADO']
        )

    def form_valid(self, form):
        """
        Salva e redireciona com mensagem de sucesso
        """
        messages.success(
            self.request,
            '✅ Agendamento atualizado com sucesso!'
        )
        return super().form_valid(form)


# ==========================================
# CANCELAR AGENDAMENTO
# ==========================================
class AgendamentoCancelarView(LoginRequiredMixin, View):
    """
    Descrição: Muda o status do agendamento para CANCELADO
               Só cancela agendamentos PENDENTE ou CONFIRMADO
    """

    def post(self, request, pk):
        """
        Processa o cancelamento via POST
        """
        # Busca o agendamento garantindo que é do terapeuta logado
        agendamento = get_object_or_404(
            Agendamento,
            pk=pk,
            terapeuta=request.user.terapeuta,
            status__in=['PENDENTE', 'CONFIRMADO']
        )

        # Muda o status para cancelado
        agendamento.status = 'CANCELADO'
        agendamento.save()

        messages.success(
            request,
            '✅ Agendamento cancelado com sucesso!'
        )
        return redirect('terapeutas:dashboard_agendamentos')