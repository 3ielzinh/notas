"""
Forms para autenticação
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class LoginForm(AuthenticationForm):
    """Form customizado de login"""
    
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome de usuário',
            'autofocus': True
        }),
        label='Usuário'
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha'
        }),
        label='Senha'
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Lembrar-me'
    )


class RegisterForm(UserCreationForm):
    """Form customizado de registro"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'nome.sobrenome@inss.gov.br',
            'autofocus': True
        }),
        label='E-mail Institucional',
        help_text='Utilize seu e-mail institucional @inss.gov.br'
    )
    
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        }),
        label='Senha',
        help_text='Sua senha deve conter pelo menos 8 caracteres.'
    )
    
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        }),
        label='Confirmação de senha'
    )
    
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Validar domínio institucional
        if not email.endswith('@inss.gov.br'):
            raise ValidationError('Apenas e-mails institucionais @inss.gov.br são permitidos.')
        
        # Verificar se já existe
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está cadastrado.')
        
        return email
