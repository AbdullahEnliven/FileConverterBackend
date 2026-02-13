"""
Background Removal Service
Removes background from images using AI
"""

from PIL import Image
from rembg import remove
from io import BytesIO
import os

def remove_background(input_path, output_path, add_background_color=None):
    """
    Remove background from image and preserve quality.
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image
        add_background_color: Optional string "R,G,B" or tuple (R, G, B) for solid background
        
    Returns:
        dict: Result information
    """
    try:
        # Open input image to preserve format
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()

        # Remove background
        output_data = remove(input_data)

        # Convert to PIL Image
        img = Image.open(BytesIO(output_data))

        # Parse background color if it's a string
        if add_background_color:
            if isinstance(add_background_color, str):
                # Parse "R,G,B" format from frontend
                rgb_values = tuple(int(x.strip()) for x in add_background_color.split(','))
                add_background_color = rgb_values

        # Add solid background if requested
        if add_background_color:
            background = Image.new('RGB', img.size, add_background_color)
            background.paste(img, (0, 0), img)  # Using transparency
            img = background
            # Save as PNG with background
            img.save(output_path, format='PNG', quality=95)
        else:
            # Save as PNG with transparency
            img.save(output_path, format='PNG', quality=95)
        
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

def process_batch_background_removal(input_paths, output_dir, add_background_color=None):
    """
    Process multiple images for background removal with improved quality.
    
    Args:
        input_paths: List of input image paths
        output_dir: Directory to save outputs
        add_background_color: Optional background color
        
    Returns:
        list: Results for each image
    """
    results = []
    
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}_no_bg{ext}")  # Keep original extension
        
        result = remove_background(input_path, output_path, add_background_color)
        result['filename'] = filename
        results.append(result)
    
    return results
