from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, View
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from apps.accounts.decorators import authenticated_required
from django.utils.decorators import method_decorator
from .models import PageContent, ContentCard
from .forms import PageContentForm, ContentCardForm


class HelpView(TemplateView):
    """View para exibir a página de ajuda e guia de uso."""
    template_name = 'pages/help.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Busca conteúdo editável do banco
        try:
            page_content = PageContent.objects.get(page_key='help')
            context['page_title'] = page_content.title
            context['page_content'] = page_content
        except PageContent.DoesNotExist:
            context['page_title'] = 'Central de Ajuda'
            context['page_content'] = None
        
        # Busca cards editáveis da página de ajuda
        context['content_cards'] = ContentCard.objects.filter(
            page='help',
            is_active=True
        ).order_by('order', 'created_at')
        
        return context


class ManualView(TemplateView):
    """View para exibir o Manual de Normas e Procedimentos."""
    template_name = 'pages/manual.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Busca conteúdo editável do banco
        try:
            page_content = PageContent.objects.get(page_key='manual')
            context['page_title'] = page_content.title
            context['page_content'] = page_content
        except PageContent.DoesNotExist:
            context['page_title'] = 'Manual DGP'
            context['page_content'] = None
        
        # Sincroniza capítulos hardcoded com ContentCards
        self.sync_manual_cards()
        
        # Busca cards do manual (capítulos)
        context['capitulos'] = ContentCard.objects.filter(
            page='manual',
            is_active=True
        ).order_by('order')
        
        # Verifica se está em modo de edição
        context['edit_mode'] = self.request.GET.get('edit') == '1'
        
        return context
    
    def sync_manual_cards(self):
        """Sincroniza capítulos hardcoded com ContentCards no banco"""
        capitulos_hardcoded = self.get_capitulos_hardcoded()
        
        for idx, cap in enumerate(capitulos_hardcoded, start=1):
            # Verifica se já existe o card
            card, created = ContentCard.objects.get_or_create(
                page='manual',
                order=idx,
                defaults={
                    'card_type': 'chapter',
                    'title': f"{cap['numero']}. {cap['titulo']}",
                    'content': f"<p><strong>{cap['descricao']}</strong></p>",
                    'is_active': True
                }
            )
    
    def get_capitulos_hardcoded(self):
        """Retorna lista de capítulos hardcoded do manual."""
        return [
            {"numero": "I", "titulo": "Abono de Permanência", "descricao": "Normas sobre abono de permanência para servidores"},
            {"numero": "II", "titulo": "Acumulação de Cargos", "descricao": "Regulamentação sobre acumulação de cargos públicos"},
            {"numero": "III", "titulo": "Adicional de Insalubridade", "descricao": "Critérios para concessão de adicional de insalubridade"},
            {"numero": "IV", "titulo": "Afastamento para Curso de Formação", "descricao": "Procedimentos para afastamento visando participação em cursos de formação"},
            {"numero": "V", "titulo": "Afastamento para Exercício de Mandato Eletivo", "descricao": "Normas sobre afastamento para mandato eletivo"},
            {"numero": "VI", "titulo": "Afastamento para Participar de Competição Desportiva", "descricao": "Regras para afastamento visando competições desportivas"},
            {"numero": "VII", "titulo": "Ajuda de Custo", "descricao": "Concessão de ajuda de custo para servidores"},
            {"numero": "VIII", "titulo": "Aproveitamento e Disponibilidade", "descricao": "Procedimentos de aproveitamento e colocação em disponibilidade"},
            {"numero": "IX", "titulo": "Auxílio Pré-Escolar", "descricao": "Normas sobre concessão de auxílio pré-escolar"},
            {"numero": "X", "titulo": "Auxílio-Alimentação", "descricao": "Regulamentação do auxílio-alimentação"},
            {"numero": "XI", "titulo": "Auxílio-Funeral", "descricao": "Concessão de auxílio-funeral"},
            {"numero": "XII", "titulo": "Auxílio-Moradia", "descricao": "Critérios para concessão de auxílio-moradia"},
            {"numero": "XIII", "titulo": "Auxílio-Natalidade", "descricao": "Concessão de auxílio-natalidade"},
            {"numero": "XIV", "titulo": "Auxílio-Transporte", "descricao": "Regulamentação do auxílio-transporte"},
            {"numero": "XV", "titulo": "Averbação de Tempo de Contribuição", "descricao": "Procedimentos para averbação de tempo de contribuição"},
            {"numero": "XVI", "titulo": "Certidão de Tempo de Contribuição", "descricao": "Emissão de certidão de tempo de contribuição"},
            {"numero": "XVII", "titulo": "Consignação em Folha de Pagamento", "descricao": "Normas sobre consignações em folha de pagamento"},
            {"numero": "XVIII", "titulo": "Contribuição para o Plano de Seguridade Social do Servidor", "descricao": "Regras de contribuição para seguridade social"},
            {"numero": "XIX", "titulo": "Direito de Pleitear", "descricao": "Normas sobre direito de pleitear do servidor"},
            {"numero": "XX", "titulo": "Exercício Provisório", "descricao": "Regulamentação do exercício provisório"},
            {"numero": "XXI", "titulo": "Férias", "descricao": "Normas sobre concessão e gozo de férias"},
            {"numero": "XXII", "titulo": "Gratificação Natalina", "descricao": "Regras para pagamento da gratificação natalina"},
            {"numero": "XXIII", "titulo": "Indenização de Transporte e Serviço Externo", "descricao": "Concessão de indenização de transporte para serviço externo"},
            {"numero": "XXIV", "titulo": "Licença à(ao) Adotante", "descricao": "Normas sobre licença para adotantes"},
            {"numero": "XXV", "titulo": "Licença Maternidade/Gestante", "descricao": "Concessão de licença maternidade e gestante"},
            {"numero": "XXVI", "titulo": "Licença para Acompanhamento de Cônjuge ou Companheiro(a)", "descricao": "Procedimentos para licença de acompanhamento conjugal"},
            {"numero": "XXVII", "titulo": "Licença para Atividade Política", "descricao": "Normas sobre licença para atividade política"},
            {"numero": "XXVIII", "titulo": "Licença para Desempenho de Mandato Classista", "descricao": "Regulamentação da licença para mandato classista"},
            {"numero": "XXIX", "titulo": "Licença para Tratamento de Saúde", "descricao": "Concessão de licença para tratamento de saúde"},
            {"numero": "XXX", "titulo": "Licença para Tratar de Interesses Particulares", "descricao": "Normas sobre licença para interesses particulares"},
            {"numero": "XXXI", "titulo": "Licença por Motivo de Doença em Pessoa da Família", "descricao": "Concessão de licença para cuidar de pessoa da família"},
            {"numero": "XXXII", "titulo": "Licença Prêmio Por Assiduidade", "descricao": "Critérios para concessão de licença prêmio"},
            {"numero": "XXXIII", "titulo": "Licença-Paternidade", "descricao": "Normas sobre licença-paternidade"},
            {"numero": "XXXIV", "titulo": "Nomeação, Exoneração, Desig. e Dispensa de Cargo ou Função: CCE e FCE", "descricao": "Procedimentos de nomeação, exoneração, designação e dispensa"},
            {"numero": "XXXV", "titulo": "Nomeação, Posse e Exercício em Cargo Público de Caráter Efetivo", "descricao": "Regulamentação de nomeação, posse e exercício em cargo efetivo"},
            {"numero": "XXXVI", "titulo": "Readaptação", "descricao": "Normas sobre readaptação de servidores"},
            {"numero": "XXXVII", "titulo": "Recondução", "descricao": "Procedimentos para recondução de servidores"},
            {"numero": "XXXVIII", "titulo": "Redistribuição", "descricao": "Regras para redistribuição de cargos"},
            {"numero": "XXXIX", "titulo": "Reintegração", "descricao": "Normas sobre reintegração de servidores"},
            {"numero": "XL", "titulo": "Remoção", "descricao": "Procedimentos para remoção de servidores"},
            {"numero": "XLI", "titulo": "Reversão", "descricao": "Regulamentação da reversão de aposentadoria"},
            {"numero": "XLII", "titulo": "Serviço Extraordinário", "descricao": "Normas sobre serviço extraordinário"},
            {"numero": "XLIII", "titulo": "Substituição", "descricao": "Regras para substituição de servidores"},
            {"numero": "XLIV", "titulo": "Vacância de Cargo Público de Provimento Efetivo", "descricao": "Procedimentos de vacância de cargo efetivo"},
            {"numero": "XLV", "titulo": "Cobrança Administrativa/Reposição ao Erário", "descricao": "Normas sobre cobrança administrativa e reposição ao erário"},
            {"numero": "XLVI", "titulo": "Cessão", "descricao": "Regulamentação de cessão de servidores"},
            {"numero": "XLVII", "titulo": "Requisição", "descricao": "Normas sobre requisição de servidores"},
        ]


