"""
Video Conversion Service
Converts videos between different formats
"""

import os
from moviepy.editor import VideoFileClip


def convert_video(input_path, output_path, output_format='mp4', resolution=None, fps=None):
    """
    Convert video to different format
    
    Args:
        input_path: Path to input video
        output_path: Path to save output video
        output_format: Output format (mp4, avi, mkv, mov, webm)
        resolution: Tuple (width, height) or None to maintain original
        fps: Frames per second or None to maintain original
        
    Returns:
        dict: Result information
    """
    try:
        # Load video
        video = VideoFileClip(input_path)
        
        # Resize if specified
        if resolution:
            video = video.resize(resolution)
        
        # Change fps if specified
        if fps:
            video = video.set_fps(fps)
        
        # Set codec based on format
        codec_map = {
            'mp4': 'libx264',
            'avi': 'png',
            'mkv': 'libx264',
            'mov': 'libx264',
            'webm': 'libvpx'
        }
        
        codec = codec_map.get(output_format.lower(), 'libx264')
        
        # Write output video
        video.write_videofile(
            output_path,
            codec=codec,
            audio_codec='aac' if output_format != 'webm' else 'libvorbis'
        )
        
        video.close()
        
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


def convert_video_batch(input_paths, output_dir, output_format='mp4', resolution=None):
    """
    Convert multiple videos
    
    Args:
        input_paths: List of input video paths
        output_dir: Directory to save outputs
        output_format: Output format
        resolution: Resolution tuple or None
        
    Returns:
        list: Results for each video
    """
    results = []
    
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.{output_format}")
        
        result = convert_video(input_path, output_path, output_format, resolution)
        result['filename'] = filename
        results.append(result)
    
    return results


def get_video_info(video_path):
    """
    Get information about a video file
    
    Args:
        video_path: Path to video file
        
    Returns:
        dict: Video information
    """
    try:
        video = VideoFileClip(video_path)
        
        info = {
            'duration': video.duration,
            'fps': video.fps,
            'size': video.size,
            'width': video.w,
            'height': video.h
        }
        
        video.close()
        return info
        
    except Exception as e:
        return {'error': str(e)}