from django.urls import path
from . import views

urlpatterns = [
    path('', views.optimizer_view, name='optimizer'),
]