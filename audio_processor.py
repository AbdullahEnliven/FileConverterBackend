"""
Audio Extraction and Conversion Service
Extracts audio from videos and converts between audio formats
"""

import os
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment


def extract_audio_from_video(input_path, output_path, audio_format='mp3'):
    """
    Extract audio from video file
    
    Args:
        input_path: Path to input video
        output_path: Path to save output audio
        audio_format: Output format (mp3, wav, aac, ogg)
        
    Returns:
        dict: Result information
    """
    try:
        # Load video
        video = VideoFileClip(input_path)
        
        # Extract audio
        audio = video.audio
        
        if audio is None:
            return {
                'success': False,
                'error': 'No audio track found in video'
            }
        
        # Write audio file
        audio.write_audiofile(output_path)
        
        video.close()
        audio.close()
        
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


def convert_audio(input_path, output_path, output_format='mp3', bitrate='192k'):
    """
    Convert audio between formats
    
    Args:
        input_path: Path to input audio
        output_path: Path to save output audio
        output_format: Output format (mp3, wav, aac, ogg)
        bitrate: Audio bitrate (e.g., '192k', '256k')
        
    Returns:
        dict: Result information
    """
    try:
        # Detect input format
        input_ext = os.path.splitext(input_path)[1].lower().replace('.', '')
        
        # Load audio using pydub
        if input_ext == 'mp3':
            audio = AudioSegment.from_mp3(input_path)
        elif input_ext == 'wav':
            audio = AudioSegment.from_wav(input_path)
        elif input_ext in ['ogg', 'oga']:
            audio = AudioSegment.from_ogg(input_path)
        else:
            audio = AudioSegment.from_file(input_path)
        
        # Export in target format
        if output_format == 'mp3':
            audio.export(output_path, format='mp3', bitrate=bitrate)
        elif output_format == 'wav':
            audio.export(output_path, format='wav')
        elif output_format == 'ogg':
            audio.export(output_path, format='ogg', bitrate=bitrate)
        elif output_format == 'aac':
            audio.export(output_path, format='adts', bitrate=bitrate)
        else:
            audio.export(output_path, format=output_format)
        
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


def trim_audio(input_path, output_path, start_time=0, end_time=None):
    """
    Trim audio file
    
    Args:
        input_path: Path to input audio
        output_path: Path to save output audio
        start_time: Start time in seconds
        end_time: End time in seconds (None = end of file)
        
    Returns:
        dict: Result information
    """
    try:
        # Load audio
        audio = AudioSegment.from_file(input_path)
        
        # Convert times to milliseconds
        start_ms = start_time * 1000
        end_ms = end_time * 1000 if end_time else len(audio)
        
        # Trim audio
        trimmed = audio[start_ms:end_ms]
        
        # Export
        output_format = os.path.splitext(output_path)[1].lower().replace('.', '')
        trimmed.export(output_path, format=output_format)
        
        # Get file sizes
        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        
        return {
            'success': True,
            'input_size': input_size,
            'output_size': output_size,
            'output_path': output_path,
            'duration': len(trimmed) / 1000
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def extract_audio_batch(input_paths, output_dir, audio_format='mp3'):
    """
    Extract audio from multiple videos
    
    Args:
        input_paths: List of input video paths
        output_dir: Directory to save outputs
        audio_format: Output audio format
        
    Returns:
        list: Results for each video
    """
    results = []
    
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.{audio_format}")
        
        result = extract_audio_from_video(input_path, output_path, audio_format)
        result['filename'] = filename
        results.append(result)
    
    return results


def convert_audio_batch(input_paths, output_dir, output_format='mp3', bitrate='192k'):
    """
    Convert multiple audio files
    
    Args:
        input_paths: List of input audio paths
        output_dir: Directory to save outputs
        output_format: Output audio format
        bitrate: Audio bitrate
        
    Returns:
        list: Results for each audio file
    """
    results = []
    
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.{output_format}")
        
        result = convert_audio(input_path, output_path, output_format, bitrate)
        result['filename'] = filename
        results.append(result)
    
    return results