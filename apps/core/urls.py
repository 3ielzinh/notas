from django.urls import path
from .views import (
    HelpView, ManualView, CardCreateView, CardEditView, CardDeleteView
)

app_name = 'core'

urlpatterns = [
    path('help/', HelpView.as_view(), name='help'),
    path('manual/', ManualView.as_view(), name='manual'),
    path('card/<str:page>/create/', CardCreateView.as_view(), name='card_create'),
    path('card/<int:pk>/edit/', CardEditView.as_view(), name='card_edit'),
    path('card/<int:pk>/delete/', CardDeleteView.as_view(), name='card_delete'),
]
