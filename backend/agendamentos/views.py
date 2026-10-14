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
from terapeutas.views import TerapeutaRequiredMixin
from .forms import AgendamentoForm, AgendamentoEditarForm
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
class AgendamentoCriarView(TerapeutaRequiredMixin, CreateView):
    """
    Descrição: Formulário para o terapeuta criar um novo agendamento de sala.
               Valida pelo AgendamentoForm: data, antecedência mínima,
               horário da sala, conflito e vínculo com o espaço.
               O terapeuta vem do usuário logado, nunca do POST.
    """
    model = Agendamento
    form_class = AgendamentoForm
    template_name = 'agendamentos/agendamento_form.html'
    success_url = reverse_lazy('terapeutas:dashboard_agendamentos')

    def get_form_kwargs(self):
        """
        Passa o terapeuta logado para o formulário
        """
        kwargs = super().get_form_kwargs()
        kwargs['terapeuta'] = self.request.user.terapeuta
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Envia ao template os espaços vinculados e as salas ativas deles.
        O JS monta o select de sala conforme o espaço escolhido; a
        validação de verdade continua no AgendamentoForm (servidor).
        """
        context = super().get_context_data(**kwargs)

        espacos = context['form'].fields['espaco'].queryset
        salas = Sala.objects.filter(
            espaco__in=espacos,
            is_active=True
        ).select_related('espaco').order_by('espaco__nome', 'nome')

        context['tem_espacos_vinculados'] = espacos.exists()
        context['salas'] = salas
        context['salas_json'] = [
            {
                'id': sala.pk,
                'nome': sala.nome,
                'espaco_id': sala.espaco_id,
                'valor': str(sala.valor_sessao),
                'duracao': sala.duracao_sessao,
            }
            for sala in salas
        ]
        return context

    def form_valid(self, form):
        """
        Salva pelo formulário, que define terapeuta, espaço, hora_fim,
        valor, status e pago. Campos forjados no POST são ignorados.
        """
        self.object = form.save()

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
class AgendamentoDetalheView(TerapeutaRequiredMixin, DetailView):
    """
    Descrição: Exibe todos os dados de um agendamento específico.
               Usuário sem perfil de terapeuta vai para a home.
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
class AgendamentoEditarView(TerapeutaRequiredMixin, UpdateView):
    """
    Descrição: Formulário para editar um agendamento existente.
               Só edita agendamento PENDENTE do próprio terapeuta, e só
               data, hora de início e observações (AgendamentoEditarForm).
               Os demais status vão para o detalhe com mensagem de erro.
    """
    model = Agendamento
    form_class = AgendamentoEditarForm
    template_name = 'agendamentos/agendamento_form.html'
    success_url = reverse_lazy('terapeutas:dashboard_agendamentos')

    def get_queryset(self):
        """
        Só agendamentos do próprio terapeuta: de outro dá 404.
        O status é tratado em _bloquear_se_nao_pendente.
        """
        return Agendamento.objects.filter(
            terapeuta=self.request.user.terapeuta
        ).select_related('sala', 'sala__espaco')

    def _bloquear_se_nao_pendente(self):
        """
        Devolve um redirect para o detalhe quando o agendamento não
        está PENDENTE; devolve None quando a edição pode seguir.
        """
        if self.get_object().status != 'PENDENTE':
            messages.error(
                self.request,
                '❌ Só é possível editar agendamentos pendentes.'
            )
            return redirect(
                'agendamentos:agendamento_detail', pk=self.kwargs['pk']
            )
        return None

    def get(self, request, *args, **kwargs):
        """
        Bloqueia o GET fora de PENDENTE antes de mostrar o formulário
        """
        return (
            self._bloquear_se_nao_pendente()
            or super().get(request, *args, **kwargs)
        )

    def post(self, request, *args, **kwargs):
        """
        Bloqueia o POST fora de PENDENTE antes de validar e gravar
        """
        return (
            self._bloquear_se_nao_pendente()
            or super().post(request, *args, **kwargs)
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
class AgendamentoCancelarView(TerapeutaRequiredMixin, View):
    """
    Descrição: Cancela o agendamento pelo Agendamento.cancelar(), que
               aplica a regra da multa (só CONFIRMADO) de forma atômica
               e sem duplicar multa. Só o terapeuta dono cancela (de
               outro: 404). Exige o valor da multa que o usuário viu no
               aviso (multa_prevista); se estiver desatualizado, ausente
               ou inválido, não cancela.
    """

    def post(self, request, pk):
        """
        Processa o cancelamento via POST
        """
        # Busca o agendamento garantindo que é do terapeuta logado
        agendamento = get_object_or_404(
            Agendamento.objects.select_related('sala'),
            pk=pk,
            terapeuta=request.user.terapeuta
        )

        # Aviso desatualizado: o valor da multa mudou desde que a tela foi
        # aberta. Não cancela; o detalhe mostra o aviso recalculado.
        # CANCELADO e CONCLUIDO são tratados pelo próprio cancelar().
        if (
            agendamento.status in ('PENDENTE', 'CONFIRMADO')
            and not agendamento.multa_prevista_confere(
                request.POST.get('multa_prevista')
            )
        ):
            messages.warning(request, agendamento.texto_aviso_desatualizado())
            return redirect('agendamentos:agendamento_detail', pk=agendamento.pk)

        # Motivo opcional, limitado a 200 caracteres
        motivo = (
            request.POST.get('motivo', '').strip()[:200]
            or 'Cancelado pelo terapeuta'
        )

        sucesso, mensagem, valor_multa = agendamento.cancelar(
            usuario=request.user,
            motivo=motivo
        )

        if not sucesso:
            messages.error(request, f'❌ {mensagem}')
            return redirect('agendamentos:agendamento_detail', pk=agendamento.pk)

        if valor_multa > 0:
            messages.warning(request, f'⚠️ {mensagem}')
        else:
            messages.success(request, f'✅ {mensagem}')

        return redirect('terapeutas:dashboard_agendamentos')