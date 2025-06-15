"""
Utility functions for vid-subtitle library.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class VidSubtitleError(Exception):
    """Base exception for vid-subtitle library."""
    pass


class FFmpegNotFoundError(VidSubtitleError):
    """Raised when FFmpeg is not found on the system."""
    pass


class InvalidVideoFormatError(VidSubtitleError):
    """Raised when the video format is not supported."""
    pass


class OpenAIKeyNotFoundError(VidSubtitleError):
    """Raised when OpenAI API key is not found."""
    pass


def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and available in the system PATH.
    
    Returns:
        bool: True if FFmpeg is available, False otherwise.
    """
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
            timeout=10
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def validate_video_format(video_path: str) -> bool:
    """
    Validate if the video file has a supported format.
    
    Args:
        video_path (str): Path to the video file.
        
    Returns:
        bool: True if format is supported, False otherwise.
    """
    supported_formats = {'.mp4', '.mov'}
    file_extension = Path(video_path).suffix.lower()
    return file_extension in supported_formats


def validate_file_exists(file_path: str) -> bool:
    """
    Check if a file exists and is readable.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        bool: True if file exists and is readable, False otherwise.
    """
    return os.path.isfile(file_path) and os.access(file_path, os.R_OK)


def get_openai_api_key() -> str:
    """
    Get OpenAI API key from environment variables.
    
    Returns:
        str: The OpenAI API key.
        
    Raises:
        OpenAIKeyNotFoundError: If the API key is not found.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise OpenAIKeyNotFoundError(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
        )
    return api_key


def create_temp_file(suffix: str = "") -> str:
    """
    Create a temporary file and return its path.
    
    Args:
        suffix (str): File suffix/extension.
        
    Returns:
        str: Path to the temporary file.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()
    return temp_file.name


def cleanup_temp_file(file_path: str) -> None:
    """
    Clean up a temporary file.
    
    Args:
        file_path (str): Path to the temporary file.
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except OSError:
        # Ignore errors when cleaning up temp files
        pass


def get_output_srt_path(input_video_path: str) -> str:
    """
    Generate the output SRT file path based on the input video path.
    
    Args:
        input_video_path (str): Path to the input video file.
        
    Returns:
        str: Path for the output SRT file.
    """
    video_path = Path(input_video_path)
    return str(video_path.with_suffix('.srt'))


def validate_inputs(input_video: str, output_video: str, language: str) -> None:
    """
    Validate all inputs for the add_subtitles function.
    
    Args:
        input_video (str): Path to input video file.
        output_video (str): Path to output video file.
        language (str): Language code.
        
    Raises:
        VidSubtitleError: If any validation fails.
    """
    # Check if FFmpeg is installed
    if not check_ffmpeg_installed():
        raise FFmpegNotFoundError(
            "FFmpeg is not installed or not found in PATH. "
            "Please install FFmpeg to use this library."
        )
    
    # Check if input video exists
    if not validate_file_exists(input_video):
        raise VidSubtitleError(f"Input video file not found or not readable: {input_video}")
    
    # Check if input video format is supported
    if not validate_video_format(input_video):
        raise InvalidVideoFormatError(
            f"Unsupported video format. Supported formats: .mp4, .mov. "
            f"Got: {Path(input_video).suffix}"
        )
    
    # Check if output directory exists and is writable
    output_dir = Path(output_video).parent
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise VidSubtitleError(f"Cannot create output directory: {e}")
    
    if not os.access(output_dir, os.W_OK):
        raise VidSubtitleError(f"Output directory is not writable: {output_dir}")
    
    # Validate language code (basic check)
    if not isinstance(language, str) or len(language) < 2:
        raise VidSubtitleError(f"Invalid language code: {language}")
    
    # Check OpenAI API key
    get_openai_api_key()
