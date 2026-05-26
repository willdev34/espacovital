"""
Título: Views do Fluxo de Onboarding
Descrição: Views responsáveis pelo processo de onboarding de novos usuários após o cadastro
Autor: Will
Data: 2024-12-13
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
from django.contrib import messages
from django.utils.text import slugify
from terapeutas.models import Terapeuta


@method_decorator(login_required, name='dispatch')
class WelcomeView(View):
    """
    View de boas-vindas ao fluxo de onboarding.
    
    Primeira tela após confirmação de email.
    Explica o fluxo e redireciona para seleção de plano.
    """
    
    template_name = 'onboarding/welcome.html'
    
    def get(self, request):
        """
        Exibe a tela de boas-vindas
        """
        # Verificar se o email foi confirmado
        if not request.user.emailaddress_set.filter(verified=True).exists():
            messages.warning(
                request, 
                'Por favor, confirme seu email antes de continuar.'
            )
            return redirect('account_email')
        
        # Verificar se já completou o onboarding
        # (se já tem perfil de terapeuta ou espaço criado)
        if hasattr(request.user, 'terapeuta') or hasattr(request.user, 'espacos'):
            messages.info(
                request,
                'Você já completou o processo de cadastro!'
            )
            # Redirecionar para o dashboard apropriado
            if hasattr(request.user, 'terapeuta'):
                return redirect('terapeutas:dashboard')
            else:
                return redirect('espacos:dashboard')
        
        # Pegar dados salvos na sessão durante o signup
        signup_data = request.session.get('signup_data', {})
        
        # Contexto para o template
        context = {
            'first_name': request.user.first_name,
            'tipo_perfil': signup_data.get('tipo_perfil', 'terapeuta'),
            'has_voucher': 'voucher_id' in signup_data,
        }
        
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
class SelectPlanView(View):
    """
    View de seleção de plano durante o onboarding.
    
    Mostra os planos disponíveis filtrados por tipo de perfil.
    Aplica desconto de voucher se houver.
    """
    
    template_name = 'onboarding/select_plan.html'
    
    def get(self, request):
        """
        Exibe os planos disponíveis para seleção
        """
        from .models import Plano, Voucher
        
        # Verificar se já completou o onboarding
        if hasattr(request.user, 'terapeuta') or hasattr(request.user, 'espacos'):
            messages.info(request, 'Você já completou o processo de cadastro!')
            if hasattr(request.user, 'terapeuta'):
                return redirect('terapeutas:dashboard')
            else:
                return redirect('espacos:dashboard')
        
        # Pegar dados da sessão
        signup_data = request.session.get('signup_data', {})
        tipo_perfil = signup_data.get('tipo_perfil', 'terapeuta')
        voucher_id = signup_data.get('voucher_id')
        
        # Buscar voucher se houver
        voucher = None
        if voucher_id:
            try:
                voucher = Voucher.objects.get(id=voucher_id)
                if not voucher.esta_valido():
                    voucher = None
                    messages.warning(request, 'O voucher não é mais válido.')
            except Voucher.DoesNotExist:
                pass
        
        # Filtrar planos baseado no tipo de perfil
        planos_disponiveis = Plano.objects.filter(is_active=True)
        
        # Aplicar filtro baseado no tipo
        if tipo_perfil == 'terapeuta':
            # Mostrar: Basic, Premium A, Combos
            planos_disponiveis = planos_disponiveis.filter(
                nome__in=['basic', 'premium_a', 'combo_a_s', 'combo_a_s_plus']
            )
        elif tipo_perfil == 'espaco':
            # Mostrar: Premium S, Premium S+, Combos
            planos_disponiveis = planos_disponiveis.filter(
                nome__in=['premium_s', 'premium_s_plus', 'combo_a_s', 'combo_a_s_plus']
            )
        else:  # ambos
            # Mostrar todos exceto Gratuito Filiado
            planos_disponiveis = planos_disponiveis.exclude(nome='gratuito_filiado')
        
        # Ordenar por ordem de exibição
        planos_disponiveis = planos_disponiveis.order_by('ordem_exibicao')
        
        # Calcular valores com desconto (se houver voucher)
        planos_com_desconto = []
        for plano in planos_disponiveis:
            plano_info = {
                'plano': plano,
                'valor_original': plano.valor,
                'tem_desconto': False,
                'valor_desconto': 0,
                'valor_final': plano.valor,
                'dias_gratuidade': 0,
            }
            
            # Aplicar voucher se existir e for aplicável
            if voucher and plano in voucher.planos_aplicaveis.all():
                desconto_info = voucher.calcular_desconto(plano.valor)
                plano_info['tem_desconto'] = True
                plano_info['valor_desconto'] = desconto_info['valor_desconto']
                plano_info['valor_final'] = desconto_info['valor_final']
                plano_info['dias_gratuidade'] = desconto_info.get('dias_gratuidade', 0)
            
            planos_com_desconto.append(plano_info)
        
        context = {
            'planos': planos_com_desconto,
            'tipo_perfil': tipo_perfil,
            'voucher': voucher,
            'first_name': request.user.first_name,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        """
        Salva o plano selecionado na sessão e redireciona para criar perfil
        """
        from .models import Plano
        
        plano_id = request.POST.get('plano_id')
        
        if not plano_id:
            messages.error(request, 'Por favor, selecione um plano.')
            return redirect('core:onboarding_select_plan')
        
        try:
            plano = Plano.objects.get(id=plano_id, is_active=True)
            
            # Verificar se o plano tem vagas (se aplicável)
            # tem_vagas() é um MÉTODO, precisa dos parênteses
            # Mas primeiro verifica se o plano tem limite de usuários
            if plano.max_usuarios and plano.max_usuarios > 0:
                # Contar quantos usuários já tem este plano
                from .models import Assinatura
                assinaturas_ativas = Assinatura.objects.filter(
                    plano=plano,
                    status__in=['trial', 'active']
                ).count()
                
                if assinaturas_ativas >= plano.max_usuarios:
                    messages.error(
                        request, 
                        f'O plano {plano.nome_exibicao} está lotado no momento. '
                        'Por favor, escolha outro plano.'
                    )
                    return redirect('core:onboarding_select_plan')
            
            # Salvar na sessão
            if 'signup_data' not in request.session:
                request.session['signup_data'] = {}
            
            request.session['signup_data']['plano_id'] = plano.id
            request.session.modified = True
            
            messages.success(
                request, 
                f'Plano {plano.nome_exibicao} selecionado com sucesso!'
            )
            
            # Redirecionar para criar perfil
            return redirect('core:onboarding_create_profile')
            
        except Plano.DoesNotExist:
            messages.error(request, 'Plano inválido.')
            return redirect('core:onboarding_select_plan')


@method_decorator(login_required, name='dispatch')
class CreateProfileView(View):
    """
    View de criação de perfil durante o onboarding.
    
    Wizard multi-step que adapta o formulário baseado no tipo de perfil:
    - Terapeuta: 1 step (formulário de terapeuta)
    - Espaço: 1 step (formulário de espaço)
    - Ambos: 2 steps (terapeuta + espaço com dados compartilhados)
    """
    
    template_name = 'onboarding/create_profile.html'
    
    def get(self, request):
        """
        Exibe o formulário apropriado baseado no tipo de perfil e step atual
        """
        from .forms_onboarding import (
            TerapeutaOnboardingForm, 
            EspacoOnboardingForm,
            DadosCompartilhadosForm
        )
        
        # Verificar se já completou o onboarding
        if hasattr(request.user, 'terapeuta') or hasattr(request.user, 'espacos'):
            messages.info(request, 'Você já completou o processo de cadastro!')
            if hasattr(request.user, 'terapeuta'):
                return redirect('terapeutas:dashboard')
            else:
                return redirect('espacos:dashboard')
        
        # Pegar dados da sessão
        signup_data = request.session.get('signup_data', {})
        tipo_perfil = signup_data.get('tipo_perfil', 'terapeuta')
        plano_id = signup_data.get('plano_id')
        
        # Verificar se selecionou um plano
        if not plano_id:
            messages.warning(request, 'Por favor, selecione um plano primeiro.')
            return redirect('core:onboarding_select_plan')
        
        # Determinar step atual (para "ambos")
        current_step = request.session.get('onboarding_step', 1)
        
        # Preparar contexto base
        context = {
            'tipo_perfil': tipo_perfil,
            'current_step': current_step,
            'total_steps': 2 if tipo_perfil == 'ambos' else 1,
            'first_name': request.user.first_name,
        }
        
        # Criar formulários baseado no tipo e step
        if tipo_perfil == 'terapeuta':
            # Apenas formulário de terapeuta
            form_terapeuta = TerapeutaOnboardingForm(
                initial={
                    'email_profissional': request.user.email,
                    'nome_completo': f'{request.user.first_name} {request.user.last_name}',
                    'nome_exibicao': request.user.first_name,
                    'whatsapp': signup_data.get('phone', ''),
                    'whatsapp_ativo': True,
                }
            )
            context['form_terapeuta'] = form_terapeuta
            context['show_terapeuta_form'] = True
            
        elif tipo_perfil == 'espaco':
            # Apenas formulário de espaço
            form_espaco = EspacoOnboardingForm(
                initial={
                    'email': request.user.email,
                    'whatsapp': signup_data.get('phone', ''),
                    'whatsapp_ativo': True,
                }
            )
            context['form_espaco'] = form_espaco
            context['show_espaco_form'] = True
            
        else:  # ambos
            # Wizard com 2 steps
            if current_step == 1:
                # Step 1: Terapeuta + Dados Compartilhados
                form_terapeuta = TerapeutaOnboardingForm(
                    initial={
                        'email_profissional': request.user.email,
                        'nome_completo': f'{request.user.first_name} {request.user.last_name}',
                        'nome_exibicao': request.user.first_name,
                        'whatsapp': signup_data.get('phone', ''),
                        'whatsapp_ativo': True,
                    }
                )
                form_compartilhado = DadosCompartilhadosForm(
                    initial={
                        'whatsapp': signup_data.get('phone', ''),
                        'whatsapp_ativo': True,
                        'pais': 1,  # Brasil
                    }
                )
                context['form_terapeuta'] = form_terapeuta
                context['form_compartilhado'] = form_compartilhado
                context['show_terapeuta_form'] = True
                context['show_compartilhado_form'] = True
                
            else:  # Step 2
                # Step 2: Espaço (usa dados compartilhados salvos)
                dados_compartilhados = request.session.get('dados_compartilhados', {})
                form_espaco = EspacoOnboardingForm(
                    initial={
                        'email': request.user.email,
                        'whatsapp': dados_compartilhados.get('whatsapp', ''),
                        'whatsapp_ativo': dados_compartilhados.get('whatsapp_ativo', True),
                        'pais': dados_compartilhados.get('pais'),
                        'estado': dados_compartilhados.get('estado'),
                        'cidade': dados_compartilhados.get('cidade_principal'),
                        'cidade_texto': dados_compartilhados.get('cidade_texto', ''),
                    }
                )
                context['form_espaco'] = form_espaco
                context['show_espaco_form'] = True
                context['dados_compartilhados'] = dados_compartilhados
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        """
        Processa o formulário e cria os perfis
        """
        from .forms_onboarding import (
            TerapeutaOnboardingForm, 
            EspacoOnboardingForm,
            DadosCompartilhadosForm
        )
        from .models import Plano, Assinatura, HistoricoAssinatura, Voucher
        from terapeutas.models import TerapeutaEspecialidade
        from datetime import date, timedelta
        
        signup_data = request.session.get('signup_data', {})
        tipo_perfil = signup_data.get('tipo_perfil', 'terapeuta')
        plano_id = signup_data.get('plano_id')
        voucher_id = signup_data.get('voucher_id')
        current_step = request.session.get('onboarding_step', 1)
        
        # Buscar plano
        try:
            plano = Plano.objects.get(id=plano_id, is_active=True)
        except Plano.DoesNotExist:
            messages.error(request, 'Plano inválido.')
            return redirect('core:onboarding_select_plan')
        
        # Buscar voucher se houver
        voucher = None
        if voucher_id:
            try:
                voucher = Voucher.objects.get(id=voucher_id)
                if not voucher.esta_valido():
                    voucher = None
            except Voucher.DoesNotExist:
                pass
        
        # Processar baseado no tipo
        if tipo_perfil == 'terapeuta':
            # Criar apenas terapeuta
            return self._criar_terapeuta(request, plano, voucher)
            
        elif tipo_perfil == 'espaco':
            # Criar apenas espaço
            return self._criar_espaco(request, plano, voucher)
            
        else:  # ambos
            if current_step == 1:
                # Step 1: Salvar terapeuta e dados compartilhados
                return self._processar_step_1(request)
            else:
                # Step 2: Criar espaço e finalizar
                return self._processar_step_2(request, plano, voucher)
    
    def _criar_terapeuta(self, request, plano, voucher):
        """
        Cria perfil de terapeuta e assinatura
        """
        from .forms_onboarding import TerapeutaOnboardingForm
        from terapeutas.models import TerapeutaEspecialidade, Terapeuta
        from .models import Assinatura, HistoricoAssinatura
        from datetime import date, timedelta
        
        form = TerapeutaOnboardingForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Criar terapeuta
            terapeuta = form.save(commit=False)
            terapeuta.user = request.user

            # Gerar slug único
            base_slug = slugify(terapeuta.nome_exibicao)
            slug = base_slug
            contador = 1

            # Verificar se slug já existe e adicionar número se necessário
            while Terapeuta.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{contador}"
                contador += 1

            terapeuta.slug = slug
            terapeuta.save()

            # Salvar especialidades
            especialidades = form.cleaned_data.get('especialidades', [])
            for especialidade in especialidades:
                TerapeutaEspecialidade.objects.create(
                    terapeuta=terapeuta,
                    especialidade=especialidade
                )

            # Criar assinatura
            data_inicio = date.today()
            data_fim_trial = None

            # Calcular data de fim do trial
            if voucher and voucher.tipo_desconto == 'gratuidade':
                # Voucher de gratuidade
                data_fim_trial = data_inicio + timedelta(days=voucher.dias_gratuidade)
            elif plano.dias_trial > 0:
                # Trial padrão do plano
                data_fim_trial = data_inicio + timedelta(days=plano.dias_trial)

            assinatura = Assinatura.objects.create(
                usuario=request.user,
                plano=plano,
                status='trial' if data_fim_trial else 'active',
                data_inicio=data_inicio,
                data_fim_trial=data_fim_trial,
                voucher_utilizado=voucher
            )

            # NOVO: Atualizar o plano do terapeuta baseado no plano da assinatura
            # Mapear nome do plano (core.Plano) para campo plano do Terapeuta
            plano_map = {
                'basic': 'basic',
                'premium_a': 'premium_a',
                'premium_s': 'premium_s',
                'combo_a_s': 'premium_a',  # Combo usa premium_a no terapeuta
                'combo_a_s_plus': 'premium_a',  # Combo usa premium_a no terapeuta
            }

            terapeuta_plano = plano_map.get(plano.nome, 'basic')
            terapeuta.plano = terapeuta_plano
            terapeuta.data_assinatura_plano = data_inicio
            terapeuta.save(update_fields=['plano', 'data_assinatura_plano'])
            
            # Registrar uso do voucher
            if voucher:
                voucher.registrar_uso()
            
            # Criar histórico
            HistoricoAssinatura.objects.create(
                assinatura=assinatura,
                acao='Assinatura criada via onboarding',
                plano_novo=plano,
                realizado_por=request.user
            )
            
            # Limpar sessão
            if 'signup_data' in request.session:
                del request.session['signup_data']
            
            messages.success(
                request,
                f'Parabéns! Seu perfil de terapeuta foi criado com sucesso! '
                f'{"Você tem " + str(plano.dias_trial) + " dias grátis para testar." if data_fim_trial else ""}'
            )
            
            return redirect('terapeutas:dashboard')
        
        # Se houver erros, re-renderizar
        context = {
            'form_terapeuta': form,
            'show_terapeuta_form': True,
            'tipo_perfil': 'terapeuta',
            'current_step': 1,
            'total_steps': 1,
            'first_name': request.user.first_name,
        }
        return render(request, self.template_name, context)
    
    def _criar_espaco(self, request, plano, voucher):
        """
        Cria perfil de espaço e assinatura
        """
        from .forms_onboarding import EspacoOnboardingForm
        from .models import Assinatura, HistoricoAssinatura
        from datetime import date, timedelta
        
        form = EspacoOnboardingForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Criar espaço
            espaco = form.save(commit=False)
            espaco.responsavel = request.user
            espaco.save()
            
            # Criar assinatura
            data_inicio = date.today()
            data_fim_trial = None
            
            if voucher and voucher.tipo_desconto == 'gratuidade':
                data_fim_trial = data_inicio + timedelta(days=voucher.dias_gratuidade)
            elif plano.dias_trial > 0:
                data_fim_trial = data_inicio + timedelta(days=plano.dias_trial)
            
            assinatura = Assinatura.objects.create(
                usuario=request.user,
                plano=plano,
                status='trial' if data_fim_trial else 'active',
                data_inicio=data_inicio,
                data_fim_trial=data_fim_trial,
                voucher_utilizado=voucher
            )
            
            if voucher:
                voucher.registrar_uso()
            
            HistoricoAssinatura.objects.create(
                assinatura=assinatura,
                acao='Assinatura criada via onboarding',
                plano_novo=plano,
                realizado_por=request.user
            )
            
            # Limpar sessão
            if 'signup_data' in request.session:
                del request.session['signup_data']
            
            messages.success(
                request,
                f'Parabéns! Seu espaço terapêutico foi cadastrado com sucesso! '
                f'{"Você tem " + str(plano.dias_trial) + " dias grátis para testar." if data_fim_trial else ""}'
            )
            
            return redirect('espacos:dashboard')
        
        # Se houver erros, re-renderizar
        context = {
            'form_espaco': form,
            'show_espaco_form': True,
            'tipo_perfil': 'espaco',
            'current_step': 1,
            'total_steps': 1,
            'first_name': request.user.first_name,
        }
        return render(request, self.template_name, context)
    
    def _processar_step_1(self, request):
        """
        Processa Step 1 (Terapeuta + Dados Compartilhados) quando tipo = 'ambos'
        """
        from .forms_onboarding import TerapeutaOnboardingForm, DadosCompartilhadosForm
        from terapeutas.models import TerapeutaEspecialidade
        
        form_terapeuta = TerapeutaOnboardingForm(request.POST, request.FILES)
        form_compartilhado = DadosCompartilhadosForm(request.POST)
        
        if form_terapeuta.is_valid() and form_compartilhado.is_valid():
            # Criar terapeuta (ainda sem assinatura)
            terapeuta = form_terapeuta.save(commit=False)
            terapeuta.user = request.user

            # Aplicar dados compartilhados
            terapeuta.whatsapp = form_compartilhado.cleaned_data['whatsapp']
            terapeuta.whatsapp_ativo = form_compartilhado.cleaned_data['whatsapp_ativo']
            terapeuta.pais = form_compartilhado.cleaned_data['pais']
            terapeuta.estado = form_compartilhado.cleaned_data.get('estado')
            terapeuta.cidade_principal = form_compartilhado.cleaned_data.get('cidade_principal')
            terapeuta.cidade_texto = form_compartilhado.cleaned_data.get('cidade_texto', '')

            # Gerar slug único
            base_slug = slugify(terapeuta.nome_exibicao)
            slug = base_slug
            contador = 1

            while Terapeuta.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{contador}"
                contador += 1

            terapeuta.slug = slug
            terapeuta.save()
            
            # Salvar especialidades
            especialidades = form_terapeuta.cleaned_data.get('especialidades', [])
            for especialidade in especialidades:
                TerapeutaEspecialidade.objects.create(
                    terapeuta=terapeuta,
                    especialidade=especialidade,
                    ordem=0
                )
            
            # Salvar dados compartilhados na sessão
            request.session['dados_compartilhados'] = {
                'whatsapp': form_compartilhado.cleaned_data['whatsapp'],
                'whatsapp_ativo': form_compartilhado.cleaned_data['whatsapp_ativo'],
                'pais': form_compartilhado.cleaned_data['pais'].id,
                'estado': form_compartilhado.cleaned_data.get('estado').id if form_compartilhado.cleaned_data.get('estado') else None,
                'cidade_principal': form_compartilhado.cleaned_data.get('cidade_principal').id if form_compartilhado.cleaned_data.get('cidade_principal') else None,
                'cidade_texto': form_compartilhado.cleaned_data.get('cidade_texto', ''),
            }
            
            # Avançar para step 2
            request.session['onboarding_step'] = 2
            request.session.modified = True
            
            messages.success(request, 'Perfil de terapeuta criado! Agora vamos configurar seu espaço.')
            
            return redirect('core:onboarding_create_profile')
        
        # Se houver erros, re-renderizar
        context = {
            'form_terapeuta': form_terapeuta,
            'form_compartilhado': form_compartilhado,
            'show_terapeuta_form': True,
            'show_compartilhado_form': True,
            'tipo_perfil': 'ambos',
            'current_step': 1,
            'total_steps': 2,
            'first_name': request.user.first_name,
        }
        return render(request, self.template_name, context)
    
    def _processar_step_2(self, request, plano, voucher):
        """
        Processa Step 2 (Espaço) quando tipo = 'ambos' e finaliza onboarding
        """
        from .forms_onboarding import EspacoOnboardingForm
        from .models import Assinatura, HistoricoAssinatura
        from datetime import date, timedelta
        
        form_espaco = EspacoOnboardingForm(request.POST, request.FILES)
        
        if form_espaco.is_valid():
            # Criar espaço
            espaco = form_espaco.save(commit=False)
            espaco.responsavel = request.user
            espaco.save()
            
            # Criar assinatura (uma única para ambos)
            data_inicio = date.today()
            data_fim_trial = None
            
            if voucher and voucher.tipo_desconto == 'gratuidade':
                data_fim_trial = data_inicio + timedelta(days=voucher.dias_gratuidade)
            elif plano.dias_trial > 0:
                data_fim_trial = data_inicio + timedelta(days=plano.dias_trial)
            
            assinatura = Assinatura.objects.create(
                usuario=request.user,
                plano=plano,
                status='trial' if data_fim_trial else 'active',
                data_inicio=data_inicio,
                data_fim_trial=data_fim_trial,
                voucher_utilizado=voucher
            )
            
            if voucher:
                voucher.registrar_uso()
            
            HistoricoAssinatura.objects.create(
                assinatura=assinatura,
                acao='Assinatura criada via onboarding (Terapeuta + Espaço)',
                plano_novo=plano,
                realizado_por=request.user
            )
            
            # Limpar sessão
            if 'signup_data' in request.session:
                del request.session['signup_data']
            if 'dados_compartilhados' in request.session:
                del request.session['dados_compartilhados']
            if 'onboarding_step' in request.session:
                del request.session['onboarding_step']
            
            messages.success(
                request,
                f'Parabéns! Seus perfis foram criados com sucesso! '
                f'{"Você tem " + str(plano.dias_trial) + " dias grátis para testar." if data_fim_trial else ""}'
            )
            
            # Redirecionar para seleção de perfil
            return redirect('terapeutas:dashboard')  # Ou criar uma view de seleção
        
        # Se houver erros, re-renderizar
        dados_compartilhados = request.session.get('dados_compartilhados', {})
        context = {
            'form_espaco': form_espaco,
            'show_espaco_form': True,
            'tipo_perfil': 'ambos',
            'current_step': 2,
            'total_steps': 2,
            'first_name': request.user.first_name,
            'dados_compartilhados': dados_compartilhados,
        }
        return render(request, self.template_name, context)