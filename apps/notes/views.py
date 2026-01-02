"""
Views para o app Notes - Pesquisa e visualização de notas
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, View
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from apps.accounts.decorators import authenticated_required
from .models import Note
from .forms import NoteEditForm, NoteSearchForm
from apps.terms.models import Term
import re


@method_decorator(authenticated_required, name='dispatch')
class NoteSearchView(ListView):
    """View para pesquisa de notas técnicas"""
    model = Note
    template_name = 'notes/search.html'
    context_object_name = 'notes'
    paginate_by = 20
    
    def get_queryset(self):
        # Defer pdf_content para performance (campo grande), mas mantém pdf_filename
        queryset = Note.objects.defer('pdf_content')
        
        # Filtro de busca
        query = self.request.GET.get('q', '').strip()
        if query:
            # Tokeniza a query (remove palavras muito pequenas)
            terms = [t for t in re.findall(r'\w{2,}', query.lower()) if len(t) >= 2]
            
            # Busca em múltiplos campos
            q_filters = Q()
            for term in terms[:8]:  # Limita a 8 termos como no original
                q_filters &= (
                    Q(note_name__icontains=term) |
                    Q(sanitized_text__icontains=term) |
                    Q(original_text__icontains=term)
                )
            
            if q_filters:
                queryset = queryset.filter(q_filters)
        
        # Filtro de ano
        year = self.request.GET.get('year', '').strip()
        if year and year != 'Todas':
            try:
                year_int = int(year)
                queryset = queryset.filter(note_year=year_int)
            except ValueError:
                pass
        
        # Ordena por ano (descendente) e nome
        return queryset.order_by('-note_year', 'note_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Passa os parâmetros de busca para o template
        context['query'] = self.request.GET.get('q', '')
        context['selected_year'] = self.request.GET.get('year', 'Todas')
        
        # Lista de anos disponíveis
        years = Note.objects.values_list('note_year', flat=True).distinct().order_by('-note_year')
        context['available_years'] = ['Todas'] + [str(y) for y in years if y is not None]
        
        # Termos de busca para highlight
        query = context['query']
        if query:
            context['search_terms'] = [t for t in re.findall(r'\w{2,}', query.lower()) if len(t) >= 2]
        else:
            context['search_terms'] = []
        
        # Flag de busca submetida
        context['search_submitted'] = 'q' in self.request.GET or 'year' in self.request.GET
        
        return context


def analyst_or_admin_required(view_func):
    """Decorator para verificar se usuário é ANALISTA ou ADMIN"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar autenticado.')
            return redirect('accounts:login')
        
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role not in ['ANALISTA', 'ADMIN']:
            messages.error(request, 'Acesso restrito. Apenas ANALISTA ou ADMIN podem acessar esta página.')
            return redirect('notes:search')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


@method_decorator(authenticated_required, name='dispatch')
class NoteConfigListView(ListView):
    """View para listar notas para configuração"""
    model = Note
    template_name = 'notes/config_list.html'
    context_object_name = 'notes'
    paginate_by = 50
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica permissão
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role not in ['ANALISTA', 'ADMIN']:
            messages.error(request, 'Acesso restrito. Apenas ANALISTA ou ADMIN podem acessar esta página.')
            return redirect('notes:search')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Note.objects.all()
        
        # Filtro de busca
        query = self.request.GET.get('q', '').strip()
        if query:
            terms = [t for t in re.findall(r'\w{2,}', query.lower()) if len(t) >= 2]
            
            q_filters = Q()
            for term in terms[:8]:
                q_filters &= (
                    Q(note_name__icontains=term) |
                    Q(sanitized_text__icontains=term)
                )
            
            if q_filters:
                queryset = queryset.filter(q_filters)
        
        return queryset.order_by('-note_year', 'note_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['search_form'] = NoteSearchForm(initial={'query': context['query']})
        
        # Agrupa notas por ano
        notes_by_year = {}
        for note in context['notes']:
            year = note.note_year or 'Sem ano'
            if year not in notes_by_year:
                notes_by_year[year] = []
            notes_by_year[year].append(note)
        
        context['notes_by_year'] = dict(sorted(notes_by_year.items(), reverse=True))
        
        return context


@method_decorator(authenticated_required, name='dispatch')
class NoteEditView(View):
    """View para editar uma nota específica"""
    template_name = 'notes/config_edit.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica permissão
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role not in ['ANALISTA', 'ADMIN']:
            messages.error(request, 'Acesso restrito. Apenas ANALISTA ou ADMIN podem editar notas.')
            return redirect('notes:search')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        """Exibe formulário de edição"""
        note = get_object_or_404(Note, pk=pk)
        
        # Carrega valores do banco
        form = NoteEditForm(instance=note)
        
        return render(request, self.template_name, {
            'form': form,
            'note': note,
            'query': request.GET.get('q', '')
        })
    
    def post(self, request, pk):
        """Processa edição da nota"""
        note = get_object_or_404(Note, pk=pk)
        form = NoteEditForm(request.POST, instance=note)
        
        if form.is_valid():
            # Salva a nota com todos os campos (incluindo situacao e justificativa)
            note = form.save(commit=False)
            note.updated_at = timezone.now()
            note.save()
            
            messages.success(request, f'Nota "{note.note_name}" atualizada com sucesso!')
            
            # Volta para a lista com a busca preservada
            query = request.GET.get('q', '')
            if query:
                return redirect(f"{reverse('notes:config_list')}?q={query}")
            return redirect('notes:config_list')
        
        return render(request, self.template_name, {
            'form': form,
            'note': note,
            'query': request.GET.get('q', '')
        })


@authenticated_required
def view_pdf(request, note_id):
    """View para visualizar PDF inline (sem download)"""
    note = get_object_or_404(Note, pk=note_id)
    
    if not note.pdf_content:
        messages.error(request, 'PDF não disponível para esta nota.')
        return redirect('notes:search')
    
    # Retorna PDF para visualização inline
    response = HttpResponse(bytes(note.pdf_content), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{note.pdf_filename or "nota.pdf"}"'
    
    return response


@authenticated_required
def download_pdf(request, note_id):
    """View para download do PDF anonimizado"""
    note = get_object_or_404(Note, pk=note_id)
    
    if not note.pdf_content:
        messages.error(request, 'PDF não disponível para esta nota.')
        return redirect('notes:search')
    
    # Retorna PDF como download
    response = HttpResponse(bytes(note.pdf_content), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{note.pdf_filename or "nota.pdf"}"'
    
    return response
