from django.db import models
from django.contrib.auth.models import *
import os
import uuid
import subprocess
from django.shortcuts import render
from django.conf import settings
import pymupdf as fitz  # PyMuPDF


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


class Product(models.Model):
    CATEGORIES = {
        ('Office 2013', 'Office 2013'),
        ('Office 2016', 'Office 2016'),
        ('Office 2019', 'Office 2019'),
        ('Office 2021', 'Office 2021'),
        ('Office 2024', 'Office 2024'),
        ('Office 365', 'Office 365'),
    }
    product_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='uploads' ,null=True, blank=True)
    office_created = models.CharField(max_length=200, null=True, blank=True, choices=CATEGORIES)
    morph = models.BooleanField(null=True, blank=True)
    premium = models.BooleanField(null=True, blank=True)
    favorite = models.BooleanField(null=True, blank=True)
    product_type = models.ManyToManyField(Tag, blank=True)
    size = models.FloatField(null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name if self.product_name else "Unnamed Product"

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if this is a new file
        super().save(*args, **kwargs)  # Save first to get the file path    

        if is_new and self.file:
            unique_id = str(uuid.uuid4())  # Generate a unique folder ID
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', unique_id)
            os.makedirs(upload_dir, exist_ok=True)  # ✅ Create the folder first    

            pptx_path = os.path.join(upload_dir, os.path.basename(self.file.name))  
            # Move file to UUID folder 
            with open(pptx_path, 'wb+') as f:
                for chunk in self.file.chunks():
                    f.write(chunk)

            for ext in ('.pptx', '.pptm', '.ppt'):
                if pptx_path.lower().endswith(ext):
                    pdf_path = pptx_path[: -len(ext)] + '.pdf'
                    break

            # ✅ Convert PPTX to PDF using LibreOffice
            convert_command = [
                LIBREOFFICE_PATH, "--headless", "--convert-to", "pdf:writer_pdf_Export", pptx_path, "--outdir", upload_dir
            ]
            subprocess.run(convert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # ✅ Check if an extra PDF was created outside the folder
            original_pdf_path = os.path.splitext(pptx_path)[0] + ".pdf"  # Where LibreOffice might save it
            pdf_path = os.path.join(upload_dir, os.path.basename(original_pdf_path))  # Correct location

            # ✅ If the extra PDF exists outside, delete it
            if original_pdf_path != pdf_path and os.path.exists(original_pdf_path):
                os.remove(original_pdf_path)  #

            doc = fitz.open(pdf_path)
            image_paths = []
            num_pages = min(5, len(doc))  # Limit to first 10 slides
            for i in range(num_pages):
                page = doc[i]
                pix = page.get_pixmap()
                image_path = os.path.join(upload_dir, f'slide{i+1}.jpg')
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(image_path, format="JPEG")  # Save as JPEG

                image_paths.append(os.path.join('uploads', unique_id, f'slide{i+1}.png'))

            doc.close()

            # ✅ Update file path to the new UUID-based location
            self.file.name = f'uploads/{unique_id}/{self.file.name.split('/')[-1]}'
            try:
                os.remove(pdf_path)
            except PermissionError:
                pass  # If file is locked, don't crash
            super().save(update_fields=['file'])  # Save the new file path in the database
