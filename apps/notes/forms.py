"""
Forms para gerenciamento de notas
"""

from django import forms
from .models import Note


class NoteEditForm(forms.ModelForm):
    """Formulário para edição de notas técnicas"""
    
    class Meta:
        model = Note
        fields = ['note_name', 'note_year', 'situacao', 'justificativa', 'sanitized_text']
        widgets = {
            'note_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da nota técnica (sem extensão)'
            }),
            'note_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2025',
                'min': 2000,
                'max': 2100
            }),
            'situacao': forms.Select(attrs={
                'class': 'form-control'
            }),
            'justificativa': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva o motivo da revogação ou alteração...'
            }),
            'sanitized_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 20,
                'placeholder': 'Texto completo da nota técnica...'
            }),
        }
        labels = {
            'note_name': 'Título da Nota',
            'note_year': 'Ano',
            'situacao': 'Situação',
            'justificativa': 'Observação/Justificativa',
            'sanitized_text': 'Texto da Nota (conteúdo pesquisável)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def clean_note_name(self):
        """Remove extensões .pdf ou .txt do nome"""
        name = self.cleaned_data.get('note_name', '').strip()
        
        # Remove extensões conhecidas
        for ext in ['.pdf', '.txt', '.PDF', '.TXT']:
            if name.endswith(ext):
                name = name[:-len(ext)]
        
        return name.strip()
    
    def clean_note_year(self):
        """Valida ano"""
        year = self.cleaned_data.get('note_year')
        
        if year and (year < 2000 or year > 2100):
            raise forms.ValidationError('Informe um ano válido entre 2000 e 2100.')
        
        return year


class NoteSearchForm(forms.Form):
    """Formulário de busca de notas para edição"""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Pesquisar por título, ano ou conteúdo...',
            'autocomplete': 'off'
        }),
        label=''
    )
