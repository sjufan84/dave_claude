""" Utility functions for extracting text from images and text files. """
import logging
from io import BytesIO
import pdfplumber
import docx

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")

def extract_docx_file_contents(file: bytes) -> str:
    """ Extract the text from the docx file. """
    file_contents = ''
    try:
        file = BytesIO(file)
        doc = docx.Document(file)
        for paragraph in doc.paragraphs:
            logger.debug(f"Paragraph: {paragraph.text}")
            file_contents += paragraph.text
    except Exception as e:
        logger.error(f"Error extracting text from docx file: {e}")
    logger.debug(f"File contents: {file_contents}")
    return file_contents

def extract_text_file_contents(file) -> str:
    """ Extract the text from the text file."""
    total_file_contents = ''
    try:
        file_contents = file
        total_file_contents += file_contents
    except Exception as e:
        logger.error(f"Error extracting text from text file: {e}")
    return total_file_contents

def extract_pdf_file_contents(file: bytes) -> str:
    """ Extract the text from the pdf file. """
    file_contents = ''
    try:
        pdf = pdfplumber.open(BytesIO(file))
        for page in pdf.pages:
            file_contents += page.extract_text()
    except Exception as e:
        logger.error(f"Error extracting text from pdf file: {e}")

    return file_contents
