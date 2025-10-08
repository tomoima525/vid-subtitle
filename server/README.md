# MCP File Server

A Model Context Protocol (MCP) server that provides secure local file access through resources and tools, with root-based security boundaries.

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure the server by editing `config.json`(see below section) to set your allowed root directories.

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

To use this MCP file server with Claude Desktop app, you need to configure it in Claude Desktop's settings.

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

You can now ask Claude to interact with your files:

```
"List files in the project workspace"
"Read the package.json file"
"Search for Python files containing 'async'"
"Write a new README to the docs folder"
```

### Troubleshooting

If the server doesn't connect:

1. **Check paths**: Ensure Python executable and script paths are correct and absolute
2. **Install dependencies**: Run `pip install -r requirements.txt` in the server directory
3. **Verify config**: Make sure your `config.json` has valid root directories
4. **Check logs**: Enable Claude Desktop's developer console for error messages
5. **Test manually**: Try running `python run_server.py` to test the server independently

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

- **read_file**: Read file contents
- **write_file**: Write content to files
- **list_directory**: List directory contents
- **search_files**: Search by filename or content
- **get_file_info**: Get file metadata

## Available Resources

All files within configured root directories are exposed as resources with `file://` URIs.
