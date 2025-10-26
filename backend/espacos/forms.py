# ===============================================================
# Título: Forms do App Espacos - Espaço Vital
# Descrição: Formulários para contato e avaliação de espaços terapêuticos
# Autor: Will | Empresa: Espaço Vital
# Data: 14/09/2025
# ===============================================================

from django import forms
from django.core.validators import EmailValidator, RegexValidator
from .models import ContatoEspaco, AvaliacaoEspaco, Espaco, Comodidade


# ===============================================================
# FORM DE CONTATO COM ESPACO
# ===============================================================

class ContatoEspacoForm(forms.ModelForm):
    """
    Formulário para contato com espaços terapêuticos
    Layout profissional com validações robustas
    """
    
    class Meta:
        model = ContatoEspaco
        fields = ['nome', 'email', 'telefone', 'assunto', 'mensagem']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar widgets e classes CSS
        self.fields['nome'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
            'placeholder': 'Seu nome completo',
            'maxlength': '100'
        })
        
        self.fields['email'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
            'placeholder': 'seu@email.com',
            'type': 'email'
        })
        
        self.fields['telefone'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
            'placeholder': '(11) 99999-9999',
            'pattern': r'\(\d{2}\)\s\d{4,5}-\d{4}',
            'title': 'Formato: (11) 99999-9999'
        })
        
        self.fields['assunto'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
            'placeholder': 'Assunto da sua mensagem',
            'maxlength': '200'
        })
        
        self.fields['mensagem'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-none',
            'placeholder': 'Escreva sua mensagem aqui... Conte sobre suas necessidades, horários de preferência, ou qualquer dúvida sobre o espaço.',
            'rows': '6'
        })
        
        # Labels personalizados
        self.fields['nome'].label = 'Nome completo'
        self.fields['email'].label = 'Email para resposta'
        self.fields['telefone'].label = 'Telefone (opcional)'
        self.fields['assunto'].label = 'Assunto'
        self.fields['mensagem'].label = 'Mensagem'
        
        # Help texts informativos
        self.fields['telefone'].help_text = 'Formato: (11) 99999-9999'
        self.fields['mensagem'].help_text = 'Descreva suas necessidades, horários de preferência ou dúvidas sobre o espaço.'
    
    def clean_telefone(self):
        """
        Validação personalizada do telefone
        """
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remove caracteres especiais para validação
            telefone_limpo = ''.join(filter(str.isdigit, telefone))
            if len(telefone_limpo) not in [10, 11]:
                raise forms.ValidationError('Telefone deve ter 10 ou 11 dígitos.')
        return telefone
    
    def clean_mensagem(self):
        """
        Validação da mensagem
        """
        mensagem = self.cleaned_data.get('mensagem')
        if len(mensagem) < 10:
            raise forms.ValidationError('Mensagem deve ter pelo menos 10 caracteres.')
        return mensagem


# ===============================================================
# FORM DE AVALIACAO DE ESPACO
# ===============================================================

class AvaliacaoEspacoForm(forms.ModelForm):
    """
    Formulário para avaliação de espaços terapêuticos
    Sistema de estrelas e comentários
    """
    
    class Meta:
        model = AvaliacaoEspaco
        fields = ['nota', 'comentario']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Widget personalizado para as estrelas
        self.fields['nota'].widget = forms.RadioSelect(
            choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)]
        )
        self.fields['nota'].widget.attrs.update({
            'class': 'rating-stars'
        })
        
        # Widget para comentário
        self.fields['comentario'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-none',
            'placeholder': 'Compartilhe sua experiência com este espaço... Como foi o atendimento? O ambiente estava adequado? Recomendaria para outros?',
            'rows': '5',
            'maxlength': '500'
        })
        
        # Labels
        self.fields['nota'].label = 'Avaliação geral'
        self.fields['comentario'].label = 'Seu comentário'
        
        # Help text
        self.fields['comentario'].help_text = 'Máximo 500 caracteres. Seja construtivo e respeitoso.'
    
    def clean_comentario(self):
        """
        Validação do comentário
        """
        comentario = self.cleaned_data.get('comentario')
        if len(comentario) < 10:
            raise forms.ValidationError('Comentário deve ter pelo menos 10 caracteres.')
        
        # Verificar palavras inadequadas (lista básica)
        palavras_inadequadas = ['idiota', 'péssimo', 'horrível', 'lixo']
        comentario_lower = comentario.lower()
        
        for palavra in palavras_inadequadas:
            if palavra in comentario_lower:
                raise forms.ValidationError(
                    'Por favor, mantenha um tom respeitoso em seu comentário.'
                )
        
        return comentario