# ========== VIEWS DE GERENCIAMENTO DE CARDS (APENAS ADMIN) ==========

@method_decorator(authenticated_required, name='dispatch')
class PageContentEditView(View):
    """View para editar conteúdo de páginas"""
    template_name = 'pages/content_edit.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se é ADMIN
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role != 'ADMIN':
            messages.error(request, 'Acesso restrito. Apenas ADMIN pode editar conteúdo.')
            return redirect('notes:search')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, page_key):
        """Exibe formulário de edição"""
        # Busca ou cria o conteúdo da página
        page_content, created = PageContent.objects.get_or_create(
            page_key=page_key,
            defaults={
                'title': self._get_default_title(page_key),
                'content': self._get_default_content(page_key)
            }
        )
        
        form = PageContentForm(instance=page_content)
        
        return render(request, self.template_name, {
            'form': form,
            'page_content': page_content,
            'page_key': page_key,
            'page_display': page_content.get_page_key_display()
        })
    
    def post(self, request, page_key):
        """Processa edição do conteúdo"""
        page_content = get_object_or_404(PageContent, page_key=page_key)
        form = PageContentForm(request.POST, instance=page_content)
        
        if form.is_valid():
            page_content = form.save(commit=False)
            page_content.updated_by = request.user
            page_content.updated_at = timezone.now()
            page_content.save()
            
            messages.success(request, f'Conteúdo da página "{page_content.get_page_key_display()}" atualizado com sucesso!')
            
            # Redireciona para a página apropriada
            if page_key == 'help':
                return redirect('core:help')
            elif page_key == 'manual':
                return redirect('core:manual')
            else:
                return redirect('notes:search')
        
        return render(request, self.template_name, {
            'form': form,
            'page_content': page_content,
            'page_key': page_key,
            'page_display': page_content.get_page_key_display()
        })
    
    def _get_default_title(self, page_key):
        """Retorna título padrão baseado na página"""
        defaults = {
            'help': 'Central de Ajuda',
            'manual': 'Manual de Normas e Procedimentos'
        }
        return defaults.get(page_key, 'Página')
    
    def _get_default_content(self, page_key):
        """Retorna conteúdo HTML padrão baseado na página"""
        if page_key == 'help':
            return '''<h2>Bem-vindo à Central de Ajuda</h2>
<p>Aqui você encontrará informações sobre como utilizar o sistema.</p>'''
        elif page_key == 'manual':
            return '''<h2>Manual de Normas e Procedimentos</h2>
<p>Documentação completa sobre normas e procedimentos do INSS.</p>'''
        return '<p>Conteúdo da página.</p>'


