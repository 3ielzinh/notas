"""
Decorators para controle de acesso baseado em roles
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Role


def role_required(roles):
    """
    Decorator que verifica se o usuário tem um dos roles especificados.
    
    Args:
        roles: Lista de roles permitidos (Role.VISUALIZAR, Role.ANALISTA, Role.ADMIN)
        
    Usage:
        @role_required([Role.ADMIN])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar se está autenticado
            if not request.user.is_authenticated:
                messages.warning(request, 'Você precisa fazer login para acessar esta página.')
                return redirect('accounts:login')
            
            # Verificar se tem perfil
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'Seu usuário não possui um perfil configurado.')
                return redirect('home')
            
            # Verificar role
            if request.user.profile.role not in roles:
                messages.error(request, 'Você não tem permissão para acessar esta página.')
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator que permite apenas usuários com role ADMIN.
    
    Usage:
        @admin_required
        def my_view(request):
            ...
    """
    return role_required([Role.ADMIN])(view_func)


def analyst_required(view_func):
    """
    Decorator que permite usuários ANALISTA e ADMIN.
    
    Usage:
        @analyst_required
        def my_view(request):
            ...
    """
    return role_required([Role.ANALISTA, Role.ADMIN])(view_func)


def authenticated_required(view_func):
    """
    Decorator que permite qualquer usuário autenticado.
    
    Usage:
        @authenticated_required
        def my_view(request):
            ...
    """
    return role_required([Role.VISUALIZAR, Role.ANALISTA, Role.ADMIN])(view_func)
