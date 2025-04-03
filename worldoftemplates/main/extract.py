
'''
import os
import uuid
import subprocess
from django.shortcuts import render
from django.conf import settings

LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"

def convert_pptx_to_jpeg(self):
    if not self.file:
        return None  # No file uploaded

    # Generate unique folder for this upload
    unique_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'product_files', unique_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Get the PPTX file path
    pptx_path = self.file.path  # Use the actual saved file path
    pdf_path = os.path.splitext(pptx_path)[0] + ".pdf"

    # Convert PPTX to PDF using LibreOffice
    convert_command = [
        LIBREOFFICE_PATH, "--headless", "--convert-to", "pdf:writer_pdf_Export",
        pptx_path, "--outdir", upload_dir
    ]
    subprocess.run(convert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Convert FIRST 10 PDF pages to images using PyMuPDF
    doc = fitz.open(pdf_path)
    image_paths = []
    num_pages = min(10, len(doc))  # Process up to 10 slides

    for i in range(num_pages):  
        page = doc[i]
        pix = page.get_pixmap()
        image_path = os.path.join(upload_dir, f'slide{i+1}.png')
        pix.save(image_path)  # Saves the image directly

        # Save the relative path for Django
        media_relative_path = f'product_files/{unique_id}/slide{i+1}.png'
        image_paths.append(media_relative_path)

    doc.close()  # Close PDF before deletion

        # Remove only the PDF file
    try:
        os.remove(pdf_path)
    except PermissionError:
        pass  # If file is locked, skip deletion

    return image_paths  # Return the paths of generated images
'''