"""
Models para o app Accounts - Autenticação e Perfis de Usuário
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Role(models.TextChoices):
    """Níveis de acesso do sistema"""
    VISUALIZAR = 'VISUALIZAR', 'Visualizar'
    ANALISTA = 'ANALISTA', 'Analista'
    ADMIN = 'ADMIN', 'Administrador'


class UserProfile(models.Model):
    """Perfil estendido do usuário com controle de acesso"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Usuário"
    )
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VISUALIZAR,
        verbose_name="Perfil de Acesso"
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
        db_table = 'user_profiles'
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    @property
    def can_view_notes(self):
        """Pode visualizar notas (todos os perfis)"""
        return True
    
    @property
    def can_edit_notes(self):
        """Pode editar configurações de notas"""
        return self.role in [Role.ANALISTA, Role.ADMIN]
    
    @property
    def can_manage_terms(self):
        """Pode gerenciar termos"""
        return self.role == Role.ADMIN
    
    @property
    def can_import_notes(self):
        """Pode importar notas"""
        return self.role in [Role.ANALISTA, Role.ADMIN]
    
    @property
    def can_delete_notes(self):
        """Pode excluir notas"""
        return self.role == Role.ADMIN
    
    @property
    def is_admin(self):
        """Verifica se é administrador"""
        return self.role == Role.ADMIN


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria perfil automaticamente ao criar usuário"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva perfil ao salvar usuário"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
