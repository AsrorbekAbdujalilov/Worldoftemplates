from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django import forms

from .models import *

class CreateUserForm(UserCreationForm):
  class Meta:
    model = User
    fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    widgets = {
      'username': forms.TextInput(attrs={'placeholder': 'Enter username'}),
      'first_name': forms.TextInput(attrs={'placeholder': 'Enter first name'}),
      'last_name': forms.TextInput(attrs={'placeholder': 'Enter last name'}),
      'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
      'password1': forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
      'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
    }