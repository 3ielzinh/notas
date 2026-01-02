"""
Configuração do Django Admin para Terms
"""

from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.db import transaction
from .models import Term, TermCategory, IgnoredTerm
import openpyxl


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    """Admin para gerenciamento de Termos"""
    
    list_display = ['term', 'category', 'enabled', 'created_at', 'updated_at']
    list_filter = ['category', 'enabled', 'created_at']
    search_fields = ['term', 'norm_term']
    list_editable = ['enabled']
    readonly_fields = ['norm_term', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Termo', {
            'fields': ('category', 'term', 'enabled')
        }),
        ('Dados Automáticos', {
            'fields': ('norm_term', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def get_urls(self):
        """Adiciona URL customizada para importação"""
        urls = super().get_urls()
        custom_urls = [
            path('importar-planilha/', self.admin_site.admin_view(self.import_excel), name='terms_term_import'),
        ]
        return custom_urls + urls
    
    def import_excel(self, request):
        """View para importação de planilha Excel"""
        if request.method == 'POST' and request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']
            
            try:
                # Carrega a planilha
                wb = openpyxl.load_workbook(excel_file, read_only=True, data_only=True)
                ws = wb.active
                
                imported_count = 0
                batch_terms = []
                batch_size = 1000  # Processa em lotes de 1000
                existing_terms = set()  # Cache de termos existentes
                
                # Carrega termos existentes (category + norm_term)
                for term in Term.objects.all().values_list('category', 'norm_term'):
                    existing_terms.add(term)
                
                # Itera pelas linhas (pulando cabeçalho)
                for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    if not row or all(cell is None for cell in row):
                        continue
                    
                    matricula, nome, cpf = row[0], row[1], row[2]
                    
                    # Prepara SIAPE
                    if matricula:
                        matricula_str = str(matricula).strip()
                        if matricula_str and len(matricula_str) >= 2:
                            new_term = Term(term=matricula_str, category='siape')
                            norm = Term.normalize_text(matricula_str)
                            new_term.norm_term = norm
                            if ('siape', norm) not in existing_terms:
                                batch_terms.append(new_term)
                                existing_terms.add(('siape', norm))
                    
                    # Prepara nome
                    if nome:
                        nome_str = str(nome).strip()
                        if nome_str and len(nome_str) >= 2:
                            new_term = Term(term=nome_str, category='nome')
                            norm = Term.normalize_text(nome_str)
                            new_term.norm_term = norm
                            if ('nome', norm) not in existing_terms:
                                batch_terms.append(new_term)
                                existing_terms.add(('nome', norm))
                    
                    # Prepara CPF
                    if cpf:
                        cpf_str = str(cpf).strip()
                        cpf_clean = ''.join(filter(str.isdigit, cpf_str))
                        if cpf_clean and len(cpf_clean) >= 2:
                            new_term = Term(term=cpf_clean, category='cpf')
                            norm = Term.normalize_text(cpf_clean)
                            new_term.norm_term = norm
                            if ('cpf', norm) not in existing_terms:
                                batch_terms.append(new_term)
                                existing_terms.add(('cpf', norm))
                    
                    # Insere em lotes
                    if len(batch_terms) >= batch_size:
                        with transaction.atomic():
                            Term.objects.bulk_create(batch_terms, batch_size=batch_size)
                            imported_count += len(batch_terms)
                        batch_terms = []
                
                # Insere o restante
                if batch_terms:
                    with transaction.atomic():
                        Term.objects.bulk_create(batch_terms, batch_size=batch_size)
                        imported_count += len(batch_terms)
                
                wb.close()
                
                messages.success(
                    request,
                    f'✅ Importação concluída! {imported_count} termos novos importados.'
                )
                
            except Exception as e:
                import traceback
                messages.error(request, f'❌ Erro ao importar planilha: {str(e)}\n{traceback.format_exc()}')
            
            return redirect('..')
        
        # Renderiza formulário de upload
        context = {
            'title': 'Importar Termos de Anonimização',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/terms/import_excel.html', context)
    
    def changelist_view(self, request, extra_context=None):
        """Adiciona botão de importação na lista"""
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context)
    
    def get_queryset(self, request):
        """Otimiza query"""
        qs = super().get_queryset(request)
        return qs.select_related()
    
    actions = ['enable_terms', 'disable_terms']
    
    def enable_terms(self, request, queryset):
        """Ativa termos selecionados"""
        updated = queryset.update(enabled=True)
        self.message_user(request, f'{updated} termo(s) ativado(s) com sucesso.')
    enable_terms.short_description = 'Ativar termos selecionados'
    
    def disable_terms(self, request, queryset):
        """Desativa termos selecionados"""
        updated = queryset.update(enabled=False)
        self.message_user(request, f'{updated} termo(s) desativado(s) com sucesso.')
    disable_terms.short_description = 'Desativar termos selecionados'


@admin.register(IgnoredTerm)
class IgnoredTermAdmin(admin.ModelAdmin):
    """Admin para gerenciamento de Termos Ignorados"""
    
    list_display = ['term', 'reason', 'enabled', 'created_at']
    list_filter = ['enabled', 'created_at']
    search_fields = ['term', 'norm_term', 'reason']
    list_editable = ['enabled']
    readonly_fields = ['norm_term', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Termo a Ignorar', {
            'fields': ('term', 'reason', 'enabled')
        }),
        ('Dados Automáticos', {
            'fields': ('norm_term', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    actions = ['enable_ignored', 'disable_ignored']
    
    def enable_ignored(self, request, queryset):
        """Ativa termos ignorados selecionados"""
        updated = queryset.update(enabled=True)
        self.message_user(request, f'{updated} termo(s) ignorado(s) ativado(s) com sucesso.')
    enable_ignored.short_description = 'Ativar termos ignorados selecionados'
    
    def disable_ignored(self, request, queryset):
        """Desativa termos ignorados selecionados"""
        updated = queryset.update(enabled=False)
        self.message_user(request, f'{updated} termo(s) ignorado(s) desativado(s) com sucesso.')
    disable_ignored.short_description = 'Desativar termos ignorados selecionados'
