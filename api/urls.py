from django.urls import path
from .views import dashboard, register, setup_company

urlpatterns = [
    path('register/', register),
    path('dashboard/', dashboard),
    path('setup-company/', setup_company),
]