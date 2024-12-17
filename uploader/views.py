import os
import fitz  # PyMuPDF
import comtypes.client
import pythoncom
import logging
from django.http import StreamingHttpResponse
from django.conf import settings
from django.shortcuts import render
from .forms import UploadFileForm
from .models import UploadedFile
from .gesture_presentation import run_presentation

# Set up logging
logging.basicConfig(level=logging.INFO)


def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save()
            try:
                sasi = int(request.POST.get("camera") or 0)
                # Process the uploaded file
                process_file(uploaded_file.file.path, uploaded_file.id)
                output_dir = os.path.join(
                    settings.MEDIA_ROOT, "uploads", str(uploaded_file.id)
                )
                # run_presentation(output_dir)
                return render(
                    request,
                    "upload_success.html",
                    {"file": uploaded_file, "sasi": sasi},
                )
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                form.add_error(
                    None,
                    "An error occurred while processing the file. Please try again.",
                )
    else:
        form = UploadFileForm()
    return render(request, "upload.html", {"form": form})


def process_file(file_path, file_id):
    output_dir = os.path.join(
        settings.MEDIA_ROOT, "uploads", str(file_id)
    )  # Use MEDIA_ROOT for the base path
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    if file_path.lower().endswith(".pdf"):
        process_pdf(file_path, output_dir)
    elif file_path.lower().endswith((".ppt", ".pptx")):
        process_ppt(file_path, output_dir)
    else:
        logging.error(f"Unsupported file format: {file_path}")
        raise ValueError("Unsupported file format")


def process_pdf(file_path, output_dir):
    try:
        pdf_document = fitz.open(file_path)
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            pix = page.get_pixmap()
            image_path = os.path.join(output_dir, f"slide_{page_number + 1}.png")
            pix.save(image_path)
            logging.info(f"Saved PDF page {page_number + 1} as {image_path}")
    except Exception as e:
        logging.error(f"An error occurred while processing PDF: {e}")
        raise


def process_ppt(file_path, output_dir):
    try:
        pythoncom.CoInitialize()  # Initialize COM
        powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
        powerpoint.Visible = 1  # Make PowerPoint visible for debugging

        presentation = powerpoint.Presentations.Open(
            os.path.abspath(file_path), WithWindow=False
        )

        for slide_index in range(1, presentation.Slides.Count + 1):
            slide = presentation.Slides(slide_index)
            image_path = os.path.join(output_dir, f"slide_{slide_index}.png")

            # Ensure image_path is absolute
            image_path = os.path.abspath(image_path)
            slide.Export(image_path, "PNG")
            logging.info(f"Converted slide {slide_index} to {image_path}")

        presentation.Close()
        powerpoint.Quit()

    except Exception as e:
        logging.error(f"An error occurred while converting PPT: {e}")
        raise

    finally:
        pythoncom.CoUninitialize()  # Clean up COM


def presentation_stream(request, file_id, sasi):
    output_dir = os.path.join(settings.MEDIA_ROOT, "uploads", str(file_id))
    return StreamingHttpResponse(
        run_presentation(output_dir, sasi),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )
