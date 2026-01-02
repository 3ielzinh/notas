"""
Configuração do Django Admin para Notes
"""

from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from .models import Note
from .services.pdf_processor import PDFProcessor


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Admin para gerenciamento de Notas Técnicas"""
    
    list_display = ['note_name', 'note_year', 'imported_by', 'word_count', 'download_pdf_link', 'created_at']
    list_filter = ['note_year', 'created_at', 'imported_by']
    search_fields = ['note_name', 'sanitized_text', 'original_text']
    readonly_fields = ['source_hash', 'created_at', 'updated_at', 'display_text_info', 'pdf_filename']
    
    fieldsets = (
        ('Informações da Nota', {
            'fields': ('note_name', 'note_year', 'source_path', 'pdf_filename')
        }),
        ('Conteúdo', {
            'fields': ('original_text', 'sanitized_text'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('source_hash', 'imported_by', 'created_at', 'updated_at', 'display_text_info'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def download_pdf_link(self, obj):
        """Link para download do PDF"""
        if obj.pdf_content:
            return format_html(
                '<a href="{}">📄 Baixar PDF</a>',
                f'/admin/notes/note/{obj.pk}/download-pdf/'
            )
        return '-'
    download_pdf_link.short_description = 'PDF'
    
    def word_count(self, obj):
        """Exibe contagem de palavras"""
        return f"{obj.get_word_count()} palavras"
    word_count.short_description = 'Tamanho'
    
    def display_text_info(self, obj):
        """Exibe informações sobre o texto"""
        return format_html(
            '<strong>Palavras:</strong> {}<br>'
            '<strong>Caracteres:</strong> {}<br>'
            '<strong>Hash:</strong> {}',
            obj.get_word_count(),
            obj.get_char_count(),
            obj.source_hash[:16] + '...'
        )
    display_text_info.short_description = 'Informações do Texto'
    
    def get_urls(self):
        """Adiciona URLs customizadas"""
        urls = super().get_urls()
        custom_urls = [
            path('importar-pdf/', self.admin_site.admin_view(self.import_pdf), name='notes_note_import_pdf'),
            path('<int:note_id>/download-pdf/', self.admin_site.admin_view(self.download_pdf), name='notes_note_download_pdf'),
        ]
        return custom_urls + urls
    
    def download_pdf(self, request, note_id):
        """View para download do PDF do banco"""
        note = Note.objects.get(pk=note_id)
        
        if not note.pdf_content:
            messages.error(request, 'PDF não disponível.')
            return redirect('admin:notes_note_changelist')
        
        # Cria resposta HTTP com o PDF
        response = HttpResponse(bytes(note.pdf_content), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{note.pdf_filename or "nota.pdf"}"'
        
        return response
    
    def import_pdf(self, request):
        """View para importação de PDF com anonimização"""
        if request.method == 'POST' and request.FILES.get('pdf_file'):
            pdf_file = request.FILES['pdf_file']
            
            # Validação básica
            if not pdf_file.name.lower().endswith('.pdf'):
                messages.error(request, '❌ Por favor, envie apenas arquivos PDF.')
                return redirect('.')
            
            try:
                # Processa PDF
                result = PDFProcessor.process_pdf(pdf_file, pdf_file.name)
                
                # Verifica se já existe (por hash)
                if Note.objects.filter(source_hash=result['hash']).exists():
                    messages.warning(
                        request,
                        f'⚠️ Este PDF já foi importado anteriormente (hash: {result["hash"][:16]}...)'
                    )
                    return redirect('..')
                
                # Cria nova nota
                with transaction.atomic():
                    pdf_filename = f"{result['note_name'].replace(' ', '_')}_{result['year'] or 'SA'}.pdf"
                    
                    note = Note(
                        note_name=result['note_name'],
                        note_year=result['year'],
                        source_hash=result['hash'],
                        original_text=result['original_text'],
                        sanitized_text=result['anonymized_text'],
                        imported_by=request.user,
                        pdf_content=result['anonymized_pdf'],  # Salva binário no banco
                        pdf_filename=pdf_filename
                    )
                    
                    note.save()
                
                # Mensagem de sucesso
                terms_count = len(result['sensitive_terms'])
                messages.success(
                    request,
                    f'✅ PDF importado e anonimizado com sucesso!<br>'
                    f'<strong>Nota:</strong> {result["note_name"]}<br>'
                    f'<strong>Ano:</strong> {result["year"] or "Não identificado"}<br>'
                    f'<strong>Termos removidos:</strong> {terms_count}'
                )
                
                # Mostra detalhes dos termos encontrados
                if terms_count > 0:
                    categories_count = {}
                    for _, _, cat in result['sensitive_terms']:
                        categories_count[cat] = categories_count.get(cat, 0) + 1
                    
                    details = ', '.join([f'{count} {cat.upper()}' for cat, count in categories_count.items()])
                    messages.info(request, f'📊 Detalhes: {details}')
                
            except Note.DoesNotExist:
                pass  # Hash único, pode prosseguir
            except Exception as e:
                import traceback
                messages.error(
                    request,
                    f'❌ Erro ao processar PDF: {str(e)}<br>'
                    f'<pre>{traceback.format_exc()}</pre>'
                )
            
            return redirect('..')
        
        # Renderiza formulário de upload
        context = {
            'title': 'Importar Nota Técnica (PDF)',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/notes/import_pdf.html', context)
    
    def changelist_view(self, request, extra_context=None):
        """Adiciona botão de importação na lista"""
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context)
    
    def get_queryset(self, request):
        """Otimiza query"""
        qs = super().get_queryset(request)
        return qs.select_related('imported_by')
    
    actions = ['export_selected']
    
    def export_selected(self, request, queryset):
        """Exporta notas selecionadas"""
        # Implementar exportação posteriormente
        count = queryset.count()
        self.message_user(request, f'{count} nota(s) selecionada(s) para exportação.')
    export_selected.short_description = 'Exportar notas selecionadas'
