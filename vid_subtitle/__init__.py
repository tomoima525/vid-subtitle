"""
vid-subtitle: A Python library to add subtitles to videos using FFmpeg and OpenAI Whisper API.
"""

from .core import (
    add_subtitles,
    extract_subtitles_only,
    get_supported_languages,
    get_library_info,
    add_subtitle_file,
    refine_subtitles
)

__version__ = "0.1.0"
__author__ = "Tomoaki Imai"
__email__ = "tomoima525@gmail.com"

__all__ = [
    "add_subtitles",
    "extract_subtitles_only", 
    "get_supported_languages",
    "get_library_info",
    "add_subtitle_file",
    "refine_subtitles"
]
