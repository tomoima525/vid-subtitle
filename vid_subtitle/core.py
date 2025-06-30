"""
Core module for vid-subtitle library.
"""

import os
from typing import Optional

from .utils import (
    validate_inputs, 
    get_output_srt_path, 
    cleanup_temp_file,
    VidSubtitleError
)
from .audio_extractor import extract_audio, get_audio_duration
from .transcriber import transcribe_audio, estimate_transcription_cost
from .subtitle_generator import generate_srt, get_subtitle_stats
from .video_processor import create_video_with_burned_subtitles, get_video_info, estimate_processing_time


def add_subtitles(input_video: str, output_video: str, language: str = "en", 
                 verbose: bool = False) -> dict:
    """
    Add subtitles to a video using OpenAI Whisper API and FFmpeg.
    
    This is the main function of the vid-subtitle library. It performs the complete
    workflow of extracting audio, transcribing it, generating subtitles, and 
    embedding them into the video.
    
    Args:
        input_video (str): Path to the input video file (MP4 or MOV).
        output_video (str): Path for the output video file with embedded subtitles.
        language (str, optional): Language code for transcription. Defaults to "en".
        verbose (bool, optional): Whether to print progress information. Defaults to False.
        
    Returns:
        dict: Dictionary containing information about the process:
            - srt_file: Path to the generated SRT file
            - output_video: Path to the output video file
            - transcription_cost: Estimated cost of transcription
            - processing_time: Estimated processing time
            - subtitle_stats: Statistics about the generated subtitles
            
    Raises:
        VidSubtitleError: If any step in the process fails.
        
    Example:
        >>> from vid_subtitle import add_subtitles
        >>> result = add_subtitles("input.mp4", "output.mp4", language="en")
        >>> print(f"SRT file created: {result['srt_file']}")
        >>> print(f"Video with subtitles: {result['output_video']}")
    """
    temp_audio_file = None
    
    try:
        # Step 1: Validate inputs
        if verbose:
            print("Validating inputs...")
        validate_inputs(input_video, output_video, language)
        
        # Step 2: Get video information
        if verbose:
            print("Getting video information...")
        video_info = get_video_info(input_video)
        if verbose:
            print(f"Video duration: {video_info['duration']:.1f} seconds")
            print(f"Video resolution: {video_info['resolution']}")
        
        # Step 3: Extract audio from video
        if verbose:
            print("Extracting audio from video...")
        temp_audio_file = extract_audio(input_video)
        if verbose:
            print(f"Audio extracted to temporary file: {temp_audio_file}")
        
        # Step 4: Get audio duration and estimate cost
        audio_duration = get_audio_duration(temp_audio_file)
        estimated_cost = estimate_transcription_cost(audio_duration)
        if verbose:
            print(f"Audio duration: {audio_duration:.1f} seconds")
            print(f"Estimated transcription cost: ${estimated_cost:.4f}")
        
        # Step 5: Transcribe audio using Whisper API
        if verbose:
            print(f"Transcribing audio using Whisper API (language: {language})...")
        transcription = transcribe_audio(temp_audio_file, language)
        if verbose:
            print(f"Transcription completed. Text length: {len(transcription['text'])} characters")
        
        # Step 6: Generate SRT subtitle file
        srt_file_path = get_output_srt_path(input_video)
        if verbose:
            print(f"Generating SRT file: {srt_file_path}")
        generate_srt(transcription, srt_file_path)
        
        # Step 7: Get subtitle statistics
        subtitle_stats = get_subtitle_stats(srt_file_path)
        if verbose:
            print(f"Generated {subtitle_stats['subtitle_count']} subtitles")
        
        # Step 8: Embed subtitles into video
        if verbose:
            print(f"Embedding subtitles into video: {output_video}")
        create_video_with_burned_subtitles(input_video, srt_file_path, output_video)
        
        # Step 9: Estimate processing time
        processing_time = estimate_processing_time(video_info['duration'])
        
        if verbose:
            print("Process completed successfully!")
            print(f"Output video: {output_video}")
            print(f"SRT file: {srt_file_path}")
        
        # Return result information
        return {
            'srt_file': srt_file_path,
            'output_video': output_video,
            'transcription_cost': estimated_cost,
            'processing_time': processing_time,
            'subtitle_stats': subtitle_stats,
            'video_info': video_info,
            'transcription_language': transcription.get('language', language)
        }
        
    except Exception as e:
        # Clean up temporary files on error
        if temp_audio_file:
            cleanup_temp_file(temp_audio_file)
        
        # Re-raise the exception
        if isinstance(e, VidSubtitleError):
            raise
        else:
            raise VidSubtitleError(f"Unexpected error in add_subtitles: {str(e)}") from e
    
    finally:
        # Always clean up temporary files
        if temp_audio_file:
            cleanup_temp_file(temp_audio_file)


