"""
Subtitle generation module for creating SRT files.
"""

import re
from typing import Dict, Any, List

from .utils import VidSubtitleError


class SubtitleGenerationError(VidSubtitleError):
    """Raised when subtitle generation fails."""
    pass


def format_timestamp(seconds: float) -> str:
    """
    Format timestamp in seconds to SRT format (HH:MM:SS,mmm).
    
    Args:
        seconds (float): Time in seconds.
        
    Returns:
        str: Formatted timestamp string.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def clean_text(text: str) -> str:
    """
    Clean and format text for subtitle display.
    
    Args:
        text (str): Raw text to clean.
        
    Returns:
        str: Cleaned text.
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove or replace problematic characters
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    
    # Ensure text doesn't exceed reasonable length per line
    # Split long sentences into multiple lines
    if len(text) > 80:
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= 40:  # Max 40 chars per line
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Join with newline, but limit to 2 lines max
        text = '\n'.join(lines[:2])
    
    return text


def split_long_segments(segments: List[Dict[str, Any]], max_duration: float = 5.0) -> List[Dict[str, Any]]:
    """
    Split long segments into shorter ones for better readability.
    
    Args:
        segments (List[Dict[str, Any]]): List of transcript segments.
        max_duration (float): Maximum duration for a single subtitle (seconds).
        
    Returns:
        List[Dict[str, Any]]: List of processed segments.
    """
    processed_segments = []
    
    for segment in segments:
        duration = segment['end'] - segment['start']
        
        if duration <= max_duration:
            processed_segments.append(segment)
        else:
            # Split long segment
            text = segment['text']
            words = text.split()
            
            if len(words) <= 1:
                # Can't split further, keep as is
                processed_segments.append(segment)
                continue
            
            # Calculate how many parts we need
            num_parts = int(duration / max_duration) + 1
            words_per_part = len(words) // num_parts
            
            start_time = segment['start']
            time_per_part = duration / num_parts
            
            for i in range(num_parts):
                part_start = start_time + (i * time_per_part)
                part_end = start_time + ((i + 1) * time_per_part)
                
                # Get words for this part
                word_start = i * words_per_part
                if i == num_parts - 1:
                    # Last part gets remaining words
                    part_words = words[word_start:]
                else:
                    part_words = words[word_start:word_start + words_per_part]
                
                if part_words:  # Only add if there are words
                    new_segment = {
                        'id': len(processed_segments),
                        'start': part_start,
                        'end': part_end,
                        'text': ' '.join(part_words)
                    }
                    processed_segments.append(new_segment)
    
    return processed_segments


def generate_srt(transcription: Dict[str, Any], output_path: str) -> str:
    """
    Generate SRT subtitle file from transcription data.
    
    Args:
        transcription (Dict[str, Any]): Transcription data with segments.
        output_path (str): Path to save the SRT file.
        
    Returns:
        str: Path to the generated SRT file.
        
    Raises:
        SubtitleGenerationError: If SRT generation fails.
    """
    try:
        if 'segments' not in transcription or not transcription['segments']:
            raise SubtitleGenerationError("No segments found in transcription data")
        
        segments = transcription['segments']
        
        # Process segments (split long ones, clean text)
        processed_segments = split_long_segments(segments)
        
        # Generate SRT content
        srt_content = []
        
        for i, segment in enumerate(processed_segments, 1):
            # Subtitle number
            srt_content.append(str(i))
            
            # Timestamp line
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            srt_content.append(f"{start_time} --> {end_time}")
            
            # Subtitle text
            clean_subtitle_text = clean_text(segment['text'])
            if clean_subtitle_text:  # Only add non-empty text
                srt_content.append(clean_subtitle_text)
            else:
                srt_content.append("[No speech]")
            
            # Empty line between subtitles
            srt_content.append("")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
        
        return output_path
        
    except Exception as e:
        if isinstance(e, SubtitleGenerationError):
            raise
        
        error_msg = f"Failed to generate SRT file: {str(e)}"
        raise SubtitleGenerationError(error_msg) from e


def validate_srt_file(srt_path: str) -> bool:
    """
    Validate if an SRT file is properly formatted.
    
    Args:
        srt_path (str): Path to the SRT file.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic validation: check for subtitle number, timestamp, and text patterns
        # SRT format: number, timestamp line, text, empty line
        lines = content.strip().split('\n')
        
        if len(lines) < 3:
            return False
        
        # Check first subtitle structure
        # Line 1: should be a number
        if not lines[0].strip().isdigit():
            return False
        
        # Line 2: should be timestamp format
        timestamp_pattern = r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}'
        if not re.match(timestamp_pattern, lines[1].strip()):
            return False
        
        return True
        
    except Exception:
        return False


def get_subtitle_stats(srt_path: str) -> Dict[str, Any]:
    """
    Get statistics about a subtitle file.
    
    Args:
        srt_path (str): Path to the SRT file.
        
    Returns:
        Dict[str, Any]: Statistics including subtitle count, duration, etc.
    """
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count subtitles
        subtitle_count = content.count('\n\n') + 1 if content.strip() else 0
        
        # Extract timestamps to calculate duration
        timestamp_pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})'
        timestamps = re.findall(timestamp_pattern, content)
        
        total_duration = 0.0
        if timestamps:
            # Parse last end timestamp
            last_end = timestamps[-1][1]
            h, m, s_ms = last_end.split(':')
            s, ms = s_ms.split(',')
            total_duration = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        
        # Count total characters
        text_lines = [line for line in content.split('\n') 
                     if line.strip() and not line.strip().isdigit() 
                     and '-->' not in line]
        total_chars = sum(len(line) for line in text_lines)
        
        return {
            'subtitle_count': subtitle_count,
            'total_duration': total_duration,
            'total_characters': total_chars,
            'average_chars_per_subtitle': total_chars / subtitle_count if subtitle_count > 0 else 0
        }
        
    except Exception as e:
        raise SubtitleGenerationError(f"Failed to get subtitle stats: {str(e)}") from e
