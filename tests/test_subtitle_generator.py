"""
Tests for subtitle_generator module.
"""

import unittest
import tempfile
import os

from vid_subtitle.subtitle_generator import (
    format_timestamp,
    clean_text,
    split_long_segments,
    generate_srt,
    validate_srt_file,
    get_subtitle_stats,
    SubtitleGenerationError
)


class TestSubtitleGenerator(unittest.TestCase):
    """Test cases for subtitle generation functions."""
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        # Test various timestamps
        self.assertEqual(format_timestamp(0), "00:00:00,000")
        self.assertEqual(format_timestamp(1.5), "00:00:01,500")
        self.assertEqual(format_timestamp(61.25), "00:01:01,250")
        self.assertEqual(format_timestamp(3661.75), "01:01:01,750")
        self.assertEqual(format_timestamp(3600), "01:00:00,000")
    
    def test_clean_text(self):
        """Test text cleaning."""
        # Test basic cleaning
        self.assertEqual(clean_text("  Hello   world  "), "Hello world")
        self.assertEqual(clean_text("Hello\nworld"), "Hello world")
        self.assertEqual(clean_text("Hello\rworld"), "Hello world")
        
        # Test long text splitting
        long_text = "This is a very long sentence that should be split into multiple lines for better readability in subtitles."
        cleaned = clean_text(long_text)
        self.assertIn('\n', cleaned)  # Should contain line break
        lines = cleaned.split('\n')
        self.assertLessEqual(len(lines), 2)  # Max 2 lines
        for line in lines:
            self.assertLessEqual(len(line), 40)  # Max 40 chars per line
    
    def test_split_long_segments(self):
        """Test splitting of long segments."""
        # Short segment (should not be split)
        short_segments = [{
            'id': 0,
            'start': 0.0,
            'end': 3.0,
            'text': 'Short text'
        }]
        result = split_long_segments(short_segments, max_duration=5.0)
        self.assertEqual(len(result), 1)
        
        # Long segment (should be split)
        long_segments = [{
            'id': 0,
            'start': 0.0,
            'end': 10.0,
            'text': 'This is a very long segment that should be split into multiple parts'
        }]
        result = split_long_segments(long_segments, max_duration=5.0)
        self.assertGreater(len(result), 1)
        
        # Check that all resulting segments are within duration limit
        for segment in result:
            duration = segment['end'] - segment['start']
            self.assertLessEqual(duration, 5.5)  # Allow small tolerance
    
    def test_generate_srt(self):
        """Test SRT file generation."""
        # Sample transcription data
        transcription = {
            'text': 'Hello world. This is a test.',
            'segments': [
                {
                    'id': 0,
                    'start': 0.0,
                    'end': 2.0,
                    'text': 'Hello world.'
                },
                {
                    'id': 1,
                    'start': 2.5,
                    'end': 4.5,
                    'text': 'This is a test.'
                }
            ]
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Generate SRT
            result_path = generate_srt(transcription, temp_path)
            self.assertEqual(result_path, temp_path)
            
            # Check file exists and has content
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check SRT format
            self.assertIn('1\n', content)  # Subtitle number
            self.assertIn('00:00:00,000 --> 00:00:02,000', content)  # Timestamp
            self.assertIn('Hello world.', content)  # Text
            self.assertIn('2\n', content)  # Second subtitle
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_generate_srt_no_segments(self):
        """Test SRT generation with no segments."""
        transcription = {'text': 'Hello', 'segments': []}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with self.assertRaises(SubtitleGenerationError):
                generate_srt(transcription, temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_srt_file(self):
        """Test SRT file validation."""
        # Create valid SRT content
        valid_srt = """1
00:00:00,000 --> 00:00:02,000
Hello world

2
00:00:02,500 --> 00:00:04,500
This is a test

"""
        
        # Create temporary file with valid content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as temp_file:
            temp_file.write(valid_srt)
            temp_path = temp_file.name
        
        try:
            # Should be valid
            self.assertTrue(validate_srt_file(temp_path))
        finally:
            os.unlink(temp_path)
        
        # Test invalid SRT
        invalid_srt = "This is not a valid SRT file"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as temp_file:
            temp_file.write(invalid_srt)
            temp_path = temp_file.name
        
        try:
            # Should be invalid
            self.assertFalse(validate_srt_file(temp_path))
        finally:
            os.unlink(temp_path)
        
        # Test nonexistent file
        self.assertFalse(validate_srt_file("nonexistent.srt"))
    
    def test_get_subtitle_stats(self):
        """Test subtitle statistics."""
        # Create SRT content
        srt_content = """1
00:00:00,000 --> 00:00:02,000
Hello world

2
00:00:02,500 --> 00:00:04,500
This is a test

"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as temp_file:
            temp_file.write(srt_content)
            temp_path = temp_file.name
        
        try:
            stats = get_subtitle_stats(temp_path)
            
            # Check stats
            self.assertEqual(stats['subtitle_count'], 2)
            self.assertEqual(stats['total_duration'], 4.5)
            self.assertGreater(stats['total_characters'], 0)
            self.assertGreater(stats['average_chars_per_subtitle'], 0)
            
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
