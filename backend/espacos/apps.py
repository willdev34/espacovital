# ===============================================================
# Título: Apps.py do App Espacos - Espaço Vital
# Descrição: Configuração do app espacos
# ===============================================================

from django.apps import AppConfig


class EspacosConfig(AppConfig):
    """
    Configuração do app Espacos
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'espacos'
    verbose_name = 'Espaços Terapêuticos'
    
    def ready(self):
        """
        Código executado quando o app está pronto
        Importa signals se necessário
        """
        try:
            import espacos.signals
        except ImportError:
            pass