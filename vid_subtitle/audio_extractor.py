"""
Audio extraction module using FFmpeg.
"""

import subprocess
from typing import Optional

from .utils import VidSubtitleError, create_temp_file, cleanup_temp_file


class AudioExtractionError(VidSubtitleError):
    """Raised when audio extraction fails."""
    pass


def extract_audio(video_path: str, output_audio_path: Optional[str] = None) -> str:
    """
    Extract audio from a video file using FFmpeg.
    
    Args:
        video_path (str): Path to the input video file.
        output_audio_path (str, optional): Path for the output audio file.
                                         If None, a temporary file will be created.
    
    Returns:
        str: Path to the extracted audio file.
        
    Raises:
        AudioExtractionError: If audio extraction fails.
    """
    if output_audio_path is None:
        output_audio_path = create_temp_file(suffix='.ogg')
    
    # FFmpeg command to extract audio
    # -i: input file
    # -vn: disable video recording
    # -acodec pcm_s16le: use PCM 16-bit little-endian audio codec
    # -ar 16000: set audio sample rate to 16kHz (optimal for Whisper)
    # -ac 1: set audio channels to 1 (mono)
    # -y: overwrite output file if it exists
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', 'libopus',
        '-b:a', '12k',
        '-application', 'voip',
        '-ac', '1',  # Mono
        '-y',  # Overwrite output
        output_audio_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # 5 minutes timeout
        )
        
        return output_audio_path
        
    except subprocess.CalledProcessError as e:
        # Clean up the output file if it was created
        cleanup_temp_file(output_audio_path)
        
        error_msg = f"FFmpeg audio extraction failed: {e.stderr}"
        raise AudioExtractionError(error_msg) from e
        
    except subprocess.TimeoutExpired as e:
        # Clean up the output file if it was created
        cleanup_temp_file(output_audio_path)
        
        error_msg = "Audio extraction timed out (5 minutes limit exceeded)"
        raise AudioExtractionError(error_msg) from e
        
    except Exception as e:
        # Clean up the output file if it was created
        cleanup_temp_file(output_audio_path)
        
        error_msg = f"Unexpected error during audio extraction: {str(e)}"
        raise AudioExtractionError(error_msg) from e


def get_audio_duration(audio_path: str) -> float:
    """
    Get the duration of an audio file in seconds using FFmpeg.
    
    Args:
        audio_path (str): Path to the audio file.
        
    Returns:
        float: Duration in seconds.
        
    Raises:
        AudioExtractionError: If getting duration fails.
    """
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'csv=p=0',
        audio_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        duration = float(result.stdout.strip())
        return duration
        
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired) as e:
        error_msg = f"Failed to get audio duration: {str(e)}"
        raise AudioExtractionError(error_msg) from e
