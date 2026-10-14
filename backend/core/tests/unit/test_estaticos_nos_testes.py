# ===============================================================
# Título: Teste de Regressão - Estáticos nos Testes
# Descrição: Garante que {% static %} de um arquivo fora do
#            manifesto não levanta ValueError nos testes, ou seja,
#            que a suíte não depende do collectstatic.
# Autor: Will
# Data: 2026-10-14
# ===============================================================

from django.template import Template, Context


# ---------------------------------------------------------------
# Renderiza {% static %} com um arquivo que não existe em lugar
# nenhum. Com o storage de manifesto isso levantaria ValueError;
# com o StaticFilesStorage da fixture autouse só devolve a URL.
# ---------------------------------------------------------------
def test_static_de_arquivo_inexistente_nao_levanta_erro():
    template = Template(
        "{% load static %}{% static 'arquivo/que/nao/existe.svg' %}"
    )

    url = template.render(Context({}))

    assert url == '/static/arquivo/que/nao/existe.svg'
