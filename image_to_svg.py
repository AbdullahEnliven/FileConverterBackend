import os
import subprocess
from PIL import Image
import tempfile
import shutil

def image_to_svg(input_path, output_path, num_colors=8):
    """
    Convert raster image to colorful SVG using vtracer or potrace.
    
    Args:
        input_path: Path to input raster image
        output_path: Path to save output SVG file
        num_colors: Number of colors (2-16, default 8)
        
    Returns:
        dict: Result information with success status, file sizes, method used
    """
    try:
        # Method 1: Try using vtracer (BEST quality for color SVGs)
        try:
            import vtracer
            
            # Open and resize if too large (for performance)
            img = Image.open(input_path)
            original_size = os.path.getsize(input_path)
            
            max_size = 1024
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                img.save(tmp_path, 'PNG')
            
            try:
                # Convert with vtracer - FULL COLOR support
                vtracer.convert_image_to_svg_py(
                    tmp_path,
                    output_path,
                    colormode='color',  # Full color mode
                    hierarchical='stacked',
                    mode='spline',
                    filter_speckle=4,  # Remove small artifacts
                    color_precision=6,
                    layer_difference=16,
                    corner_threshold=60,
                    length_threshold=4.0,
                    splice_threshold=45,
                    path_precision=8
                )
                
                if os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    return {
                        'success': True,
                        'input_size': original_size,
                        'output_size': output_size,
                        'output_path': output_path,
                        'method': 'vtracer',
                        'colors_traced': num_colors
                    }
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
        except ImportError:
            pass  # vtracer not available, try potrace
        except Exception as e:
            print(f"vtracer failed: {e}")
            pass
        
        # Method 2: Fallback to potrace (basic, works but lower quality)
        img = Image.open(input_path)
        original_size = os.path.getsize(input_path)
        original_width, original_height = img.size
        
        # Resize for better results
        max_dimension = 600
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Quantize colors
        img = img.convert("RGB")
        img = img.convert("P", palette=Image.Resampling.ADAPTIVE, colors=num_colors)
        img = img.convert("RGB")
        
        # Get dominant colors (skip near-white colors)
        colors = img.getcolors(maxcolors=num_colors * 2)
        if not colors:
            return {
                'success': False,
                'error': 'Could not extract colors from image'
            }
        
        colors = sorted(colors, key=lambda x: x[0], reverse=True)
        
        # Filter out background-like colors
        filtered_colors = []
        for count, color in colors[:num_colors]:
            # Skip very light colors (likely background)
            if sum(color) < 720:  # Not too white
                filtered_colors.append(color)
        
        if not filtered_colors:
            filtered_colors = [colors[0][1]]  # At least keep one color
        
        temp_dir = tempfile.mkdtemp()
        svg_layers = []
        
        try:
            for idx, color in enumerate(filtered_colors):
                # Create mask with some tolerance
                mask = Image.new('L', img.size, 0)
                pixels = img.load()
                mask_pixels = mask.load()
                
                for y in range(img.size[1]):
                    for x in range(img.size[0]):
                        pixel = pixels[x, y]
                        # Color matching with tolerance
                        diff = sum(abs(pixel[i] - color[i]) for i in range(3))
                        if diff < 30:  # Tolerance
                            mask_pixels[x, y] = 255
                
                # Apply median filter to reduce noise
                try:
                    from PIL import ImageFilter
                    mask = mask.filter(ImageFilter.MedianFilter(3))
                except:
                    pass
                
                mask_path = os.path.join(temp_dir, f'mask_{idx}.bmp')
                mask.save(mask_path, 'BMP')
                
                svg_path = os.path.join(temp_dir, f'layer_{idx}.svg')
                
                # Optimized potrace settings
                result = subprocess.run(
                    ['potrace', '-s', '-o', svg_path, 
                     '-t', '1.5',  # Threshold
                     '-O', '0.2',  # Optimization
                     '-a', '0.5',  # Corner threshold
                     '-u', '10',   # Unit size
                     '--opttolerance', '0.2',
                     mask_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and os.path.exists(svg_path):
                    with open(svg_path, 'r') as f:
                        content = f.read()
                        if '<path' in content:
                            hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
                            svg_layers.append({
                                'color': hex_color,
                                'svg_content': content
                            })
            
            if not svg_layers:
                return {
                    'success': False,
                    'error': 'No vector paths generated'
                }
            
            # Build combined SVG with proper scaling
            svg_header = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{img.size[0]}" 
     height="{img.size[1]}" 
     viewBox="0 0 {img.size[0]} {img.size[1]}"
     preserveAspectRatio="xMidYMid meet">
'''
            
            svg_content = svg_header
            
            # Extract and combine paths from each layer
            for layer in svg_layers:
                content = layer['svg_content']
                # Extract paths
                import re
                paths = re.findall(r'<path[^>]*d="([^"]*)"[^>]*/?>', content)
                for path_d in paths:
                    svg_content += f'  <path fill="{layer["color"]}" d="{path_d}"/>\n'
            
            svg_content += '</svg>'
            
            with open(output_path, 'w') as f:
                f.write(svg_content)
            
            output_size = os.path.getsize(output_path)
            
            return {
                'success': True,
                'input_size': original_size,
                'output_size': output_size,
                'output_path': output_path,
                'method': 'potrace',
                'colors_traced': len(svg_layers),
                'note': 'Using potrace. For better quality, vtracer is recommended but requires Rust compiler.'
            }
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Conversion error: {str(e)}'
        }
