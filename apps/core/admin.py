"""
Configuração do admin para o app Core
"""

from django.contrib import admin
from .models import PageContent, ContentCard


@admin.register(ContentCard)
class ContentCardAdmin(admin.ModelAdmin):
    """Admin para cards de conteúdo"""
    list_display = ['title', 'page', 'card_type', 'order', 'is_active', 'updated_at']
    list_filter = ['page', 'card_type', 'is_active']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_editable = ['order', 'is_active']
    ordering = ['page', 'order']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('page', 'card_type', 'title', 'order', 'is_active')
        }),
        ('Conteúdo', {
            'fields': ('content',),
        }),
        ('Metadados', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Registra quem criou/atualizou"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    """Admin para conteúdo de páginas"""
    list_display = ['page_key', 'title', 'updated_by', 'updated_at']
    list_filter = ['page_key', 'updated_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('page_key', 'title')
        }),
        ('Conteúdo', {
            'fields': ('content',),
            'description': 'Use HTML para formatar o conteúdo.'
        }),
        ('Metadados', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Registra quem atualizou"""
        if change:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