def extract_subtitles_only(input_video: str, output_srt: Optional[str] = None, 
                          language: str = "en", verbose: bool = False) -> dict:
    """
    Extract subtitles from a video without creating a new video file.
    
    This function only generates the SRT subtitle file without embedding
    subtitles into the video.
    
    Args:
        input_video (str): Path to the input video file (MP4 or MOV).
        output_srt (str, optional): Path for the output SRT file. 
                                   If None, uses input video name with .srt extension.
        language (str, optional): Language code for transcription. Defaults to "en".
        verbose (bool, optional): Whether to print progress information. Defaults to False.
        
    Returns:
        dict: Dictionary containing information about the process:
            - srt_file: Path to the generated SRT file
            - transcription_cost: Estimated cost of transcription
            - subtitle_stats: Statistics about the generated subtitles
            
    Raises:
        VidSubtitleError: If any step in the process fails.
    """
    temp_audio_file = None
    
    try:
        # Validate inputs (create dummy output video path for validation)
        dummy_output = input_video.replace('.mp4', '_temp.mp4').replace('.mov', '_temp.mov')
        validate_inputs(input_video, dummy_output, language)
        
        # Determine output SRT path
        if output_srt is None:
            output_srt = get_output_srt_path(input_video)
        
        if verbose:
            print("Extracting audio from video...")
        temp_audio_file = extract_audio(input_video)
        
        # Get audio duration and estimate cost
        audio_duration = get_audio_duration(temp_audio_file)
        estimated_cost = estimate_transcription_cost(audio_duration)
        if verbose:
            print(f"Estimated transcription cost: ${estimated_cost:.4f}")
        
        if verbose:
            print(f"Transcribing audio using Whisper API (language: {language})...")
        transcription = transcribe_audio(temp_audio_file, language)
        
        if verbose:
            print(f"Generating SRT file: {output_srt}")
        generate_srt(transcription, output_srt)
        
        # Get subtitle statistics
        subtitle_stats = get_subtitle_stats(output_srt)
        if verbose:
            print(f"Generated {subtitle_stats['subtitle_count']} subtitles")
            print("Subtitle extraction completed successfully!")
        
        return {
            'srt_file': output_srt,
            'transcription_cost': estimated_cost,
            'subtitle_stats': subtitle_stats,
            'transcription_language': transcription.get('language', language)
        }
        
    except Exception as e:
        if temp_audio_file:
            cleanup_temp_file(temp_audio_file)
        
        if isinstance(e, VidSubtitleError):
            raise
        else:
            raise VidSubtitleError(f"Unexpected error in extract_subtitles_only: {str(e)}") from e
    
    finally:
        if temp_audio_file:
            cleanup_temp_file(temp_audio_file)


