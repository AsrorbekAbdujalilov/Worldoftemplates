from django.db import models
from django.contrib.auth.models import *
import os
from django.db import models

from .extract import convert_pptx_to_jpeg

# Customer Model
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    first_name = models.CharField(max_length=200, null=True, blank=True)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, unique=True, blank=True)
    image = models.ImageField(default='profile/profile_pic.png',upload_to='profile/',null=True, blank=True)

    def __str__(self):
        return self.username if self.username else "Unnamed Customer"

# Tag Model
class Tag(models.Model):
    tag_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.tag_name

# Product Model
class Product(models.Model):
    CATEGORIES = {
        ('Office 2013','Office 2013'),
        ('Office 2016','Office 2016'),
        ('Office 2019','Office 2019'),
        ('Office 2021','Office 2021'),
    }
    product_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='product_files', null=True, blank=True)
    office_created = models.CharField(max_length=200, null=True, blank=True, choices=CATEGORIES)
    morph = models.BooleanField(null=True, blank=True)
    product_type = models.ManyToManyField(Tag, blank=True)
    size = models.FloatField(null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name if self.product_name else "Unnamed Product"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the file first
        self.convert_pptx_to_jpeg()
