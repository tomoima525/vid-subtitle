# vid-subtitle

A Python library to add subtitles to videos using FFmpeg and OpenAI Whisper API.



https://github.com/user-attachments/assets/7c2d0a6a-7d75-4837-b141-097104a0cb5e



## Features

- Extract audio from MP4 and MOV video files
- Transcribe audio using OpenAI Whisper API
- Generate SRT subtitle files
- Embed subtitles into video files
- Support for multiple languages (English by default)

## Prerequisites

- Python 3.7+
- FFmpeg installed on your system
- OpenAI API key

## Installation

```bash
pip install vid-subtitle
```

## Setup

1. Install FFmpeg on your system:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
   - **Windows**: Download from [FFmpeg official website](https://ffmpeg.org/download.html)

2. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   or create a `.env` file in the root directory and add the following:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### Basic Usage

```python
from vid_subtitle import add_subtitles

# Add subtitles to a video
add_subtitles(
    input_video="input.mp4",
    output_video="output_with_subtitles.mp4",
    language="en"  # Optional, defaults to English
)
```

This will:
1. Extract audio from the input video
2. Transcribe the audio using OpenAI Whisper API
3. Generate an SRT subtitle file
4. Create a new video with embedded subtitless

### CLI Usage

```bash
vid-subtitle add -l en -v  input.mp4 output.mp4 
```

### Supported Languages

The library supports all languages supported by OpenAI Whisper API. Use ISO 639-1 language codes:

- `en` - English (default)
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese
- And many more...

### Supported Video Formats

- MP4 (.mp4)
- MOV (.mov)

## Output Files

The library generates two outputs:
1. **Video file with embedded subtitles**: `{output_video}`
2. **Separate SRT subtitle file**: `{input_video_name}.srt`

## Error Handling

The library includes comprehensive error handling for:
- Missing FFmpeg installation
- Invalid video formats
- Missing OpenAI API key
- Network connectivity issues
- File permission errors

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