# ========== VIEWS DE GERENCIAMENTO DE CARDS (APENAS ADMIN) ==========

@method_decorator(authenticated_required, name='dispatch')
class CardCreateView(View):
    """View para criar novo card"""
    template_name = 'pages/card_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se é ADMIN ou ANALISTA
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role not in ['ADMIN', 'ANALISTA']:
            messages.error(request, 'Acesso restrito. Apenas ADMIN e ANALISTA podem gerenciar cards.')
            return redirect('notes:search')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, page):
        """Exibe formulário de criação"""
        initial_data = {'page': page}
        
        # Se for um card do manual, calcula a próxima ordem e número romano
        if page == 'manual':
            last_card = ContentCard.objects.filter(page='manual').order_by('-order').first()
            next_order = (last_card.order + 1) if last_card else 1
            next_roman = ContentCard.int_to_roman(next_order)
            
            initial_data['order'] = next_order
            initial_data['card_type'] = 'chapter'
            initial_data['title'] = f"{next_roman}. "
        
        form = ContentCardForm(initial=initial_data)
        
        return render(request, self.template_name, {
            'form': form,
            'page': page,
            'action': 'Criar',
            'is_new': True,
            'next_roman': ContentCard.get_next_manual_number() if page == 'manual' else None
        })
    
    def post(self, request, page):
        """Processa criação do card"""
        form = ContentCardForm(request.POST)
        
        if form.is_valid():
            card = form.save(commit=False)
            card.page = page
            card.created_by = request.user
            card.updated_by = request.user
            card.save()
            
            messages.success(request, f'Card "{card.title}" criado com sucesso!')
            
            if page == 'help':
                return redirect('core:help')
            else:
                return redirect('core:manual')
        
        return render(request, self.template_name, {
            'form': form,
            'page': page,
            'action': 'Criar',
            'is_new': True,
            'next_roman': ContentCard.get_next_manual_number() if page == 'manual' else None
        })


