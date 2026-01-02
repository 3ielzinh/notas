"""
Views para autenticação e gerenciamento de usuários
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from .forms import LoginForm, RegisterForm
from .models import UserProfile


class LoginView(View):
    """View de login"""
    
    template_name = 'accounts/login.html'
    form_class = LoginForm
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        # Se já estiver autenticado, redireciona
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        """Exibe o formulário de login"""
        form = self.form_class()
        next_url = request.GET.get('next', '')
        return render(request, self.template_name, {
            'form': form,
            'next': next_url
        })
    
    def post(self, request):
        """Processa o login"""
        form = self.form_class(data=request.POST)
        next_url = request.POST.get('next', 'home')
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Autenticar usuário
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Login bem-sucedido
                login(request, user)
                
                # Configurar duração da sessão
                if not remember_me:
                    request.session.set_expiry(0)  # Expira ao fechar o navegador
                else:
                    request.session.set_expiry(1209600)  # 2 semanas
                
                # Mensagem de sucesso
                messages.success(request, f'Bem-vindo(a), {user.first_name or user.username}!')
                
                # Redirecionar
                if next_url and next_url != 'None':
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
        
        return render(request, self.template_name, {
            'form': form,
            'next': next_url
        })


@login_required
def logout_view(request):
    """View de logout"""
    username = request.user.username
    logout(request)
    messages.info(request, f'Você saiu do sistema, {username}. Até logo!')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """View de perfil do usuário"""
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': request.user.profile
    })


class RegisterView(View):
    """View de registro de novos usuários"""
    
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        # Se já estiver autenticado, redireciona
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        """Exibe o formulário de registro"""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """Processa o registro"""
        form = self.form_class(data=request.POST)
        
        if form.is_valid():
            # Gerar username a partir do email (parte antes do @)
            email = form.cleaned_data['email']
            username = email.split('@')[0]  # nome.sobrenome
            
            # Verificar se username já existe e adicionar sufixo se necessário
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Criar usuário
            user = form.save(commit=False)
            user.username = username
            user.email = email
            user.save()
            
            # O perfil é criado automaticamente pelo signal post_save
            
            # Login automático após registro
            login(request, user)
            
            messages.success(request, f'Bem-vindo(a), {user.username}! Sua conta foi criada com sucesso.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
        
        return render(request, self.template_name, {'form': form})

