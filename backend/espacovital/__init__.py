# ===============================================================
# Título: __init__ - Espaço Vital
# Descrição: Inicialização do projeto com encoding UTF-8
# ===============================================================

import sys
import os

# Força UTF-8 globalmente
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'