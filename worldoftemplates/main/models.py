from django.db import models
from django.contrib.auth.models import *
import os
import logging
import subprocess
import fitz  # PyMuPDF
from django.db import models    
from django.conf import settings

# Configure logging
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
        """
        Override save method to process PPTX file and extract full slide images.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Save to get an ID
        if self.file and (is_new or 'file' in kwargs.get('update_fields', [])):
            logger.info(f"Processing PPTX for Product ID: {self.id}")
            try:
                self._extract_full_slide_images()
                logger.info(f"Successfully extracted full slide images for Product ID: {self.id}")
            except Exception as e:
                logger.error(f"Error processing PPTX for Product ID {self.id}: {str(e)}")
                raise  # Re-raise to handle in UI or logs

    def _extract_full_slide_images(self):
        """
        Convert PPTX to PDF and extract each slide as a PNG image.
        """
        # Define target folder: media/product_files/{product_id}/
        target_folder = os.path.join(settings.MEDIA_ROOT, 'product_files', str(self.id))
        os.makedirs(target_folder, exist_ok=True)

        # Move PPTX to target folder
        original_pptx_path = self.file.path
        pptx_filename = os.path.basename(self.file.name)
        new_pptx_path = os.path.join(target_folder, pptx_filename)

        if original_pptx_path != new_pptx_path:
            os.rename(original_pptx_path, new_pptx_path)
            self.file.name = os.path.join('product_files', str(self.id), pptx_filename)

        # Convert PPTX to PDF using LibreOffice
        pdf_path = new_pptx_path.replace('.pptx', '.pdf')
        convert_command = [
            LIBREOFFICE_PATH, "--headless", "--convert-to", "pdf", new_pptx_path, "--outdir", target_folder
        ]
        result = subprocess.run(convert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if not os.path.exists(pdf_path):
            logger.error(f"Failed to convert PPTX to PDF for Product ID: {self.id}. LibreOffice error: {result.stderr}")
            raise FileNotFoundError("PDF conversion failed.")

        # Convert all PDF pages to PNG images
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):  # Process all slides
            page = doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI for quality
            image_path = os.path.join(target_folder, f'slide{i+1}.png')
            pix.save(image_path)

        doc.close()
        logger.info(f"Extracted {len(doc)} slide images for Product ID: {self.id}")

        # Clean up PDF file
        try:
            os.remove(pdf_path)
        except PermissionError:
            logger.warning(f"Could not delete PDF at {pdf_path} due to permission error")

        # Update file field to reflect new PPTX location
        super().save(update_fields=['file'])

    def get_slide_urls(self):
        """
        Return a list of URLs for all slide images.
        """
        if not self.id:
            return []
        target_folder = os.path.join('product_files', str(self.id))
        media_path = os.path.join(settings.MEDIA_ROOT, target_folder)
        if not os.path.exists(media_path):
            return []
        slide_files = sorted([f for f in os.listdir(media_path) if f.startswith('slide') and f.endswith('.png')])
        return [os.path.join(settings.MEDIA_URL, target_folder, f).replace('\\', '/') for f in slide_files]

    def get_file_url(self):
        """
        Return the URL of the original PPTX file.
        """
        return os.path.join(settings.MEDIA_URL, self.file.name).replace('\\', '/') if self.file else ''