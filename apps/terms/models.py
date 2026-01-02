"""
Models para o app Terms - Gerenciamento de Termos de Anonimização
"""

from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone
import unicodedata
import re


class TermCategory(models.TextChoices):
    """Categorias pré-definidas de termos"""
    SIAPE = 'siape', 'SIAPE'
    NOME = 'nome', 'Nome'
    CPF = 'cpf', 'CPF'
    ENDERECO = 'endereco', 'Endereço'
    TELEFONE = 'telefone', 'Telefone'
    EMAIL = 'email', 'E-mail'
    RG = 'rg', 'RG'
    CNPJ = 'cnpj', 'CNPJ'
    OUTRO = 'outro', 'Outro'


class Term(models.Model):
    """Termo para anonimização de dados sensíveis"""
    
    category = models.CharField(
        max_length=50,
        choices=TermCategory.choices,
        default=TermCategory.OUTRO,
        verbose_name="Categoria",
        db_index=True
    )
    
    term = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(2)],
        verbose_name="Termo"
    )
    
    norm_term = models.CharField(
        max_length=255,
        verbose_name="Termo Normalizado",
        editable=False,
        db_index=True
    )
    
    enabled = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        db_index=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    class Meta:
        db_table = 'terms'
        verbose_name = 'Termo'
        verbose_name_plural = 'Termos'
        unique_together = [['category', 'norm_term']]
        ordering = ['category', 'term']
        indexes = [
            models.Index(fields=['category', 'enabled']),
            models.Index(fields=['norm_term']),
        ]
    
    def __str__(self):
        return f"{self.get_category_display()}: {self.term}"
    
    def save(self, *args, **kwargs):
        """Normaliza o termo antes de salvar"""
        self.norm_term = self.normalize_text(self.term)
        super().save(*args, **kwargs)
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalização de texto para comparação.
        Remove acentos, converte para minúsculas, normaliza espaços.
        
        Args:
            text: Texto a ser normalizado
            
        Returns:
            Texto normalizado
        """
        text = text.strip().lower()
        # Remove acentos
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        # Normaliza espaços e hífens
        text = text.replace('-', ' ').replace('_', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @classmethod
    def get_active_terms_by_category(cls, categories=None):
        """
        Retorna dicionário de termos ativos agrupados por categoria.
        
        Args:
            categories: Lista de categorias para filtrar (opcional)
            
        Returns:
            Dict[str, List[str]]: Dicionário {categoria: [lista de termos]}
        """
        queryset = cls.objects.filter(enabled=True)
        
        if categories:
            queryset = queryset.filter(category__in=categories)
        
        result = {}
        for term in queryset.order_by('category', 'term'):
            if term.category not in result:
                result[term.category] = []
            result[term.category].append(term.term)
        
        return result


class IgnoredTerm(models.Model):
    """Termos que devem ser ignorados na anonimização (ex: assinaturas, cargos)"""
    
    term = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(2)],
        verbose_name="Termo a Ignorar"
    )
    
    norm_term = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Termo Normalizado",
        editable=False,
        db_index=True
    )
    
    reason = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Motivo",
        help_text="Por que este termo deve ser ignorado? Ex: Nome de autoridade, cargo, etc."
    )
    
    enabled = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        db_index=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    class Meta:
        db_table = 'ignored_terms'
        verbose_name = 'Termo Ignorado'
        verbose_name_plural = 'Termos Ignorados'
        ordering = ['term']
        indexes = [
            models.Index(fields=['norm_term']),
            models.Index(fields=['enabled']),
        ]
    
    def __str__(self):
        return f"{self.term} ({self.reason or 'Sem motivo'})"
    
    def save(self, *args, **kwargs):
        """Normaliza o termo antes de salvar"""
        self.norm_term = Term.normalize_text(self.term)
        super().save(*args, **kwargs)
    
    @classmethod
    def is_ignored(cls, text: str) -> bool:
        """
        Verifica se um texto deve ser ignorado.
        
        Args:
            text: Texto a verificar
            
        Returns:
            True se deve ser ignorado, False caso contrário
        """
        norm_text = Term.normalize_text(text)
        return cls.objects.filter(norm_term=norm_text, enabled=True).exists()
    
    @classmethod
    def get_ignored_set(cls) -> set:
        """
        Retorna set de termos normalizados que devem ser ignorados.
        
        Returns:
            Set de strings normalizadas
        """
        return set(
            cls.objects.filter(enabled=True).values_list('norm_term', flat=True)
        )
