"""
Audio transcription module using OpenAI Whisper API.
"""

import os
from typing import Dict, Any

from openai import OpenAI

from .utils import VidSubtitleError, get_openai_api_key


class TranscriptionError(VidSubtitleError):
    """Raised when transcription fails."""
    pass


def transcribe_audio(audio_path: str, language: str = "en") -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper API.
    
    Args:
        audio_path (str): Path to the audio file.
        language (str): Language code for transcription (default: "en").
        
    Returns:
        Dict[str, Any]: Transcription result with text and segments.
        
    Raises:
        TranscriptionError: If transcription fails.
    """
    try:
        # Get OpenAI API key
        api_key = get_openai_api_key()
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Check if audio file exists
        if not os.path.exists(audio_path):
            raise TranscriptionError(f"Audio file not found: {audio_path}")
        
        # Check file size (OpenAI has a 25MB limit)
        file_size = os.path.getsize(audio_path)
        max_size = 25 * 1024 * 1024  # 25MB in bytes
        
        if file_size > max_size:
            raise TranscriptionError(
                f"Audio file too large ({file_size / (1024*1024):.1f}MB). "
                f"Maximum size is 25MB."
            )
        
        # Open and transcribe the audio file
        with open(audio_path, "rb") as audio_file:
            # Use the Whisper API with timestamp information
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json",  # Get detailed response with timestamps
                timestamp_granularities=["segment"],  # Get segment-level timestamps
            )
        
        # Convert the response to a dictionary format
        result = {
            "text": transcript.text,
            "language": transcript.language,
            "duration": transcript.duration,
            "segments": []
        }
        
        # Process segments if available
        if hasattr(transcript, 'segments') and transcript.segments:
            for segment in transcript.segments:
                segment_data = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                result["segments"].append(segment_data)
        else:
            # If no segments, create a single segment for the entire text
            result["segments"] = [{
                "id": 0,
                "start": 0.0,
                "end": transcript.duration,
                "text": transcript.text.strip()
            }]
        
        return result
        
    except Exception as e:
        if isinstance(e, TranscriptionError):
            raise
        
        # Handle OpenAI API errors
        error_msg = f"Transcription failed: {str(e)}"
        
        # Check for common API errors
        if "rate limit" in str(e).lower():
            error_msg = "OpenAI API rate limit exceeded. Please try again later."
        elif "invalid api key" in str(e).lower():
            error_msg = "Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable."
        elif "insufficient quota" in str(e).lower():
            error_msg = "OpenAI API quota exceeded. Please check your account billing."
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            error_msg = "Network error occurred. Please check your internet connection and try again."
        
        raise TranscriptionError(error_msg) from e


def validate_language_code(language: str) -> bool:
    """
    Validate if the language code is supported by Whisper.
    
    Args:
        language (str): Language code to validate.
        
    Returns:
        bool: True if language is supported, False otherwise.
    """
    # Common language codes supported by Whisper
    supported_languages = {
        'af', 'am', 'ar', 'as', 'az', 'ba', 'be', 'bg', 'bn', 'bo', 'br', 'bs',
        'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'es', 'et', 'eu', 'fa', 'fi',
        'fo', 'fr', 'gl', 'gu', 'ha', 'haw', 'he', 'hi', 'hr', 'ht', 'hu', 'hy',
        'id', 'is', 'it', 'ja', 'jw', 'ka', 'kk', 'km', 'kn', 'ko', 'la', 'lb',
        'ln', 'lo', 'lt', 'lv', 'mg', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt',
        'my', 'ne', 'nl', 'nn', 'no', 'oc', 'pa', 'pl', 'ps', 'pt', 'ro', 'ru',
        'sa', 'sd', 'si', 'sk', 'sl', 'sn', 'so', 'sq', 'sr', 'su', 'sv', 'sw',
        'ta', 'te', 'tg', 'th', 'tk', 'tl', 'tr', 'tt', 'uk', 'ur', 'uz', 'vi',
        'yi', 'yo', 'zh'
    }
    
    return language.lower() in supported_languages


def estimate_transcription_cost(audio_duration_seconds: float) -> float:
    """
    Estimate the cost of transcription based on audio duration.
    
    Args:
        audio_duration_seconds (float): Duration of audio in seconds.
        
    Returns:
        float: Estimated cost in USD.
    """
    # OpenAI Whisper API pricing: $0.006 per minute
    cost_per_minute = 0.006
    duration_minutes = audio_duration_seconds / 60.0
    return duration_minutes * cost_per_minute
