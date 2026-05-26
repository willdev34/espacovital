# ===============================================================
# Título: Template Tags Personalizadas - App Espaços
# Descrição: Filtros e tags customizados para templates de espaços
# ===============================================================

from django import template

register = template.Library()


@register.filter
def getattr_filter(obj, attr):
    """
    Filtro para acessar atributos dinamicamente em templates
    
    Uso:
        {{ objeto|getattr_filter:"nome_atributo" }}
        {{ form|getattr_filter:"field_name" }}
    
    Args:
        obj: Objeto do qual se quer acessar o atributo
        attr: Nome do atributo (string)
    
    Returns:
        Valor do atributo ou string vazia se não existir
    """
    # ===== TENTAR ACESSAR ATRIBUTO =====
    try:
        return getattr(obj, attr, '')
    except (AttributeError, TypeError):
        return ''


@register.filter(name='getattr')
def getattr_alias(obj, attr):
    """
    Alias do filtro getattr_filter para compatibilidade
    
    Uso:
        {{ objeto|getattr:"nome_atributo" }}
    """
    return getattr_filter(obj, attr)