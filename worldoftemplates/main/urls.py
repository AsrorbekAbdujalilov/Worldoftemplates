from django.urls import path
from .views import *

urlpatterns = [
  path('login/', LoginPage, name='Login'),
  path('register/',RegisterPage, name='Register'),
  path('logout/', Logout, name='Logout'),
  path('email_activation/', ActivationPage, name='Activation'),

  path('activate/<uidb64>/<token>/', Activate, name='activate'),

  path('', Home, name='Home'),

  path('about/', Aboutus, name='About'),
  path('contact/', ContactPage, name='Contact'),

]