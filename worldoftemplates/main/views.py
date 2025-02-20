from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages

from django.contrib.auth.decorators import login_required

# Create your views here.

from .forms import *
from .tokens import Tokenis
from .decorators import *




def Activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and Tokenis.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated! You can now log in.")
        return redirect('Login')
    else:
        messages.error(request, "Activation link is invalid or expired.")
        return redirect('Home')


def Verification(request, user, to_email):

  mail_subject = 'CONFIRM YOUR EMAIL'
  message = render_to_string("html/massege.html", {
    'user': user.username,
    'domain': get_current_site(request).domain,
    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
    'token': Tokenis.make_token(user),
    'protocol': 'https' if request.is_secure() else 'http',
  })

  email = EmailMessage(mail_subject, message, to=[to_email])
  if email.send():
    messages.success(request, f'Dear {user.username}, We sent a VERIFICATION CODE to your email {to_email}. Please check your inbox.')
  else:
    messages.error(request, f'Problem sending email to {to_email}, check if you type correctly')

@authenticated
def RegisterPage(request):
  form = CreateUserForm()

  if request.method == 'POST':
    form = CreateUserForm(request.POST)
    if form.is_valid():
      if User.objects.filter(email=form.cleaned_data.get('email')).exists():
        messages.error(request, "Email is already in use. Please use a different email.")
      else:
        user = form.save(commit=False)
        user.is_active = False 
        user.save()
        Verification(request, user, form.cleaned_data.get('email'))
        return redirect('Activation')


  context = {'form':form}
  return render(request, 'html/register.html', context)

@authenticated
def ActivationPage(request):
  context = {}
  return render(request, 'html/verification.html', context)

@authenticated
def LoginPage(request):
  if request.method == 'POST':
    username = request.POST.get('username')
    password = request.POST.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
      login(request, user)
      return redirect('Home')
    else:
      messages.info(request, 'Username or Password is incorrect')

  context = {}
  return render(request, 'html/login.html', context)

def Logout(request):
  logout(request)
  return redirect('Login')

def Home(request):
  context = {}
  return render(request, 'html/home.html', context)

def Products(request, pk):
  presentations = Product.objects.filter(product_type='Animation')
  presentation = Product.objects.get(id=pk)

  context={'presentation':presentation, 'presentations':presentations}
  return render(request, 'html/product.html', context)

def Profile(request):
  customer = request.user.customer
  form = ProfileInput(instance=customer)

  if request.method == 'POST':
    form = ProfileInput(request.POST, request.FILES, instance=customer)
    if form.is_valid():
      form.save()
  
  context = {'form':form}
  return render(request, 'html/profile.html', context)

@login_required(login_url='Login')
def Aboutus(request):
  context = {}
  return render(request, 'html/aboutus.html', context)

@login_required(login_url='Login')
def ContactPage(request):
  context = {}
  return render(request, 'html/contact.html', context)
