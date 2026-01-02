"""
Models para o app Notes - Gerenciamento de Notas Técnicas
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import hashlib
from datetime import datetime


class Note(models.Model):
    """Nota Técnica do INSS"""
    
    SITUACAO_CHOICES = [
        ('vigente', 'Vigente'),
        ('parcialmente_revogada', 'Parcialmente Revogada'),
        ('revogada', 'Revogada'),
        ('nao_classificada', 'Não Classificada'),
    ]
    
    note_name = models.CharField(
        max_length=500,
        verbose_name="Nome da Nota",
        db_index=True
    )
    
    note_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(2100)
        ],
        verbose_name="Ano",
        db_index=True
    )
    
    source_path = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name="Caminho Original"
    )
    
    pdf_content = models.BinaryField(
        null=True,
        blank=True,
        verbose_name="Conteúdo do PDF",
        help_text="PDF anonimizado armazenado no banco de dados"
    )
    
    pdf_filename = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Nome do Arquivo PDF"
    )
    
    source_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Hash SHA-256",
        db_index=True
    )
    
    original_text = models.TextField(
        verbose_name="Texto Original"
    )
    
    sanitized_text = models.TextField(
        verbose_name="Texto Anonimizado"
    )
    
    situacao = models.CharField(
        max_length=30,
        choices=SITUACAO_CHOICES,
        default='nao_classificada',
        verbose_name="Situação",
        db_index=True
    )
    
    justificativa = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observação/Justificativa"
    )
    
    imported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imported_notes',
        verbose_name="Importado por"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
        db_index=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    class Meta:
        db_table = 'notes'
        verbose_name = 'Nota Técnica'
        verbose_name_plural = 'Notas Técnicas'
        ordering = ['-note_year', 'note_name']
        indexes = [
            models.Index(fields=['note_year', 'note_name']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['source_hash']),
        ]
    
    def __str__(self):
        return f"{self.note_name} ({self.note_year or 'S/A'})"
    
    @property
    def display_name(self):
        """Nome para exibição"""
        if self.note_year:
            return f"{self.note_name} - {self.note_year}"
        return self.note_name
    
    @property
    def has_pdf(self):
        """Verifica se a nota tem PDF sem carregar o conteúdo"""
        return bool(self.pdf_filename)
    
    def save(self, *args, **kwargs):
        """Gera hash se necessário"""
        if not self.source_hash and self.original_text:
            self.source_hash = self.generate_hash(self.original_text)
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_hash(text: str) -> str:
        """
        Gera hash SHA-256 do texto para deduplicação.
        
        Args:
            text: Texto para gerar o hash
            
        Returns:
            Hash SHA-256 em hexadecimal
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @classmethod
    def check_duplicate(cls, text: str) -> bool:
        """
        Verifica se já existe nota com o mesmo conteúdo.
        
        Args:
            text: Texto original da nota
            
        Returns:
            True se duplicada, False caso contrário
        """
        hash_value = cls.generate_hash(text)
        return cls.objects.filter(source_hash=hash_value).exists()
    
    def get_word_count(self):
        """Retorna contagem de palavras do texto sanitizado"""
        return len(self.sanitized_text.split())
    
    def get_char_count(self):
        """Retorna contagem de caracteres do texto sanitizado"""
        return len(self.sanitized_text)
