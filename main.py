import os
import shutil
import uuid
import socket
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from io import BytesIO
import zipfile

# Import all conversion services
import background_remover
import pdf_to_word
import word_to_pdf
import ppt_to_pdf
import ppt_to_word
import excel_to_pdf
import excel_to_word
import word_to_txt
import pdf_to_txt
import pdf_image_extractor
import ppt_image_extractor
import ppt_slide_exporter
import video_converter
import audio_processor
import pdf_compressor
import image_to_svg  # NEW: Image to SVG converter

app = Flask(__name__)

# ============= CORS CONFIGURATION - CRITICAL FOR CROSS-DEVICE ACCESS =============
# This allows requests from ANY origin (your phone, other computers, etc.)
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Disposition"],
        "supports_credentials": False
    }
})

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {
    'image': {'jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'heic'},
    'document': {'pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls', 'txt'},
    'video': {'mp4', 'avi', 'mkv', 'mov', 'webm'},
    'audio': {'mp3', 'wav', 'aac', 'ogg'}
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"


def allowed_file(filename, file_type):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[file_type]


def create_session_dir():
    """Create unique session directory for file processing"""
    session_id = str(uuid.uuid4())
    session_upload = os.path.join(UPLOAD_FOLDER, session_id)
    session_output = os.path.join(OUTPUT_FOLDER, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_output, exist_ok=True)
    return session_id, session_upload, session_output


def cleanup_old_files():
    """Clean up files older than 1 hour"""
    current_time = datetime.now()
    
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        if os.path.exists(folder):
            for session_dir in os.listdir(folder):
                session_path = os.path.join(folder, session_dir)
                if os.path.isdir(session_path):
                    try:
                        creation_time = datetime.fromtimestamp(os.path.getctime(session_path))
                        if current_time - creation_time > timedelta(hours=1):
                            shutil.rmtree(session_path)
                    except Exception as e:
                        print(f"Error cleaning up {session_path}: {e}")


def create_zip_file(file_paths, zip_path):
    """Create ZIP file from multiple files"""
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_path in file_paths:
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))
    return zip_path


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'ConvertAll Backend is running',
        'server_ip': get_local_ip()
    })


# ============= NEW: Image to SVG Conversion =============
@app.route('/api/convert/image-to-svg', methods=['POST'])
def convert_image_to_svg():
    """Convert raster image to SVG vector format"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, 'image'):
        return jsonify({'error': 'Invalid file type. Please upload an image file.'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.svg"
    output_path = os.path.join(output_dir, output_filename)
    
    result = image_to_svg.image_to_svg(input_path, output_path)
    
    if result['success']:
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}',
            'input_size': result.get('input_size'),
            'output_size': result.get('output_size')
        })
    else:
        return jsonify({'error': result['error']}), 500


@app.route('/api/compress/pdf', methods=['POST'])
def compress_pdf_api():
    cleanup_old_files()

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be PDF'}), 400

    level = request.form.get('level', 'ebook')
    session_id, upload_dir, output_dir = create_session_dir()

    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)

    name, _ = os.path.splitext(filename)
    output_filename = f"{name}_compressed.pdf"
    output_path = os.path.join(output_dir, output_filename)

    result = pdf_compressor.compress_pdf(input_path, output_path, level=level)

    if result.get("success"):
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}',
            'before_bytes': result.get('before_bytes'),
            'after_bytes': result.get('after_bytes'),
            'reduction_percent': result.get('reduction_percent'),
            'method': result.get('method'),
            'warning': result.get('warning'),
        })

    return jsonify({'error': result.get('error', 'Compression failed')}), 500


# ============= Background Removal =============
@app.route('/api/remove-background', methods=['POST'])
def remove_background():
    """Remove background from image"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, 'image'):
        return jsonify({'error': 'Invalid file type'}), 400
    
    background_color = request.form.get('backgroundColor') or request.form.get('background_color')
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}_no_bg.png"
    output_path = os.path.join(output_dir, output_filename)
    
    result = background_remover.remove_background(input_path, output_path, background_color)
    
    if result['success']:
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result['error']}), 500


# ============= Document Conversions =============
@app.route('/api/convert/pdf-to-word', methods=['POST'])
def convert_pdf_to_word():
    """Convert PDF to Word"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be PDF'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.docx"
    output_path = os.path.join(output_dir, output_filename)
    
    result = pdf_to_word.pdf_to_word(input_path, output_path)
    
    if result['success']:
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result.get('error', 'Conversion failed')}), 500


@app.route('/api/convert/word-to-pdf', methods=['POST'])
def convert_word_to_pdf():
    """Convert Word to PDF"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith(('.docx', '.doc')):
        return jsonify({'error': 'File must be DOCX or DOC'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    result = word_to_pdf.word_to_pdf(input_path, output_path)
    
    if result.get('success'):
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result.get('error', 'Conversion failed')}), 500


