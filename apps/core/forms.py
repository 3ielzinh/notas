"""
Forms para gerenciamento de conteúdo de páginas
"""

from django import forms
from .models import PageContent, ContentCard


class ContentCardForm(forms.ModelForm):
    """Formulário para edição de cards de conteúdo"""
    
    class Meta:
        model = ContentCard
        fields = ['title', 'content', 'link', 'card_type', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do card'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Conteúdo do card (HTML ou texto)'
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://exemplo.com/recurso'
            }),
            'card_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'content': 'Conteúdo',
            'link': 'Link (opcional)',
            'card_type': 'Tipo de Card',
            'order': 'Ordem',
            'is_active': 'Ativo',
        }
        help_texts = {
            'content': 'Use HTML para formatar: <p>, <ul>, <li>, <strong>, <em>, etc.',
            'link': 'URL completa para um recurso ou página externa (opcional)',
            'order': 'Menor valor aparece primeiro',
        }


class PageContentForm(forms.ModelForm):
    """Formulário para edição de conteúdo de páginas"""
    
    class Meta:
        model = PageContent
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da página'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 25,
                'placeholder': 'Conteúdo da página em HTML...'
            }),
        }
        labels = {
            'title': 'Título',
            'content': 'Conteúdo (HTML)',
        }
        help_texts = {
            'content': 'Use HTML para formatar o conteúdo. Tags disponíveis: <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <a>, <code>, etc.'
        }
