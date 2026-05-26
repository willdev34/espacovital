# ===============================================================
# Título: Forms do App Espacos - Espaço Vital
# Descrição: Formulários para contato, avaliação e edição de espaços terapêuticos
#
# Data: 26/12/2025
# ===============================================================

from django import forms
from django.core.validators import EmailValidator, RegexValidator
from core.models import Pais, Estado, Cidade, Especialidade
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
# FORMULÁRIO UNIFICADO - ADMIN E DASHBOARD
# ===============================================================

class EspacoForm(forms.ModelForm):
    """
    Formulário UNIFICADO para cadastro/edição de espaços
    Usado tanto no Django Admin quanto no Dashboard do proprietário
    
    IMPORTANTE: Este formulário sincroniza dados entre Admin e Dashboard.
    O que for cadastrado em um lugar, aparecerá no outro automaticamente.
    """
    
    # ===== CAMPO ESTADO (para cascata dinâmica País → Estado → Cidade) =====
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.none(),
        required=False,
        label='Estado',
        help_text='Selecione o estado (apenas para Brasil)',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
            'id': 'id_estado'
        })
    )
    
    # ===== CHECKBOXES DE DISPONIBILIDADE =====
    # Esses campos serão convertidos para JSONField ao salvar
    
    disponibilidade_manha = forms.BooleanField(
        required=False,
        label='Manhã',
        help_text='Disponível no período da manhã (06h - 12h)',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
        })
    )
    
    disponibilidade_tarde = forms.BooleanField(
        required=False,
        label='Tarde',
        help_text='Disponível no período da tarde (12h - 18h)',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
        })
    )
    
    disponibilidade_noite = forms.BooleanField(
        required=False,
        label='Noite',
        help_text='Disponível no período da noite (18h - 23h)',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
        })
    )
    
    disponibilidade_finais_semana = forms.BooleanField(
        required=False,
        label='Finais de semana',
        help_text='Disponível aos sábados e domingos',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
        })
    )
    
    class Meta:
        model = Espaco
        exclude = ['responsavel', 'slug', 'created_at', 'updated_at']
        widgets = {
            # ===== INFORMAÇÕES BÁSICAS =====
            'nome': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nome do espaço terapêutico'
            }),
            'descricao_breve': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descrição breve para cards (máximo 300 caracteres)',
                'rows': 3,
                'maxlength': 300
            }),
            'descricao_completa': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descrição completa do espaço, suas características e diferenciais',
                'rows': 6
            }),
            
            # ===== LOCALIZAÇÃO =====
            'pais': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'id': 'id_pais'
            }),
            'cidade': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'id': 'id_cidade'
            }),
            'cidade_texto': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nome da cidade (para países fora do Brasil)'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nome do bairro'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Endereço completo'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '00000-000'
            }),
            
            # ===== TIPO E CONFIGURAÇÕES =====
            'tipo_espaco': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'aceita_locacao': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
            }),
            'tem_acessibilidade': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
            }),
            
            # ===== CONTATO =====
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'email@exemplo.com'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '21987654321'
            }),
            'whatsapp_ativo': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://seusite.com.br'
            }),
            
            # ===== REDES SOCIAIS =====
            'instagram': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://instagram.com/seu_usuario'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://facebook.com/seu_perfil'
            }),
            'youtube': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://youtube.com/@seu_canal'
            }),
            'tiktok': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://tiktok.com/@seu_usuario'
            }),
            
            # ===== GALERIA (até 7 fotos) =====
            'foto_galeria_1': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'foto_galeria_2': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'foto_galeria_3': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'foto_galeria_4': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'foto_galeria_5': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'foto_galeria_6': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'foto_galeria_7': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            
            # ===== RELACIONAMENTOS M2M =====
            'comodidades': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
            'especialidades': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ===== POPULAR QUERYSETS =====
        
        # Países ativos
        self.fields['pais'].queryset = Pais.objects.filter(ativo=True).order_by('nome')
        
        # Estados do Brasil (apenas se país for Brasil)
        self.fields['estado'].queryset = Estado.objects.filter(
            pais__nome='Brasil',
            ativo=True
        ).order_by('nome')
        
        # Especialidades ativas
        self.fields['especialidades'].queryset = Especialidade.objects.filter(
            is_active=True
        ).order_by('categoria', 'nome')
        
        # Comodidades ativas
        self.fields['comodidades'].queryset = Comodidade.objects.filter(
            is_active=True
        ).order_by('-is_destaque', 'nome')
        
        # ===== CARREGAR VALORES DE DISPONIBILIDADE (ao editar) =====
        if self.instance and self.instance.pk:
            # O model usa horarios_semana (JSONField) ao invés de disponibilidade
            # Por enquanto, deixar os checkboxes desmarcados (valores padrão)
            # TODO: Implementar lógica para converter horarios_semana em checkboxes
            
            # Popular campo estado se houver cidade selecionada
            if self.instance.cidade:
                self.fields['estado'].initial = self.instance.cidade.estado
                self.fields['cidade'].queryset = Cidade.objects.filter(
                    estado=self.instance.cidade.estado,
                    ativo=True
                ).order_by('nome')
        
        # ===== LABELS PERSONALIZADOS =====
        self.fields['nome'].label = 'Nome do Espaço *'
        self.fields['descricao_breve'].label = 'Descrição Breve *'
        self.fields['descricao_completa'].label = 'Descrição Completa'
        self.fields['tipo_espaco'].label = 'Tipo de Espaço'
        self.fields['aceita_locacao'].label = 'Aceita Locação por Hora?'
        self.fields['tem_acessibilidade'].label = 'Possui Acessibilidade?'
        self.fields['comodidades'].label = 'Comodidades Disponíveis'
        self.fields['especialidades'].label = 'Terapias/Especialidades Oferecidas'
        self.fields['pais'].label = 'País *'
        self.fields['estado'].label = 'Estado (apenas Brasil)'
        self.fields['cidade'].label = 'Cidade *'
        self.fields['cidade_texto'].label = 'Cidade (outros países)'
        self.fields['bairro'].label = 'Bairro'
        self.fields['endereco'].label = 'Endereço Completo'
        self.fields['cep'].label = 'CEP'
        self.fields['email'].label = 'Email de Contato *'
        self.fields['whatsapp'].label = 'WhatsApp *'
        self.fields['whatsapp_ativo'].label = 'Este número é WhatsApp?'
        self.fields['website'].label = 'Website (opcional)'
        self.fields['instagram'].label = 'Instagram (opcional)'
        self.fields['facebook'].label = 'Facebook (opcional)'
        self.fields['youtube'].label = 'YouTube (opcional)'
        self.fields['tiktok'].label = 'TikTok (opcional)'
        self.fields['foto_principal'].label = 'Foto Principal'
    
    def clean_whatsapp(self):
        """
        Validação e formatação do WhatsApp
        Aceita números com ou sem formatação
        """
        whatsapp = self.cleaned_data.get('whatsapp')
        if whatsapp:
            # Remove TODOS os caracteres não numéricos
            whatsapp_limpo = ''.join(filter(str.isdigit, whatsapp))
            
            # Valida quantidade de dígitos (10 ou 11)
            if len(whatsapp_limpo) not in [10, 11]:
                raise forms.ValidationError(
                    f'WhatsApp deve ter 10 ou 11 dígitos. Você digitou {len(whatsapp_limpo)} dígitos.'
                )
            
            # Retorna SEM formatação (só números)
            return whatsapp_limpo
        
        return whatsapp
    
    def clean_cep(self):
        """
        Validação e formatação do CEP
        Formata para XXXXX-XXX
        """
        cep = self.cleaned_data.get('cep')
        if cep:
            # Remove caracteres especiais
            cep_limpo = ''.join(filter(str.isdigit, cep))
            
            # Valida quantidade de dígitos
            if len(cep_limpo) != 8:
                raise forms.ValidationError('CEP deve ter 8 dígitos')
            
            # Retorna formatado: 00000-000
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
    
    def clean(self):
        """
        Validação geral do formulário
        Garante consistência entre os campos de localização
        """
        cleaned_data = super().clean()
        
        # ===== VALIDAÇÃO DE LOCALIZAÇÃO =====
        pais = cleaned_data.get('pais')
        estado = cleaned_data.get('estado')
        cidade = cleaned_data.get('cidade')
        cidade_texto = cleaned_data.get('cidade_texto')
        
        # Se país é Brasil, exigir estado e cidade
        if pais and 'Brasil' in pais.nome:
            if not estado:
                self.add_error('estado', 'Estado é obrigatório para espaços no Brasil')
            if not cidade:
                self.add_error('cidade', 'Cidade é obrigatória para espaços no Brasil')
        else:
            # Se não é Brasil, exigir cidade_texto
            if not cidade_texto:
                self.add_error('cidade_texto', 'Nome da cidade é obrigatório para espaços fora do Brasil')
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Salvar o formulário convertendo checkboxes para JSONField
        
        IMPORTANTE: Este método converte os 4 checkboxes de disponibilidade
        para uma lista JSON que será salva no campo 'disponibilidade' do model.
        """
        espaco = super().save(commit=False)
        
        # ===== MONTAR LISTA DE DISPONIBILIDADE =====
        disponibilidade = []
        
        if self.cleaned_data.get('disponibilidade_manha'):
            disponibilidade.append('manha')
        if self.cleaned_data.get('disponibilidade_tarde'):
            disponibilidade.append('tarde')
        if self.cleaned_data.get('disponibilidade_noite'):
            disponibilidade.append('noite')
        if self.cleaned_data.get('disponibilidade_finais_semana'):
            disponibilidade.append('finais_de_semana')
        
        # Atribuir ao model (JSONField)
        espaco.disponibilidade = disponibilidade
        
        # ===== ATRIBUIR ESTADO (se for Brasil) =====
        cidade = self.cleaned_data.get('cidade')
        if cidade:
            espaco.estado = cidade.estado
        
        if commit:
            espaco.save()
            self.save_m2m()  # Salvar relacionamentos M2M (comodidades, especialidades)
        
        return espaco


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
        self.fields['estado'].queryset = Estado.objects.all().order_by('nome')
        self.fields['especialidades'].queryset = Especialidade.objects.filter(
            is_active=True
        ).order_by('categoria', 'nome')
        self.fields['comodidades'].queryset = Comodidade.objects.filter(
            is_active=True
        ).order_by('-is_destaque', 'nome')


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