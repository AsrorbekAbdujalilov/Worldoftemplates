from django.urls import path
from .views import *

urlpatterns = [
  path('login/', LoginPage, name='Login'),
  path('register/',RegisterPage, name='Register'),
  path('', Home, name='Home')
]