# ===============================================================
# FORM DE BUSCA AVANCADA
# ===============================================================

class BuscaEspacoForm(forms.Form):
    """
    Formulário para busca avançada de espaços
    Baseado nos filtros do layout espacoComFiltro.pdf
    """
    
    # Campo de busca textual
    busca = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Nome do espaço, terapia ou localização...'
        }),
        label='Buscar por'
    )
    
    # Filtro: Tipo de espaço
    tipo_espaco = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os tipos')] + list(Espaco._meta.get_field('tipo_espaco').choices),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Tipo de espaço'
    )
    
    # Filtro: Estado
    estado = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Será definido no __init__
        empty_label='Selecione o estado',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
            'onchange': 'carregarCidades(this.value)'
        }),
        label='Estado'
    )
    
    # Filtro: Cidade
    cidade = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Será preenchido via AJAX
        empty_label='Primeiro selecione o estado',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Cidade'
    )
    
    # Filtro: Especialidades (multi-select)
    especialidades = forms.ModelMultipleChoiceField(
        required=False,
        queryset=None,  # Será definido no __init__
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'especialidades-checkbox'
        }),
        label='Terapias disponíveis'
    )
    
    # Filtro: Acessibilidade
    acessibilidade = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Indiferente'),
            ('sim', 'Sim'),
            ('nao', 'Não')
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'acessibilidade-radio'
        }),
        label='Espaço com acessibilidade?'
    )
    
    # Filtro: Aceita locação
    aceita_locacao = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Indiferente'),
            ('sim', 'Sim'),
            ('nao', 'Não')
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'locacao-radio'
        }),
        label='Aceita locação?'
    )
    
    # Filtro: Disponibilidade por período
    disponibilidade = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('manha', 'Manhã'),
            ('tarde', 'Tarde'),
            ('noite', 'Noite'),
            ('finais_de_semana', 'Finais de semana')
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'disponibilidade-checkbox'
        }),
        label='Disponibilidade por período'
    )
    
    # Filtro: Comodidades
    comodidades = forms.ModelMultipleChoiceField(
        required=False,
        queryset=None,  # Será definido no __init__
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'comodidades-checkbox'
        }),
        label='Comodidades desejadas'
    )
    
    # Ordenação
    ordem = forms.ChoiceField(
        required=False,
        choices=[
            ('destaque', 'Destaque'),
            ('nome', 'Nome A-Z'),
            ('avaliacao', 'Melhor avaliados'),
            ('recente', 'Mais recentes')
        ],
        initial='destaque',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Ordenar por'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Carregar querysets dinamicamente
        from .models import Estado, Especialidade, Comodidade
        
        self.fields['estado'].queryset = Estado.objects.all().order_by('nome')
        self.fields['especialidades'].queryset = Especialidade.objects.filter(
            is_active=True
        ).order_by('categoria', 'nome')
        self.fields['comodidades'].queryset = Comodidade.objects.filter(
            is_active=True
        ).order_by('-is_destaque', 'nome')


# ===============================================================
# FORM PARA CADASTRO/EDIÇÃO DE ESPACO (ADMIN/PROPRIETÁRIO)
# ===============================================================

class EspacoForm(forms.ModelForm):
    """
    Formulário completo para cadastro/edição de espaços
    Para uso em dashboard de proprietários
    """
    
    class Meta:
        model = Espaco
        fields = [
            'nome', 'descricao_breve', 'descricao_completa',
            'endereco', 'cidade', 'cep', 'bairro',
            'tipo_espaco', 'aceita_locacao', 'tem_acessibilidade',
            'horario_manha_abertura', 'horario_manha_fechamento',
            'horario_tarde_abertura', 'horario_tarde_fechamento',
            'horario_noite_abertura', 'horario_noite_fechamento',
            'horario_fds_abertura', 'horario_fds_fechamento',
            'email', 'whatsapp', 'whatsapp_ativo', 'website', 
            'instagram', 'facebook', 'youtube', 'tiktok',
            'comodidades', 'especialidades', 'foto_principal'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar classes CSS consistentes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.URLInput)):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent resize-none',
                    'rows': '4'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'
                })
        
        
        # Widgets especiais
        self.fields['comodidades'].widget = forms.CheckboxSelectMultiple(attrs={
            'class': 'comodidades-grid'
        })
        self.fields['especialidades'].widget = forms.CheckboxSelectMultiple(attrs={
            'class': 'especialidades-grid'
        })
        
        # Placeholders informativos
        self.fields['nome'].widget.attrs['placeholder'] = 'Nome do seu espaço terapêutico'
        self.fields['descricao_breve'].widget.attrs['placeholder'] = 'Descrição breve para aparecer nos cards (máx 300 caracteres)'
        self.fields['endereco'].widget.attrs['placeholder'] = 'Endereço completo com número'
        self.fields['cep'].widget.attrs['placeholder'] = '12345-678'
        self.fields['email'].widget.attrs['placeholder'] = 'contato@seuespacovital.com'
        self.fields['whatsapp'].widget.attrs['placeholder'] = 'Digite apenas números: 21987654321'
        self.fields['website'].widget.attrs['placeholder'] = 'https://www.seuespacovital.com'
        self.fields['instagram'].widget.attrs['placeholder'] = 'seuespacovital (sem @)'
        self.fields['facebook'].widget.attrs['placeholder'] = 'https://facebook.com/seuperfil'
        self.fields['youtube'].widget.attrs['placeholder'] = 'https://youtube.com/@seucanal'
        self.fields['tiktok'].widget.attrs['placeholder'] = 'seuperfil (sem @)'
    
    def clean_cep(self):
        """
        Validação do CEP
        """
        cep = self.cleaned_data.get('cep')
        if cep:
            cep_limpo = ''.join(filter(str.isdigit, cep))
            if len(cep_limpo) != 8:
                raise forms.ValidationError('CEP deve ter 8 dígitos.')
            # Reformatar CEP
            return f'{cep_limpo[:5]}-{cep_limpo[5:]}'
        return cep
    
    def clean_instagram(self):
        """
        Validação do Instagram (remover @ se presente)
        """
        instagram = self.cleaned_data.get('instagram')
        if instagram:
            return instagram.replace('@', '')
        return instagram
    
