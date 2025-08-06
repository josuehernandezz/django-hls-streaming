from django.urls import path
from . import views

urlpatterns = [
    path('', views.signin_view, name='signin'),
]
