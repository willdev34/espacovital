# ===============================================================
# Título: Signals do Core
# Descrição: Signals para sincronizar Assinatura → Terapeuta/Espaço
# Autor: Will
# Data: 19/01/2026
# ===============================================================

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Assinatura


@receiver(post_save, sender=Assinatura)
def atualizar_plano_terapeuta(sender, instance, **kwargs):
    """
    Quando uma Assinatura é salva, atualiza o campo 'plano' do Terapeuta.
    
    Mapeia os planos:
    - basic → basic
    - premium_a → premium_a
    - combo_a_s → premium_a
    - combo_a_s_plus → premium_a
    """
    from terapeutas.models import Terapeuta
    
    # Verificar se o usuário tem perfil de terapeuta
    try:
        terapeuta = Terapeuta.objects.get(user=instance.usuario)
    except Terapeuta.DoesNotExist:
        return
    
    # Mapear plano da assinatura para campo do terapeuta
    plano_map = {
        'basic': 'basic',
        'premium_a': 'premium_a',
        'premium_s': 'premium_s',
        'premium_s_plus': 'premium_s',
        'combo_a_s': 'premium_a',
        'combo_a_s_plus': 'premium_a',
        'gratuito_filiado': 'basic',
    }
    
    novo_plano = plano_map.get(instance.plano.nome, 'basic')
    
    # Atualizar apenas se mudou
    if terapeuta.plano != novo_plano:
        terapeuta.plano = novo_plano
        terapeuta.data_assinatura_plano = instance.data_inicio
        terapeuta.save(update_fields=['plano', 'data_assinatura_plano'])