# ===============================================================
# FORM PARA CADASTRO/EDIÇÃO DE COMODIDADE (ADMIN)
# ===============================================================

class ComodidadeForm(forms.ModelForm):
    """
    Formulário para cadastro/edição de comodidades no admin
    Inclui o campo slug para URLs amigáveis e dropdown de ícones
    """
    
    class Meta:
        model = Comodidade
        fields = ['nome', 'slug', 'icone', 'descricao', 'is_active', 'is_destaque']
        widgets = {
            'icone': forms.Select(attrs={
                'class': 'vTextField',
                'style': 'font-size: 14px;'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar classes CSS
        self.fields['nome'].widget.attrs.update({
            'class': 'vTextField',
            'placeholder': 'Nome da comodidade'
        })
        
        self.fields['slug'].widget.attrs.update({
            'class': 'vTextField',
            'placeholder': 'slug-da-comodidade'
        })
        
        # Icone já é dropdown automático pelo choices do model
        # Apenas garantimos o estilo
        self.fields['icone'].widget.attrs.update({
            'class': 'vTextField',
            'style': 'font-size: 14px;'
        })
        
        self.fields['descricao'].widget.attrs.update({
            'class': 'vLargeTextField',
            'rows': '3',
            'placeholder': 'Descrição detalhada da comodidade'
        })
        
        # Labels personalizados
        self.fields['nome'].label = 'Nome da Comodidade'
        self.fields['slug'].label = 'Slug (URL amigável)'
        self.fields['icone'].label = 'Ícone Representativo'
        self.fields['descricao'].label = 'Descrição'
        self.fields['is_active'].label = 'Ativo?'
        self.fields['is_destaque'].label = 'Destaque nos Filtros?'
        
        # Help texts informativos
        self.fields['slug'].help_text = 'URL amigável (será gerado automaticamente se deixar em branco)'
        self.fields['icone'].help_text = 'Selecione o ícone que melhor representa esta comodidade'
        self.fields['descricao'].help_text = 'Descrição detalhada que aparecerá nos detalhes da comodidade'
        self.fields['is_destaque'].help_text = 'Comodidades em destaque aparecem no topo dos filtros'
    
    def clean_slug(self):
        """
        Validação do slug
        Garante formato correto: apenas letras minúsculas, números e hífens
        """
        slug = self.cleaned_data.get('slug')
        if slug:
            # Validar formato do slug
            import re
            if not re.match(r'^[a-z0-9-]+$', slug):
                raise forms.ValidationError(
                    'Slug deve conter apenas letras minúsculas, números e hífens.'
                )
        return slug