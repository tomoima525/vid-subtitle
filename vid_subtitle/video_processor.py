"""
Video processing module for embedding subtitles using FFmpeg.
"""

import subprocess
from typing import Optional

from .utils import VidSubtitleError


class VideoProcessingError(VidSubtitleError):
    """Raised when video processing fails."""
    pass


def create_video_with_burned_subtitles(video_path: str, srt_path: str, output_path: str,
                                     subtitle_style: Optional[str] = None) -> str:
    """
    Create a video with burned-in (hardcoded) subtitles using FFmpeg.
    
    Args:
        video_path (str): Path to the input video file.
        srt_path (str): Path to the SRT subtitle file.
        output_path (str): Path for the output video file.
        subtitle_style (str, optional): Custom subtitle styling options.
        
    Returns:
        str: Path to the output video file.
        
    Raises:
        VideoProcessingError: If video processing fails.
    """
    try:
        # Escape the subtitle file path for FFmpeg filter
        escaped_srt_path = srt_path.replace('\\', '\\\\').replace(':', '\\:')
        
        # Default subtitle style for burned-in subtitles
        if subtitle_style is None:
            subtitle_filter = f"subtitles='{escaped_srt_path}':force_style='FontName=Arial,FontSize=20,PrimaryColour=&Hffffff,OutlineColour=&H0,Outline=2,Alignment=2'"
        else:
            subtitle_filter = f"subtitles='{escaped_srt_path}':force_style='{subtitle_style}'"
        
        # FFmpeg command to burn subtitles into video
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', subtitle_filter,  # Video filter to burn subtitles
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y',  # Overwrite output
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=600  # 10 minutes timeout
        )
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg burned subtitle creation failed: {e.stderr}"
        raise VideoProcessingError(error_msg) from e
        
    except subprocess.TimeoutExpired as e:
        error_msg = "Video processing timed out (10 minutes limit exceeded)"
        raise VideoProcessingError(error_msg) from e
        
    except Exception as e:
        error_msg = f"Unexpected error during burned subtitle creation: {str(e)}"
        raise VideoProcessingError(error_msg) from e


def get_video_info(video_path: str) -> dict:
    """
    Get information about a video file using FFprobe.
    
    Args:
        video_path (str): Path to the video file.
        
    Returns:
        dict: Video information including duration, resolution, etc.
        
    Raises:
        VideoProcessingError: If getting video info fails.
    """
    try:
        # Get video duration
        duration_cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            video_path
        ]
        
        duration_result = subprocess.run(
            duration_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        duration = float(duration_result.stdout.strip())
        
        # Get video resolution
        resolution_cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            video_path
        ]
        
        resolution_result = subprocess.run(
            resolution_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        width, height = map(int, resolution_result.stdout.strip().split(','))
        
        # Get frame rate
        fps_cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'csv=p=0',
            video_path
        ]
        
        fps_result = subprocess.run(
            fps_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        fps_str = fps_result.stdout.strip()
        if '/' in fps_str:
            num, den = map(int, fps_str.split('/'))
            fps = num / den if den != 0 else 0
        else:
            fps = float(fps_str)
        
        return {
            'duration': duration,
            'width': width,
            'height': height,
            'fps': fps,
            'resolution': f"{width}x{height}"
        }
        
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired) as e:
        error_msg = f"Failed to get video information: {str(e)}"
        raise VideoProcessingError(error_msg) from e


def validate_video_file(video_path: str) -> bool:
    """
    Validate if a video file is readable by FFmpeg.
    
    Args:
        video_path (str): Path to the video file.
        
    Returns:
        bool: True if video is valid, False otherwise.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            video_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        # If we can get duration, the video is likely valid
        duration = float(result.stdout.strip())
        return duration > 0
        
    except Exception:
        return False


def estimate_processing_time(video_duration: float, burn_subtitles: bool = False) -> float:
    """
    Estimate video processing time based on duration and operation type.
    
    Args:
        video_duration (float): Duration of video in seconds.
        burn_subtitles (bool): Whether subtitles will be burned in.
        
    Returns:
        float: Estimated processing time in seconds.
    """
    if burn_subtitles:
        # Burning subtitles requires re-encoding, much slower
        # Estimate: 1 minute of video = 2-5 minutes processing time
        return video_duration * 3
    else:
        # Just embedding subtitles, much faster
        # Estimate: 1 minute of video = 5-15 seconds processing time
        return video_duration * 0.15