def get_supported_languages() -> list:
    """
    Get a list of supported language codes for transcription.
    
    Returns:
        list: List of supported ISO 639-1 language codes.
    """
    return [
        'af', 'am', 'ar', 'as', 'az', 'ba', 'be', 'bg', 'bn', 'bo', 'br', 'bs',
        'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'es', 'et', 'eu', 'fa', 'fi',
        'fo', 'fr', 'gl', 'gu', 'ha', 'haw', 'he', 'hi', 'hr', 'ht', 'hu', 'hy',
        'id', 'is', 'it', 'ja', 'jw', 'ka', 'kk', 'km', 'kn', 'ko', 'la', 'lb',
        'ln', 'lo', 'lt', 'lv', 'mg', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt',
        'my', 'ne', 'nl', 'nn', 'no', 'oc', 'pa', 'pl', 'ps', 'pt', 'ro', 'ru',
        'sa', 'sd', 'si', 'sk', 'sl', 'sn', 'so', 'sq', 'sr', 'su', 'sv', 'sw',
        'ta', 'te', 'tg', 'th', 'tk', 'tl', 'tr', 'tt', 'uk', 'ur', 'uz', 'vi',
        'yi', 'yo', 'zh'
    ]


def get_library_info() -> dict:
    """
    Get information about the vid-subtitle library.
    
    Returns:
        dict: Library information including version, supported formats, etc.
    """
    from . import __version__
    
    return {
        'version': __version__,
        'supported_video_formats': ['.mp4', '.mov'],
        'supported_subtitle_formats': ['.srt'],
        'supported_languages': len(get_supported_languages()),
        'requires_ffmpeg': True,
        'requires_openai_api_key': True
    }


def add_subtitle_file(input_video: str, subtitle_file: str, output_video: str, 
                     verbose: bool = False) -> dict:
    """
    Add existing subtitles to a video using FFmpeg.
    
    This function embeds an existing SRT subtitle file into a video without
    performing any transcription. Useful when you already have subtitles.
    
    Args:
        input_video (str): Path to the input video file (MP4 or MOV).
        subtitle_file (str): Path to the SRT subtitle file.
        output_video (str): Path for the output video file with embedded subtitles.
        verbose (bool, optional): Whether to print progress information. Defaults to False.
        
    Returns:
        dict: Dictionary containing information about the process:
            - output_video: Path to the output video file
            - subtitle_file: Path to the input subtitle file
            - processing_time: Estimated processing time
            - video_info: Information about the input video
            
    Raises:
        VidSubtitleError: If any step in the process fails.
        
    Example:
        >>> from vid_subtitle import add_subtitle_file
        >>> result = add_subtitle_file("input.mp4", "subtitles.srt", "output.mp4")
        >>> print(f"Video with subtitles: {result['output_video']}")
    """
    try:
        # Step 1: Validate inputs
        if verbose:
            print("Validating inputs...")
        
        # Validate video file exists and is readable
        if not os.path.exists(input_video):
            raise VidSubtitleError(f"Input video file not found: {input_video}")
        
        # Validate subtitle file exists
        if not os.path.exists(subtitle_file):
            raise VidSubtitleError(f"Subtitle file not found: {subtitle_file}")
        
        # Validate subtitle file has .srt extension
        if not subtitle_file.lower().endswith('.srt'):
            raise VidSubtitleError("Subtitle file must have .srt extension")
        
        # Validate output path
        output_dir = os.path.dirname(output_video)
        if output_dir and not os.path.exists(output_dir):
            raise VidSubtitleError(f"Output directory does not exist: {output_dir}")
        
        # Step 2: Get video information
        if verbose:
            print("Getting video information...")
        video_info = get_video_info(input_video)
        if verbose:
            print(f"Video duration: {video_info['duration']:.1f} seconds")
            print(f"Video resolution: {video_info['resolution']}")
        
        # Step 3: Embed subtitles into video
        if verbose:
            print(f"Embedding subtitles into video: {output_video}")
        create_video_with_burned_subtitles(input_video, subtitle_file, output_video)
        
        # Step 4: Estimate processing time
        processing_time = estimate_processing_time(video_info['duration'])
        
        if verbose:
            print("Process completed successfully!")
            print(f"Output video: {output_video}")
            print(f"Subtitle file used: {subtitle_file}")
        
        # Return result information
        return {
            'output_video': output_video,
            'subtitle_file': subtitle_file,
            'processing_time': processing_time,
            'video_info': video_info
        }
        
    except Exception as e:
        # Re-raise the exception
        if isinstance(e, VidSubtitleError):
            raise
        else:
            raise VidSubtitleError(f"Unexpected error in add_subtitle_file: {str(e)}") from e
