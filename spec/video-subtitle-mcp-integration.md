# Video Subtitle MCP Integration Plan

## Overview
This document outlines the integration of video subtitle functionality from `vid_subtitle/core.py` into the existing MCP server to create a comprehensive video subtitle processing service accessible via the Model Context Protocol.

## Goals
- Expose video subtitle generation and processing capabilities as MCP tools
- Maintain existing file access security model
- Enable Claude Desktop and other MCP clients to process video subtitles
- Provide a unified interface for both file operations and video processing

## Architecture Changes

### 1. Server Identity Update
- **Current**: "file-server" - Generic file access server
- **New**: "vid-subtitle" - Video subtitle processing server with file access
- **Rationale**: Better reflects the primary use case and capabilities

### 2. Tool Additions
The server will expose the following new MCP tools:

#### `add_subtitles`
**Purpose**: Complete video subtitle workflow - extract audio, transcribe, generate SRT, and embed subtitles

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "input_video": {
      "type": "string",
      "description": "Path to input video file (MP4 or MOV)"
    },
    "output_video": {
      "type": "string", 
      "description": "Path for output video with embedded subtitles"
    },
    "language": {
      "type": "string",
      "description": "Language code for transcription",
      "default": "en"
    },
    "verbose": {
      "type": "boolean",
      "description": "Show detailed progress information",
      "default": false
    }
  },
  "required": ["input_video", "output_video"]
}
```

**Output**: JSON object with SRT file path, output video path, transcription cost, processing time, subtitle statistics, and video information.

#### `extract_subtitles_only`
**Purpose**: Extract subtitles from video without creating new video file

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "input_video": {
      "type": "string",
      "description": "Path to input video file"
    },
    "output_srt": {
      "type": "string",
      "description": "Optional path for output SRT file"
    },
    "language": {
      "type": "string", 
      "description": "Language code for transcription",
      "default": "en"
    },
    "verbose": {
      "type": "boolean",
      "description": "Show progress information",
      "default": false
    }
  },
  "required": ["input_video"]
}
```

**Output**: JSON object with SRT file path, transcription cost, subtitle statistics.

#### `add_subtitle_file`
**Purpose**: Embed existing SRT subtitle file into video

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "input_video": {
      "type": "string",
      "description": "Path to input video file"
    },
    "subtitle_file": {
      "type": "string",
      "description": "Path to SRT subtitle file"
    },
    "output_video": {
      "type": "string",
      "description": "Path for output video with embedded subtitles"
    },
    "verbose": {
      "type": "boolean",
      "description": "Show progress information", 
      "default": false
    }
  },
  "required": ["input_video", "subtitle_file", "output_video"]
}
```

**Output**: JSON object with output video path, processing time, video information.

#### `refine_subtitles`
**Purpose**: Refine existing subtitles using OpenAI API

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "subtitle_file": {
      "type": "string",
      "description": "Path to input SRT subtitle file"
    },
    "output_subtitle_file": {
      "type": "string",
      "description": "Path for refined output SRT file"
    },
    "instruction": {
      "type": "string",
      "description": "Instructions for refining subtitles"
    },
    "verbose": {
      "type": "boolean",
      "description": "Show progress information",
      "default": false
    }
  },
  "required": ["subtitle_file", "output_subtitle_file", "instruction"]
}
```

**Output**: JSON object with refined subtitle file path.

#### `get_supported_languages`
**Purpose**: Get list of supported transcription languages

**Input Schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output**: JSON array of ISO 639-1 language codes.

### 3. Configuration Updates

#### Server Configuration
```json
{
  "server": {
    "name": "vid-subtitle",
    "version": "1.0.0", 
    "description": "MCP server for video subtitle processing and file access"
  },
  "video_processing": {
    "max_video_size": 1073741824,
    "supported_video_formats": [".mp4", ".mov"],
    "supported_subtitle_formats": [".srt"],
    "temp_directory": "/tmp/vid-subtitle",
    "cleanup_temp_files": true,
    "ffmpeg_timeout": 3600
  },
  "openai": {
    "model": "whisper-1",
    "api_key_env_var": "OPENAI_API_KEY",
    "max_retries": 3
  }
}
```

