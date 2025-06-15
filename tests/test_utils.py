"""
Tests for utils module.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock

from vid_subtitle.utils import (
    check_ffmpeg_installed,
    validate_video_format,
    validate_file_exists,
    get_openai_api_key,
    create_temp_file,
    cleanup_temp_file,
    get_output_srt_path,
    VidSubtitleError,
    FFmpegNotFoundError,
    InvalidVideoFormatError,
    OpenAIKeyNotFoundError
)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_validate_video_format(self):
        """Test video format validation."""
        # Valid formats
        self.assertTrue(validate_video_format("test.mp4"))
        self.assertTrue(validate_video_format("test.MP4"))
        self.assertTrue(validate_video_format("test.mov"))
        self.assertTrue(validate_video_format("test.MOV"))
        self.assertTrue(validate_video_format("/path/to/video.mp4"))
        
        # Invalid formats
        self.assertFalse(validate_video_format("test.avi"))
        self.assertFalse(validate_video_format("test.mkv"))
        self.assertFalse(validate_video_format("test.wmv"))
        self.assertFalse(validate_video_format("test.txt"))
        self.assertFalse(validate_video_format("test"))
    
    def test_validate_file_exists(self):
        """Test file existence validation."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            # File exists
            self.assertTrue(validate_file_exists(temp_path))
            
            # File doesn't exist
            self.assertFalse(validate_file_exists("nonexistent_file.txt"))
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-123'})
    def test_get_openai_api_key_success(self):
        """Test getting OpenAI API key when it exists."""
        key = get_openai_api_key()
        self.assertEqual(key, 'test-key-123')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_openai_api_key_missing(self):
        """Test getting OpenAI API key when it's missing."""
        with self.assertRaises(OpenAIKeyNotFoundError):
            get_openai_api_key()
    
    def test_create_and_cleanup_temp_file(self):
        """Test temporary file creation and cleanup."""
        # Create temp file
        temp_path = create_temp_file(suffix='.wav')
        
        # File should exist
        self.assertTrue(os.path.exists(temp_path))
        self.assertTrue(temp_path.endswith('.wav'))
        
        # Clean up
        cleanup_temp_file(temp_path)
        
        # File should be gone
        self.assertFalse(os.path.exists(temp_path))
    
    def test_cleanup_nonexistent_file(self):
        """Test cleanup of nonexistent file (should not raise error)."""
        # This should not raise an exception
        cleanup_temp_file("nonexistent_file.tmp")
    
    def test_get_output_srt_path(self):
        """Test SRT output path generation."""
        # Test with MP4
        srt_path = get_output_srt_path("video.mp4")
        self.assertEqual(srt_path, "video.srt")
        
        # Test with MOV
        srt_path = get_output_srt_path("video.mov")
        self.assertEqual(srt_path, "video.srt")
        
        # Test with path
        srt_path = get_output_srt_path("/path/to/video.mp4")
        self.assertEqual(srt_path, "/path/to/video.srt")
    
    @patch('vid_subtitle.utils.subprocess.run')
    def test_check_ffmpeg_installed_success(self, mock_run):
        """Test FFmpeg check when it's installed."""
        mock_run.return_value = MagicMock()
        result = check_ffmpeg_installed()
        self.assertTrue(result)
        mock_run.assert_called_once()
    
    @patch('vid_subtitle.utils.subprocess.run')
    def test_check_ffmpeg_installed_failure(self, mock_run):
        """Test FFmpeg check when it's not installed."""
        mock_run.side_effect = FileNotFoundError()
        result = check_ffmpeg_installed()
        self.assertFalse(result)


class TestExceptions(unittest.TestCase):
    """Test custom exceptions."""
    
    def test_exception_hierarchy(self):
        """Test that custom exceptions inherit from VidSubtitleError."""
        self.assertTrue(issubclass(FFmpegNotFoundError, VidSubtitleError))
        self.assertTrue(issubclass(InvalidVideoFormatError, VidSubtitleError))
        self.assertTrue(issubclass(OpenAIKeyNotFoundError, VidSubtitleError))
    
    def test_exception_messages(self):
        """Test exception messages."""
        with self.assertRaises(FFmpegNotFoundError) as cm:
            raise FFmpegNotFoundError("FFmpeg not found")
        self.assertEqual(str(cm.exception), "FFmpeg not found")
        
        with self.assertRaises(InvalidVideoFormatError) as cm:
            raise InvalidVideoFormatError("Invalid format")
        self.assertEqual(str(cm.exception), "Invalid format")
        
        with self.assertRaises(OpenAIKeyNotFoundError) as cm:
            raise OpenAIKeyNotFoundError("API key missing")
        self.assertEqual(str(cm.exception), "API key missing")


if __name__ == '__main__':
    unittest.main()