@method_decorator(authenticated_required, name='dispatch')
class CardEditView(View):
    """View para editar card existente"""
    template_name = 'pages/card_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se é ADMIN ou ANALISTA
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role not in ['ADMIN', 'ANALISTA']:
            messages.error(request, 'Acesso restrito. Apenas ADMIN e ANALISTA podem editar cards.')
            return redirect('notes:search')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        """Exibe formulário de edição inline"""
        card = get_object_or_404(ContentCard, pk=pk)
        form = ContentCardForm(instance=card)
        
        # Busca todos os cards do manual para exibir a página completa
        capitulos = ContentCard.objects.filter(
            page='manual',
            is_active=True
        ).order_by('order')
        
        return render(request, self.template_name, {
            'form': form,
            'card': card,
            'editing_card': card,
            'capitulos': capitulos,
            'edit_mode': True,
            'page_title': 'Manual DGP'
        })
    
    def post(self, request, pk):
        """Processa edição do card"""
        card = get_object_or_404(ContentCard, pk=pk)
        form = ContentCardForm(request.POST, instance=card)
        
        if form.is_valid():
            card = form.save(commit=False)
            card.updated_by = request.user
            card.save()
            
            messages.success(request, f'Card "{card.title}" atualizado com sucesso!')
            
            if card.page == 'help':
                return redirect('core:help')
            else:
                return HttpResponseRedirect(reverse('core:manual') + '?edit=1')
        
        return render(request, self.template_name, {
            'form': form,
            'card': card,
            'page': card.page,
            'action': 'Editar',
            'is_new': False
        })


@method_decorator(authenticated_required, name='dispatch')
class CardDeleteView(View):
    """View para deletar card"""
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se é ADMIN
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role != 'ADMIN':
            messages.error(request, 'Acesso restrito. Apenas ADMIN pode deletar cards.')
            return redirect('notes:search')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        """Deleta o card"""
        card = get_object_or_404(ContentCard, pk=pk)
        page = card.page
        title = card.title
        card.delete()
        
        messages.success(request, f'Card "{title}" deletado com sucesso!')
        
        if page == 'help':
            return redirect('core:help')
        else:
            return HttpResponseRedirect(reverse('core:manual') + '?edit=1')