#### Security Enhancements
- All video and subtitle file paths must be within configured roots
- Maximum video file size limits (default: 1GB)
- Temporary file cleanup after processing
- API key security via environment variables

## Implementation Approach

### 1. Direct Import Strategy
Use direct imports from `vid_subtitle` package to minimize code duplication:

```python
# Add to Python path
import sys
sys.path.append('/Users/tomoima525/workspace/imai/vid-subtitle')

# Import functions
from vid_subtitle.core import (
    add_subtitles,
    extract_subtitles_only, 
    add_subtitle_file,
    refine_subtitles,
    get_supported_languages
)
```

### 2. Error Handling Strategy
- Wrap all `VidSubtitleError` exceptions as MCP tool errors
- Provide clear error messages for common issues:
  - Missing FFmpeg installation
  - Missing OpenAI API key
  - Invalid video formats
  - File access permissions
  - Insufficient disk space

### 3. Progress Reporting
- Use `verbose` parameter to control progress output
- Stream progress information to MCP client when requested
- Provide cost estimates before processing

## Security Model

### Path Security
- **Input Validation**: All file paths validated against configured roots
- **Output Validation**: All output paths must be within allowed roots  
- **Temporary Files**: Created in secure temporary directory, cleaned up after use
- **File Extension Validation**: Only supported video/subtitle formats allowed

### API Key Management
- OpenAI API key stored in environment variables
- Never logged or returned in responses
- Validate key availability before processing

### Resource Limits
- Maximum video file size enforcement
- Processing timeout limits
- Concurrent operation limits

## Dependencies

### New Requirements
```
openai>=1.95.1
python-dotenv>=0.19.0
```

### System Requirements
- FFmpeg installation (for video processing)
- OpenAI API key (for transcription and refinement)
- Sufficient disk space for temporary files

## Error Scenarios and Handling

### 1. Missing Dependencies
- **FFmpeg not installed**: Clear error message with installation instructions
- **OpenAI API key missing**: Error message pointing to configuration

### 2. File Access Issues
- **Input file not found**: File not found error with path validation
- **Permission denied**: Clear permission error message
- **File outside roots**: Security error with allowed paths

### 3. Processing Errors
- **Video format unsupported**: List of supported formats
- **Transcription API failure**: Retry mechanism with exponential backoff
- **Insufficient disk space**: Clear error message

### 4. Invalid Parameters
- **Invalid language code**: List of supported languages
- **Invalid file paths**: Path validation errors
- **Missing required parameters**: Parameter validation errors

## Usage Examples

### Example 1: Complete Subtitle Workflow
```python
# Claude Desktop usage
"Use the add_subtitles tool to add English subtitles to video.mp4 and save as video_with_subtitles.mp4"
```

### Example 2: Extract Subtitles Only  
```python
"Extract subtitles from presentation.mp4 and save as presentation.srt"
```

### Example 3: Add Existing Subtitles
```python
"Add the existing subtitles.srt file to movie.mp4 and create movie_final.mp4"
```

### Example 4: Refine Subtitles
```python
"Refine the subtitles in rough_subtitles.srt to fix grammar and save as polished_subtitles.srt"
```

## Testing Strategy

### Unit Tests
- Test each tool with valid inputs
- Test error handling for invalid inputs
- Test path security validation
- Test API key validation

### Integration Tests  
- End-to-end video processing workflows
- Claude Desktop integration testing
- Performance testing with large video files
- Concurrent operation testing

### Security Tests
- Path traversal attack prevention
- File access permission validation
- API key security validation

## Future Enhancements

### Potential Features
1. **Batch Processing**: Process multiple videos in one operation
2. **Format Conversion**: Support additional video and subtitle formats  
3. **Translation**: Translate subtitles between languages
4. **Synchronization**: Adjust subtitle timing
5. **Styling**: Custom subtitle appearance options
6. **Preview**: Generate subtitle preview without full processing

### Performance Optimizations
1. **Caching**: Cache transcription results
2. **Parallel Processing**: Process multiple files concurrently
3. **Streaming**: Stream processing for large files
4. **Compression**: Compress temporary files

This integration plan provides a comprehensive approach to adding video subtitle capabilities to the MCP server while maintaining security, usability, and maintainability.