"""
PDF to Word Conversion Service
Converts PDF files to Word documents
"""

import os
from pdf2docx import Converter
from PyPDF2 import PdfReader


def pdf_to_word(input_path, output_path):
    """
    Convert PDF to Word document
    
    Args:
        input_path: Path to input PDF
        output_path: Path to save output DOCX
        
    Returns:
        dict: Result information
    """
    try:
        # Create converter
        cv = Converter(input_path)
        
        # Convert
        cv.convert(output_path)
        cv.close()
        
        # Get file sizes
        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        
        return {
            'success': True,
            'input_size': input_size,
            'output_size': output_size,
            'output_path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def pdf_to_word_batch(input_paths, output_dir):
    """
    Convert multiple PDFs to Word documents
    
    Args:
        input_paths: List of input PDF paths
        output_dir: Directory to save outputs
        
    Returns:
        list: Results for each PDF
    """
    results = []
    
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.docx")
        
        result = pdf_to_word(input_path, output_path)
        result['filename'] = filename
        results.append(result)
    
    return results