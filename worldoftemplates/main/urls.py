from django.urls import path
from django.conf.urls.static import static
from .views import *

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

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)