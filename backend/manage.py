#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ===============================================================
# Título: Manage.py - Espaço Vital
# Descrição: Script principal do Django com encoding UTF-8 forçado
# Autor: Will
# Data: 01/11/2025
# ===============================================================

import os
import sys

# ⚠️ CRÍTICO: FORÇA UTF-8 ANTES DE QUALQUER COISA
# Resolve problemas de encoding no Windows com PostgreSQL
if sys.platform == 'win32':
    # Define encoding UTF-8 para o Python
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Força UTF-8 no console do Windows
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'espacovital.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()