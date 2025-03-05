# main/views.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import *
from .tokens import Tokenis
from .decorators import *
from django.http import FileResponse
from django.shortcuts import get_object_or_404
import os
from .models import Product  # Import the Product model
import logging

logger = logging.getLogger(__name__)

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
    
    # Render HTML email template
    message = render_to_string("html/massege.html", {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': Tokenis.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http',
    })

    # Use EmailMultiAlternatives for sending HTML emails
    email = EmailMultiAlternatives(
        subject=mail_subject,
        body="Please verify your email by clicking the button below.",  # Plain text fallback
        to=[to_email]
    )
    email.attach_alternative(message, "text/html")  # Attach HTML version
    if email.send():
        messages.success(request, f'Dear {user.username}, We sent a VERIFICATION CODE to your email {to_email}. Please check your inbox.')
    else:
        messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')

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

    context = {'form': form}
    return render(request, 'html/register.html', context)

@authenticated
def ActivationPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        user = User.objects.filter(username=username, email=email).first()  # Fix filter syntax and use .first()

        if user:  # Ensure user exists
            to_email = user.email  # Access email directly
            Verification(request, user, to_email)  # Assuming Verification is defined elsewhere
        else:
            return render(request, 'html/verification.html', {'error': 'User not found'})
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

# main/views.py (excerpt)
# main/views.py (excerpt)
@login_required(login_url='Login')
def Products(request, pk):
    product = get_object_or_404(Product, id=pk)
    slide_urls = []  # List to store paths for all slides (up to 10)

    if product.file:
        # Get all slide images (up to 10)
        slide_urls = product.get_slide_urls()
        logger.info(f"Slide URLs for Product ID {pk}: {slide_urls}")  # Debug log

    context = {
        'product': product,
        "slide_urls": slide_urls  # Use slide_urls for thumbnails
    }
    return render(request, 'html/product.html', context)

def download_file(request, filename):
    product = get_object_or_404(Product, product_name=filename)
    file_path = product.file.path
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'  # Correct MIME type for PPTX
    response['Content-Disposition'] = f'attachment; filename="{product.product_name}.pptx"'
    return response

@login_required(login_url='Login')
def Profile(request):
    customer = request.user.customer
    form = ProfileInput(instance=customer)

    if request.method == 'POST':
        form = ProfileInput(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
    
    context = {'form': form, 'customer': customer}
    return render(request, 'html/profile.html', context)

@login_required(login_url='Login')
def Aboutus(request):
    context = {}
    return render(request, 'html/aboutus.html', context)

@login_required(login_url='Login')
def ContactPage(request):
    context = {}
    return render(request, 'html/contact.html', context)