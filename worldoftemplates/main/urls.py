from django.urls import path
from django.conf.urls.static import static
from .views import *

from django.contrib.auth import views as auth_views

urlpatterns = [
  path('login/', LoginPage, name='Login'),
  path('register/',RegisterPage, name='Register'),
  path('logout/', Logout, name='Logout'),
  path('email_activation/', ActivationPage, name='Activation'),

  path('activate/<uidb64>/<token>/', Activate, name='activate'),

  path('', Home, name='Home'),
  path('related_products', relatedProduct, name='related'),
  path('product/<str:pk>/', Products, name='Product'),
  path('download/<str:filename>/', download_file, name='download'),

  path('profile/', Profile, name='profile'),
  path('about/', Aboutus, name='About'),
  path('contact/', ContactPage, name='Contact'),




  path('reset_password/', auth_views.PasswordResetView.as_view(), name="reset_password"),

  path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),

  path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

  path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
  
    











]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)