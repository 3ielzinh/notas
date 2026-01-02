"""
Configuração do Django Admin para Accounts
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Role


class UserProfileInline(admin.StackedInline):
    """Inline para editar perfil junto com usuário"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil'
    verbose_name_plural = 'Perfil'
    fields = ['role']


class UserAdmin(BaseUserAdmin):
    """Admin customizado para User com Profile inline"""
    inlines = [UserProfileInline]
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'profile__role']
    
    def get_role(self, obj):
        """Exibe o papel do usuário"""
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '-'
    get_role.short_description = 'Perfil de Acesso'
    get_role.admin_order_field = 'profile__role'


# Re-registra UserAdmin com Profile
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para gerenciamento direto de Perfis"""
    
    list_display = ['user', 'role', 'created_at', 'updated_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user', 'role')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    
    def get_queryset(self, request):
        """Otimiza query"""
        qs = super().get_queryset(request)
        return qs.select_related('user')
