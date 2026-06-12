from django.urls import path
from . import views

urlpatterns = [
    path('ingest/', views.ingest_logs_view, name='api_ingest_logs'),
]
