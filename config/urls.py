"""
URLs principais do projeto
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/notes/search/', permanent=False), name='home'),
    path('accounts/', include('apps.accounts.urls')),
    path('notes/', include('apps.notes.urls')),
    path('', include('apps.core.urls')),
]
