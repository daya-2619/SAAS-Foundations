from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('kanban/', views.kanban_view, name='kanban'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('products/', views.products_view, name='products'),
    path('invoice/', views.invoice_view, name='invoice'),
    path('messages/', views.messages_view, name='messages'),
    path('docs/', views.docs_view, name='docs'),
    path('components/', views.components_view, name='components'),
    path('help/', views.help_view, name='help'),
]
