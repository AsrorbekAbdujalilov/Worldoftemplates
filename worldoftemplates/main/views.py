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

#[Errno 11001] getaddrinfo failed
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
    types = Tag.objects.all()

    tag_products = []

    for typ in types:
        products = Product.objects.filter(product_type=typ).order_by('-date_created')[:3]
        tag_products.append({'typ': typ, 'products': products})

        for product in products:
            if product.file:
                pptx_url = product.file.url
                image_folder = pptx_url.replace(f'{product.file.name.split('/')[-1]}','')
                product.image_preview = f'{image_folder}slide1.jpg'  # Ensure this path is valid

    context = {'types':types, 'tag_products':tag_products}
    return render(request, 'html/home.html', context)

@login_required(login_url='Login')
def ProductType(request, type):
    types = Tag.objects.all()
    product_type = get_object_or_404(Tag, tag_name=type)
    relateds = Product.objects.filter(product_type=product_type)

    for related in relateds:
        if related.file:
            pptx_url = related.file.url
            image_folder = pptx_url.replace(f'{related.file.name.split('/')[-1]}','')
            related.image_preview = f'{image_folder}slide1.jpg'  # Ensure this path is valid

    context = {'relateds':relateds, 'types':types}
    return render(request, 'html/ProductType.html', context)

@login_required(login_url='Login')
def searchrelatedProduct(request):
    if request.method == "GET":
        search_term = request.GET.get('search', '')

        # Get related products
        relateds = Product.objects.all()  # Adjust filter logic if necessary
        types = Tag.objects.all()

        if search_term:
            relateds = relateds.filter(product_name__icontains=search_term) or relateds.filter(description__icontains=search_term) or relateds.filter(office_created__icontains=search_term) or relateds.filter(product_type__tag_name__icontains=search_term)
        else:  
            relateds = Product.objects.none()

        for related in relateds:
            if related.file:
                pptx_url = related.file.url
                image_folder = pptx_url.replace(f'{related.file.name.split('/')[-1]}','')
                related.image_preview = f'{image_folder}slide1.jpg'  # Ensure this path is valid

        context = {'relateds': relateds, 'types':types}
        return render(request, 'html/relatedProduct.html', context)
    else:
        redirect('/')

@login_required(login_url='Login')
def Products(request, pk):
    product = get_object_or_404(Product, id=pk)
    relateds = Product.objects.filter(product_type__in=product.product_type.all()).exclude(product_name=product)
    types = Tag.objects.all()
    slide_urls = []

    for related in relateds:
        if related.file:
            pptx_url = related.file.url
            image_folder = pptx_url.replace(f'{related.file.name.split('/')[-1]}','')            
            related.image_preview = f'{image_folder}slide1.jpg'  # Ensure this path is valid
    
    if product.file:
        # Get the folder where images are stored
        pptx_folder = os.path.dirname(product.file.name)
        slides_folder = os.path.join(settings.MEDIA_URL, pptx_folder)

        # Dynamically check how many slides exist
        for i in range(1, 6):  # Maximum 10 slides
            image_path = os.path.join(settings.MEDIA_ROOT, pptx_folder, f"slide{i}.jpg")
            if os.path.exists(image_path):
                slide_urls.append(f"{slides_folder}/slide{i}.jpg")
            else:
                break  # Stop when no more slides are found

    context = {'product': product, 'slide_urls': slide_urls, 'relateds':relateds, 'types':types}
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
    types = Tag.objects.all()
    form = ProfileInput(instance=customer)

    if request.method == 'POST':
        form = ProfileInput(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
    
    context = {'form': form, 'customer': customer, 'types':types}
    return render(request, 'html/profile.html', context)

@login_required(login_url='Login')
def Aboutus(request):
    types = Tag.objects.all()
    context = {'types':types}
    return render(request, 'html/aboutus.html', context)

@login_required(login_url='Login')
def ContactPage(request):
    types = Tag.objects.all()
    context = {'types':types}
    return render(request, 'html/contact.html', context)

def custom_404_handler(request, exception):
    return render(request, 'html/404.html', status=404)