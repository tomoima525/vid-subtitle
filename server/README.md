# MCP Video Subtitle Server

A Model Context Protocol (MCP) server that provides video subtitle processing and secure local file access through resources and tools, with root-based security boundaries.

## Features

### Video Subtitle Processing

- **Complete Subtitle Workflow**: Extract audio, transcribe using OpenAI Whisper, generate SRT files, and embed subtitles
- **Extract Subtitles Only**: Generate SRT files without creating new video files
- **Add Existing Subtitles**: Embed existing SRT files into videos
- **Refine Subtitles**: Improve subtitle quality using OpenAI API
- **Multi-language Support**: Support for 90+ languages via OpenAI Whisper
- **Secure Processing**: All operations respect root directory boundaries

### File Access

- **Secure File Access**: Root-based directory boundaries prevent unauthorized access
- **File Operations**: Read, write, list, search files and directories
- **Resource Exposure**: Files available as MCP resources with `file://` URIs
- **Binary Support**: Automatic handling of binary files with base64 encoding

## Installation

### Prerequisites

1. **FFmpeg**: Required for video processing

   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

2. **OpenAI API Key**: Required for transcription and subtitle refinement
   - Get your API key from [OpenAI](https://platform.openai.com/api-keys)
   - Set the environment variable: `export OPENAI_API_KEY=your_api_key_here`

### Server Installation

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure the server by editing `config.json` (see Configuration section below) to set your:

   - Allowed root directories
   - Video processing settings
   - OpenAI configuration

   ```bash
   cp config.example.json config.json
   ```

## Usage

### Basic Usage

```bash
python run_server.py
```

### With Custom Configuration

```bash
python run_server.py /path/to/custom/config.json
```

### Direct Server Usage

```bash
python server.py config.json
```

## Claude Desktop Integration

To use this MCP video subtitle server with Claude Desktop app, you need to configure it in Claude Desktop's settings.

### Step 1: Locate Configuration File

Find your Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Step 2: Add MCP Server Configuration

Look for which python executable can be used by Claude Desktop:

```bash
which python3
/path/to/python3
# You see something like /Users/tomoima525/.pyenv/shims/python3
```

Open the `claude_desktop_config.json` file and add your MCP server under the `mcpServers` section:

```json
{
  "mcpServers": {
    "vid-subtitle": {
      "command": "/path/to/python3",
      "args": ["/path/to/vid-subtitle/server/run_server.py"],
      "env": {}
    }
  }
}
```

Or with a custom config file:

```json
{
  "mcpServers": {
    "vid-subtitle": {
      "command": "/path/to/python3",
      "args": [
        "/path/to/vid-subtitle/server/run_server.py",
        "/path/to/your/config.json"
      ],
      "env": {}
    }
  }
}
```

**Important**: Replace the paths with the actual absolute paths to your server files.

### Step 3: Restart Claude Desktop

1. Completely quit Claude Desktop (not just close the window)
2. Start Claude Desktop again
3. The MCP server will automatically start when Claude Desktop launches

### Step 4: Verify Connection

Once connected, you should see:

- The server listed in Claude's MCP servers
- Available tools: `read_file`, `write_file`, `list_directory`, `search_files`, `get_file_info`
- File resources from your configured root directories

### Step 5: Using the Server

You can now ask Claude to interact with your files and process videos:

#### File Operations

```
"List files in the project workspace"
"Read the package.json file"
"Search for Python files containing 'async'"
"Write a new README to the docs folder"
```

#### Video Subtitle Operations

```
"Add English subtitles to presentation.mp4 and save as presentation_with_subs.mp4"
"Extract subtitles from lecture.mov and save as lecture.srt"
"Add the existing subtitles.srt file to movie.mp4 and create movie_final.mp4"
"Refine the subtitles in rough_subs.srt to improve grammar and save as polished_subs.srt"
"What languages are supported for video transcription?"
```

### Troubleshooting

#### Server Connection Issues

If the server doesn't connect:

1. **Check paths**: Ensure Python executable and script paths are correct and absolute
2. **Install dependencies**: Run `pip install -r requirements.txt` in the server directory
3. **Verify config**: Make sure your `config.json` has valid root directories
4. **Check logs**: Enable Claude Desktop's developer console for error messages
5. **Test manually**: Try running `python run_server.py` to test the server independently

#### Video Subtitle Issues

If video processing fails:

1. **FFmpeg**: Ensure FFmpeg is installed and available in PATH (`ffmpeg -version`)
2. **OpenAI API Key**: Verify your `OPENAI_API_KEY` environment variable is set
3. **File formats**: Only MP4 and MOV video files are supported
4. **File paths**: Ensure video files are within configured root directories
5. **File size**: Check video file size doesn't exceed configured limits
6. **Permissions**: Verify read/write access to input/output directories

### Transport Details

The server uses **stdio transport** for Claude Desktop integration:

- Communication through stdin/stdout
- Automatic startup/shutdown with Claude Desktop
- No network ports required
- Secure subprocess communication

## Configuration

Edit `config.json` to customize:

- **Roots**: Directories the server can access
- **Security**: File size limits, allowed/denied extensions
- **Features**: Enable/disable specific operations
- **Performance**: Caching and optimization settings

Example configuration:

```json
{
  "roots": [
    {
      "uri": "file:///home/user/workspace",
      "name": "Workspace",
      "description": "Main development directory"
    }
  ],
  "security": {
    "max_file_size": 10485760,
    "denied_extensions": [".key", ".pem", ".env"]
  }
}
```

## Available Tools

### File Operations

- **read_file**: Read file contents
- **write_file**: Write content to files
- **list_directory**: List directory contents
- **search_files**: Search by filename or content
- **get_file_info**: Get file metadata

### Video Subtitle Tools

- **add_subtitles**: Complete video subtitle workflow (extract audio → transcribe → generate SRT → embed subtitles)
- **extract_subtitles_only**: Extract subtitles from video without creating new video file
- **add_subtitle_file**: Embed existing SRT subtitle file into video
- **refine_subtitles**: Improve existing subtitles using OpenAI API
- **get_supported_languages**: Get list of supported transcription languages (90+ languages)

## Available Resources

All files within configured root directories are exposed as resources with `file://` URIs.
