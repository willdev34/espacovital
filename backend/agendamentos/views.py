"""
Título: Views do Sistema de Agendamento de Salas
Descrição: Views para gerenciar agendamentos, AJAX e dashboard
Autor: Will
Data: 29/12/2024
"""

from django.http import JsonResponse
from django.views import View
from espacos.models import Espaco


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