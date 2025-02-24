import os
from django.conf import settings
from spire.presentation import *

def ppt_to_images(ppt_file, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Open the PowerPoint file
    presentation = Presentation()
    presentation.LoadFromFile(ppt_file)

    slides_list = []

    # Export each slide as a PNG image
    for i, slide in enumerate(presentation.Slides):
        image_path = os.path.join(output_dir, f"slide_{i + 1}.png")
        image_stream = slide.SaveAsImage()

        with open(image_path, "wb") as img_file:
            img_file.write(image_stream.ToArray())

        slides_list.append(os.path.relpath(image_path, settings.MEDIA_ROOT))  # Save relative path for Django

    return slides_list