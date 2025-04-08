from django.db import models
from django.contrib.auth.models import User
import os
import uuid
import subprocess
from django.conf import settings
import pymupdf as fitz  # PyMuPDF
from PIL import Image
import logging
from django.core.exceptions import ValidationError

# Set up logging
logger = logging.getLogger(__name__)

# Path to LibreOffice executable (adjust if necessary)
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"

# Customer Model
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    first_name = models.CharField(max_length=200, null=True, blank=True)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, unique=True, blank=True)
    image = models.ImageField(default='profile/profile_pic.png', upload_to='profile/', null=True, blank=True)

    def __str__(self):
        return self.username if self.username else "Unnamed Customer"

# Tag Model
class Tag(models.Model):
    tag_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.tag_name

# Product Model
class Product(models.Model):
    CATEGORIES = [
        'Office 2013',
        'Office 2016',
        'Office 2019',
        'Office 2021',
        'Office 2024',
        'Office 365',
    ]
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    )

    product_name = models.CharField(max_length=200)  # Now required
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='uploads')  # Now required
    office_created = models.CharField(max_length=200, choices=[(cat, cat) for cat in CATEGORIES], null=True, blank=True)
    morph = models.BooleanField(default=False)  # Added default
    premium = models.BooleanField(default=False)  # Added default
    favorite = models.BooleanField(default=False)  # Added default
    product_type = models.ManyToManyField(Tag, blank=True)
    size = models.FloatField(null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    slide_images = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('active', 'Active')], default='pending')

    def __str__(self):
        return self.product_name if self.product_name else "Unnamed Product"

    def save(self, *args, **kwargs):
        # Check if this is a new instance (i.e., being created, not updated)
        is_new = self.pk is None
        # Store the uploaded file temporarily without saving it to the default location yet
        uploaded_file = None
        if self.file and is_new:
            uploaded_file = self.file
            # Temporarily clear the file field to prevent Django from saving it to media/uploads/
            self.file = None
        # Save the instance to the database (without the file for now if it's a new instance)
        super().save(*args, **kwargs)
        # Process the file only if this is a new instance and a file was uploaded
        if is_new and uploaded_file:
            try:
                # Generate a unique folder ID for storing the file and its derivatives
                unique_id = str(uuid.uuid4())
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', unique_id)
                os.makedirs(upload_dir, exist_ok=True)  # Create the folder if it doesn't exist
                # Save the file directly to the UUID-based directory
                pptx_path = os.path.join(upload_dir, uploaded_file.name)
                with open(pptx_path, 'wb+') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                # Calculate file size in MB
                self.size = uploaded_file.size / (1024 * 1024)  # Convert bytes to MB
                # Determine the PDF path based on the file extension
                for ext in ('.pptx', '.pptm', '.ppt'):
                    if pptx_path.lower().endswith(ext):
                        pdf_path = os.path.splitext(pptx_path)[0] + '.pdf'
                        break
                else:
                    # If the file is not a PPTX/PPTM/PPT, skip conversion and mark as processed
                    self.status = 'processed'
                    self.file.name = f'uploads/{unique_id}/{uploaded_file.name}'
                    super().save(update_fields=['file', 'status', 'size'])
                    return
                # Convert PPTX to PDF using LibreOffice
                convert_command = [
                    LIBREOFFICE_PATH,  # Use the defined path or override with settings if available
                    "--headless",
                    "--convert-to",
                    "pdf:writer_pdf_Export",
                    pptx_path,
                    "--outdir",
                    upload_dir
                ]
                # Run the conversion command and capture output
                result = subprocess.run(
                    convert_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                # Check if the conversion was successful
                if result.returncode != 0:
                    error_message = f"LibreOffice conversion failed: {result.stderr}"
                    logger.error(error_message)
                    self.status = 'failed'
                    self.error_message = error_message
                    super().save(update_fields=['status', 'error_message'])
                    raise ValidationError(error_message)
                # Verify that the PDF exists before proceeding
                if not os.path.exists(pdf_path):
                    error_message = f"PDF file not found after conversion: {pdf_path}"
                    logger.error(error_message)
                    self.status = 'failed'
                    self.error_message = error_message
                    super().save(update_fields=['status', 'error_message'])
                    raise ValidationError(error_message)
                # Open the PDF and convert the first 5 slides to images
                doc = fitz.open(pdf_path)
                image_paths = []
                num_pages = min(5, len(doc))  # Limit to first 5 slides
                for i in range(num_pages):
                    page = doc[i]
                    pix = page.get_pixmap()
                    image_path = os.path.join(upload_dir, f'slide{i+1}.jpg')
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img.save(image_path, format="JPEG")  # Save as JPEG
                    # Store the relative path to the image
                    image_paths.append(os.path.join('uploads', unique_id, f'slide{i+1}.jpg'))
                doc.close()
                # Update the file path to the new UUID-based location
                self.file.name = f'uploads/{unique_id}/{uploaded_file.name}'
                # Store the slide image paths
                self.slide_images = image_paths
                # Mark the product as processed
                self.status = 'processed'
                self.error_message = None  # Clear any previous error message
                # Clean up the temporary PDF file
                try:
                    os.remove(pdf_path)
                except PermissionError:
                    logger.warning(f"Could not delete temporary PDF file: {pdf_path}")
                # Save the updated file path, slide images, and status
                super().save(update_fields=['file', 'slide_images', 'status', 'error_message', 'size'])
            except Exception as e:
                # Log the error and update the status
                error_message = f"Error processing product file {uploaded_file.name}: {str(e)}"
                logger.error(error_message)
                self.status = 'failed'
                self.error_message = error_message
                super().save(update_fields=['status', 'error_message'])
                raise ValidationError(error_message)