@app.route('/api/convert/ppt-to-pdf', methods=['POST'])
def convert_ppt_to_pdf():
    """Convert PowerPoint to PDF"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith(('.pptx', '.ppt')):
        return jsonify({'error': 'File must be PPTX or PPT'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    result = ppt_to_pdf.ppt_to_pdf(input_path, output_path)
    
    if result.get('success'):
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result.get('error', 'Conversion failed')}), 500


@app.route('/api/convert/ppt-to-word', methods=['POST'])
def convert_ppt_to_word():
    """Convert PowerPoint to Word"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith(('.pptx', '.ppt')):
        return jsonify({'error': 'File must be PPTX or PPT'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.docx"
    output_path = os.path.join(output_dir, output_filename)
    
    result = ppt_to_word.ppt_to_word(input_path, output_path)
    
    if result.get('success'):
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result.get('error', 'Conversion failed')}), 500


@app.route('/api/convert/excel-to-pdf', methods=['POST'])
def convert_excel_to_pdf():
    """Convert Excel to PDF"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'File must be XLSX or XLS'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    result = excel_to_pdf.excel_to_pdf(input_path, output_path)
    
    if result.get('success'):
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result.get('error', 'Conversion failed')}), 500


@app.route('/api/convert/excel-to-word', methods=['POST'])
def convert_excel_to_word():
    """Convert Excel to Word"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'File must be XLSX or XLS'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.docx"
    output_path = os.path.join(output_dir, output_filename)
    
    result = excel_to_word.excel_to_word(input_path, output_path)
    
    if result.get('success'):
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result.get('error', 'Conversion failed')}), 500


@app.route('/api/convert/word-to-txt', methods=['POST'])
def convert_word_to_txt():
    """Convert Word to Text"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith(('.docx', '.doc')):
        return jsonify({'error': 'File must be DOCX or DOC'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.txt"
    output_path = os.path.join(output_dir, output_filename)
    
    result = word_to_txt.word_to_txt(input_path, output_path)
    
    if result.get('success'):
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result.get('error', 'Conversion failed')}), 500


@app.route('/api/convert/pdf-to-txt', methods=['POST'])
def convert_pdf_to_txt():
    """Convert PDF to Text"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be PDF'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.txt"
    output_path = os.path.join(output_dir, output_filename)
    
    result = pdf_to_txt.pdf_to_txt(input_path, output_path)
    
    if result.get('success'):
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result.get('error', 'Conversion failed')}), 500


# ============= Image Extraction =============
@app.route('/api/extract/pdf-images', methods=['POST'])
def extract_pdf_images():
    """Extract images from PDF"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be PDF'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    result = pdf_image_extractor.extract_images_from_pdf(input_path, output_dir)
    
    if result['success']:
        if result['image_count'] > 0:
            zip_filename = f"{os.path.splitext(filename)[0]}_images.zip"
            zip_path = os.path.join(output_dir, zip_filename)
            
            image_paths = [os.path.join(output_dir, img['filename']) for img in result['extracted_images']]
            create_zip_file(image_paths, zip_path)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'image_count': result['image_count'],
                'zip_filename': zip_filename,
                'download_url': f'/api/download/{session_id}/{zip_filename}'
            })
        else:
            return jsonify({
                'success': True,
                'image_count': 0,
                'message': 'No images found in PDF'
            })
    else:
        return jsonify({'error': result['error']}), 500


@app.route('/api/extract/ppt-images', methods=['POST'])
def extract_ppt_images():
    """Extract images from PowerPoint"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith('.pptx'):
        return jsonify({'error': 'File must be PPTX'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    result = ppt_image_extractor.extract_images_from_ppt(input_path, output_dir)
    
    if result['success']:
        if result['image_count'] > 0:
            zip_filename = f"{os.path.splitext(filename)[0]}_images.zip"
            zip_path = os.path.join(output_dir, zip_filename)
            
            image_paths = [os.path.join(output_dir, img['filename']) for img in result['extracted_images']]
            create_zip_file(image_paths, zip_path)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'image_count': result['image_count'],
                'zip_filename': zip_filename,
                'download_url': f'/api/download/{session_id}/{zip_filename}'
            })
        else:
            return jsonify({
                'success': True,
                'image_count': 0,
                'message': 'No images found in presentation'
            })
    else:
        return jsonify({'error': result['error']}), 500


