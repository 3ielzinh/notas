"""
Models para o app Core - Conteúdos editáveis do sistema
"""

from django.db import models
from django.contrib.auth.models import User


class ContentCard(models.Model):
    """Card de conteúdo editável (FAQ, guia, capítulo do manual, etc)"""
    
    PAGE_CHOICES = [
        ('help', 'Ajuda'),
        ('manual', 'Manual'),
    ]
    
    CARD_TYPE_CHOICES = [
        ('faq', 'Pergunta Frequente'),
        ('guide', 'Guia'),
        ('chapter', 'Capítulo do Manual'),
        ('info', 'Informação'),
    ]
    
    page = models.CharField(
        max_length=50,
        choices=PAGE_CHOICES,
        verbose_name="Página",
        db_index=True
    )
    
    card_type = models.CharField(
        max_length=50,
        choices=CARD_TYPE_CHOICES,
        verbose_name="Tipo de Card"
    )
    
    title = models.CharField(
        max_length=300,
        verbose_name="Título"
    )
    
    content = models.TextField(
        verbose_name="Conteúdo",
        help_text="Conteúdo em HTML ou texto simples"
    )
    
    link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Link",
        help_text="URL opcional para link externo ou recurso"
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição (menor aparece primeiro)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cards',
        verbose_name="Criado por"
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_cards',
        verbose_name="Atualizado por"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última atualização"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    class Meta:
        db_table = 'content_cards'
        verbose_name = 'Card de Conteúdo'
        verbose_name_plural = 'Cards de Conteúdo'
        ordering = ['page', 'order', 'created_at']
        indexes = [
            models.Index(fields=['page', 'is_active', 'order']),
        ]
    
    def __str__(self):
        return f"{self.get_page_display()} - {self.title}"
    
    @staticmethod
    def int_to_roman(num):
        """Converte número inteiro para algarismo romano"""
        val = [
            1000, 900, 500, 400,
            100, 90, 50, 40,
            10, 9, 5, 4,
            1
        ]
        syms = [
            "M", "CM", "D", "CD",
            "C", "XC", "L", "XL",
            "X", "IX", "V", "IV",
            "I"
        ]
        roman_num = ''
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syms[i]
                num -= val[i]
            i += 1
        return roman_num
    
    @classmethod
    def get_next_manual_number(cls):
        """Retorna o próximo número romano disponível para cards do manual"""
        last_card = cls.objects.filter(page='manual', card_type='chapter').order_by('-order').first()
        if last_card:
            next_num = last_card.order + 1
        else:
            next_num = 1
        return cls.int_to_roman(next_num)


class PageContent(models.Model):
    """Conteúdo editável de páginas do sistema"""
    
    PAGE_CHOICES = [
        ('help', 'Ajuda'),
        ('manual', 'Manual'),
    ]
    
    page_key = models.CharField(
        max_length=50,
        unique=True,
        choices=PAGE_CHOICES,
        verbose_name="Página"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Título"
    )
    
    content = models.TextField(
        verbose_name="Conteúdo",
        help_text="Conteúdo em HTML. Use tags como <h2>, <p>, <ul>, <li>, etc."
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_pages',
        verbose_name="Atualizado por"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última atualização"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    class Meta:
        db_table = 'page_contents'
        verbose_name = 'Conteúdo de Página'
        verbose_name_plural = 'Conteúdos de Páginas'
        ordering = ['page_key']
    
    def __str__(self):
        return f"{self.get_page_key_display()}"
