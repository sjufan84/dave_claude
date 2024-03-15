""" Utility functions for extracting text from images and text files. """
from typing import List
import logging
from io import BytesIO
from fastapi import UploadFile
import google.cloud.vision as vision  # pylint: disable=no-member
import pdfplumber
import docx
from dependencies import get_google_vision_credentials

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")

# Load the environment variables
credentials = get_google_vision_credentials()

async def extract_docx_file_contents(files: List[UploadFile]) -> str:
    """ Extract the text from the docx file. """
    file_contents = ''
    try:
        for file in files:
            file = BytesIO(file)
            doc = docx.Document(file)
            for paragraph in doc.paragraphs:
                logger.debug(f"Paragraph: {paragraph.text}")
                file_contents += paragraph.text
    except Exception as e:
        logger.error(f"Error extracting text from docx file: {e}")
    logger.debug(f"File contents: {file_contents}")
    return file_contents

async def extract_text_file_contents(files) -> str:
    """ Extract the text from the text file."""
    total_file_contents = ''
    try:
        for file in files:
            file_contents = file
            total_file_contents += file_contents
    except Exception as e:
        logger.error(f"Error extracting text from text file: {e}")
    return file_contents

async def extract_pdf_file_contents(files: List[UploadFile]) -> str:
    """ Extract the text from the pdf file. """
    file_contents = ''
    try:
        for file in files:
            pdf = pdfplumber.open(file)
            for page in pdf.pages:
                file_contents += page.extract_text()
    except Exception as e:
        logger.error(f"Error extracting text from pdf file: {e}")
    return file_contents

async def extract_image_text(files: List[bytes]) -> str:
    """ Extract the text from the image file. """
    client = vision.ImageAnnotatorClient(credentials=credentials)
    total_response_text = ''
    try:
        for file in files:
            image = vision.Image(content=file)
            response = client.document_text_detection(image=image)
            response_text = response.full_text_annotation.text
            total_response_text += response_text
    except Exception as e:
        logger.error(f"Error extracting text from image file: {e}")
    return response_text