@app.route('/api/export/ppt-slides', methods=['POST'])
def export_ppt_slides():
    """Export PowerPoint slides as images"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith('.pptx'):
        return jsonify({'error': 'File must be PPTX'}), 400
    
    image_format = request.form.get('format', 'png').lower()
    if image_format not in ['png', 'jpg', 'jpeg']:
        image_format = 'png'
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    result = ppt_slide_exporter.export_slides_as_images(input_path, output_dir, image_format)
    
    if result['success']:
        zip_filename = f"{os.path.splitext(filename)[0]}_slides.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        slide_paths = [os.path.join(output_dir, slide['filename']) for slide in result['exported_slides']]
        create_zip_file(slide_paths, zip_path)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'exported_count': result['exported_count'],
            'zip_filename': zip_filename,
            'download_url': f'/api/download/{session_id}/{zip_filename}'
        })
    else:
        return jsonify({'error': result['error']}), 500


# ============= Video Conversion =============
@app.route('/api/convert/video', methods=['POST'])
def convert_video():
    """Convert video format"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    output_format = request.form.get('format', 'mp4')
    
    if not allowed_file(file.filename, 'video'):
        return jsonify({'error': 'Invalid video file'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.{output_format}"
    output_path = os.path.join(output_dir, output_filename)
    
    resolution = request.form.get('resolution', None)
    if resolution:
        if resolution == '720p':
            resolution = (1280, 720)
        elif resolution == '1080p':
            resolution = (1920, 1080)
        else:
            resolution = None
    
    result = video_converter.convert_video(input_path, output_path, output_format, resolution)
    
    if result['success']:
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result['error']}), 500


# ============= Audio Extraction & Conversion =============
@app.route('/api/extract/audio', methods=['POST'])
def extract_audio():
    """Extract audio from video"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    audio_format = request.form.get('format', 'mp3')
    
    if not allowed_file(file.filename, 'video'):
        return jsonify({'error': 'Invalid video file'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.{audio_format}"
    output_path = os.path.join(output_dir, output_filename)
    
    result = audio_processor.extract_audio_from_video(input_path, output_path, audio_format)
    
    if result['success']:
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result['error']}), 500


@app.route('/api/convert/audio', methods=['POST'])
def convert_audio():
    """Convert audio format"""
    cleanup_old_files()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    output_format = request.form.get('format', 'mp3')
    bitrate = request.form.get('bitrate', '192k')
    
    if not allowed_file(file.filename, 'audio'):
        return jsonify({'error': 'Invalid audio file'}), 400
    
    session_id, upload_dir, output_dir = create_session_dir()
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_dir, filename)
    file.save(input_path)
    
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}.{output_format}"
    output_path = os.path.join(output_dir, output_filename)
    
    result = audio_processor.convert_audio(input_path, output_path, output_format, bitrate)
    
    if result['success']:
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file was not created'}), 500
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_filename': output_filename,
            'download_url': f'/api/download/{session_id}/{output_filename}'
        })
    else:
        return jsonify({'error': result['error']}), 500


# ============= Download Endpoint - WINDOWS & NETWORK FIX =============
@app.route('/api/download/<session_id>/<filename>', methods=['GET'])
def download_file(session_id, filename):
    """Download processed file - Windows compatible, network accessible version"""
    
    output_folder = Path(OUTPUT_FOLDER).resolve()
    session_folder = output_folder / session_id
    file_path = session_folder / filename
    
    if not file_path.exists():
        return jsonify({
            'error': 'File not found',
            'session_id': session_id,
            'filename': filename
        }), 404
    
    try:
        # Read file to memory to avoid Windows locking issues
        file_data = file_path.read_bytes()
        
        # Send from memory
        return send_file(
            BytesIO(file_data),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"[ERROR] Failed to send file: {e}")
        return jsonify({
            'error': f'Failed to send file: {str(e)}',
            'path': str(file_path)
        }), 500


# ============= Error Handlers =============
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 500MB'}), 413


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    import os
    import sys
    
    # Get port from environment (Railway sets this)
    PORT = int(os.environ.get('PORT', 5000))
    
    # Print for debugging
    print(f"=" * 70)
    print(f"Starting ConvertAll Backend on port {PORT}")
    print(f"Python version: {sys.version}")
    print(f"=" * 70)
    
    # Start server
    app.run(
        debug=False,  # Must be False in production!
        host='0.0.0.0',
        port=PORT,
        threaded=True
    )