"""
URLs para o app Notes
"""
from django.urls import path
from .views import NoteSearchView, NoteConfigListView, NoteEditView, view_pdf, download_pdf

app_name = 'notes'

urlpatterns = [
    path('search/', NoteSearchView.as_view(), name='search'),
    path('config/', NoteConfigListView.as_view(), name='config_list'),
    path('config/<int:pk>/edit/', NoteEditView.as_view(), name='config_edit'),
    path('<int:note_id>/view-pdf/', view_pdf, name='view_pdf'),
    path('<int:note_id>/download-pdf/', download_pdf, name='download_pdf'),
]
