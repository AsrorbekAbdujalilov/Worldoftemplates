from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

# Create your views here.

from .forms import *

def RegisterPage(request):
  form = CreateUserForm()

  if request.method == 'POST':
    form = CreateUserForm(request.POST)
    if form.is_valid():
      form.save()
      username = form.cleaned_data.get('username')

      messages.success(request, 'Hi,' + username)
      return redirect('Login')

  context = {'form':form}
  return render(request, 'html/register.html', context)

def LoginPage(request):
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

def Home(request):
  return HttpResponse('home')