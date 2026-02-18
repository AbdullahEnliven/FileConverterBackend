"""
PDF Image Extraction Service
Extracts images from PDF files
"""

import os
import fitz  # PyMuPDF
from PIL import Image
import io


def extract_images_from_pdf(input_path, output_dir):
    """
    Extract all images from PDF
    
    Args:
        input_path: Path to input PDF
        output_dir: Directory to save extracted images
        
    Returns:
        dict: Result information
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Open PDF
        pdf_document = fitz.open(input_path)
        
        image_count = 0
        extracted_images = []
        
        # Iterate through pages
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Get images on page
            image_list = page.get_images()
            
            # Extract each image
            for img_index, img in enumerate(image_list):
                xref = img[0]
                
                # Get image data
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Create output filename
                output_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                output_path = os.path.join(output_dir, output_filename)
                
                # Save image
                with open(output_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                extracted_images.append({
                    'filename': output_filename,
                    'page': page_num + 1,
                    'size': len(image_bytes)
                })
                
                image_count += 1
        
        pdf_document.close()
        
        return {
            'success': True,
            'image_count': image_count,
            'extracted_images': extracted_images,
            'output_dir': output_dir
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def extract_images_from_pdf_batch(input_paths, output_base_dir):
    """
    Extract images from multiple PDFs
    
    Args:
        input_paths: List of input PDF paths
        output_base_dir: Base directory for outputs
        
    Returns:
        list: Results for each PDF
    """
    results = []
    
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        
        # Create subdirectory for this PDF's images
        output_dir = os.path.join(output_base_dir, f"{name}_images")
        
        result = extract_images_from_pdf(input_path, output_dir)
        result['pdf_filename'] = filename
        results.append(result)
    
    return results