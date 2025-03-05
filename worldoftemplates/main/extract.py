import os
import uuid
import subprocess
from django.shortcuts import render
from django.conf import settings
import pymupdf as fitz  # PyMuPDF
from pptx import Presentation
from PIL import Image

LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"

def convert_pptx_to_jpeg(request):
    if request.method == 'POST' and 'pptx_file' in request.FILES:
        pptx_file = request.FILES['pptx_file']

        # ✅ Generate Unique ID for This Upload
        unique_id = str(uuid.uuid4())
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', unique_id)
        os.makedirs(upload_dir, exist_ok=True)

        # ✅ Save the PPTX file permanently in the same folder as images
        pptx_path = os.path.join(upload_dir, pptx_file.name)
        with open(pptx_path, 'wb+') as f:
            for chunk in pptx_file.chunks():
                f.write(chunk)

        # ✅ Convert PPTX to PDF using LibreOffice
        pdf_path = pptx_path.replace('.pptx', '.pdf')
        convert_command = [
            LIBREOFFICE_PATH, "--headless", "--convert-to", "pdf", pptx_path, "--outdir", upload_dir
        ]
        subprocess.run(convert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(pdf_path):
            return render(request, 'pptx_uploader/upload.html', {'error': 'Failed to convert PPTX to PDF.'})

        # ✅ Convert FIRST 10 PDF pages to images using PyMuPDF
        doc = fitz.open(pdf_path)
        image_paths = []
        num_pages = min(10, len(doc))  # Process at most 10 slides or total available

        for i in range(num_pages):  
            page = doc[i]
            pix = page.get_pixmap()
            image_path = os.path.join(upload_dir, f'slide{i+1}.png')

            # ✅ Convert Pixmap to PIL Image and Save as PNG
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(image_path, format="PNG")

            image_paths.append(os.path.join('uploads', unique_id, f'slide{i+1}.png'))

        doc.close()  # Explicitly close the PDF before deleting

        # ✅ Remove only the PDF (keep PPTX & images)
        try:
            os.remove(pdf_path)
        except PermissionError:
            pass  # If file is locked, don't crash

        # ✅ Pass PPTX file path for download
        pptx_download_path = os.path.join('uploads', unique_id, pptx_file.name)

        return render(request, 'pptx_uploader/result.html', {
            'image_paths': image_paths,
            'pptx_download': pptx_download_path
        })

    return render(request, 'pptx_uploader/upload.html')
