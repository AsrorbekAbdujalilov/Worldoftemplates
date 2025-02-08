from django.db import models
from django.contrib.auth.models import *

# Customer Model
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    username = models.CharField(max_length=200, null=True)
    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)
    email = models.EmailField(null=True, unique=True)
    password = models.CharField(max_length=100, null=True)
    new_column = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.username if self.username else "Unnamed Customer"

# Product Model
class Product(models.Model):
    product_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to="product_files/", null=True, blank=True)
    office_created = models.BigIntegerField(null=True, blank=True)
    morph = models.BigIntegerField(null=True, blank=True)
    product_type = models.BigIntegerField(null=True, blank=True)
    size = models.BigIntegerField(null=True, blank=True)
    cost = models.BigIntegerField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name if self.product_name else "Unnamed Product"

# Order Model
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date_ordered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.customer.username}"

# Tag Model
class Tag(models.Model):
    tag_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.tag_name
