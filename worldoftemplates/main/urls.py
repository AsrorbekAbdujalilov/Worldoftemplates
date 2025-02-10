from django.urls import path
from .views import *

urlpatterns = [
  path('login/', LoginPage, name='Login'),
  path('register/',RegisterPage, name='Register'),
  path('logout/', Logout, name='Logout'),

  path('', Home, name='Home'),

  path('about/', Aboutus, name='About'),
]