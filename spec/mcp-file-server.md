# MCP File Server Specification

## Overview

This document specifies the implementation of a Model Context Protocol (MCP) server that provides secure local file access capabilities. The server exposes file system operations through MCP resources and tools while respecting security boundaries defined by roots.

## Architecture

### Core Components

1. **File Resources**: Expose files as MCP resources with `file://` URIs
2. **File Tools**: Provide file operations (read, write, list, search) as MCP tools
3. **Root Management**: Handle client-defined root directories for security
4. **Transport Layer**: Support both stdio and SSE transports

### Security Model

The server implements a security-first approach:
- **Roots**: Client-defined directories that bound server file access
- **Path Validation**: All file operations validate paths against allowed roots
- **Access Control**: No operations outside of root boundaries
- **Sanitization**: Input paths are sanitized to prevent directory traversal

## Implementation Details

### 1. Resources

#### File Resource Pattern
- URI Format: `file://{path}`
- Relative paths resolved against current root
- Absolute paths validated against root boundaries

#### Resource Handlers
```python
@mcp.resource("file://{path}")
async def read_file_resource(path: str) -> str:
    """Read a file as a resource."""
    validated_path = validate_path_against_roots(path)
    return await read_file(validated_path)
```

#### Dynamic Resource Discovery
- List available files within root directories
- Support glob patterns for resource enumeration
- Metadata inclusion (size, modified time, permissions)

### 2. Tools

#### Core File Operations

##### read_file
- **Purpose**: Read file contents
- **Parameters**: 
  - `path` (string): File path relative to root or absolute within root
- **Returns**: File contents as string or base64 for binary files
- **Security**: Validates path against roots before access

##### write_file
- **Purpose**: Write content to file
- **Parameters**:
  - `path` (string): Target file path
  - `content` (string): Content to write
  - `encoding` (optional): Text encoding (default: utf-8)
- **Returns**: Success confirmation
- **Security**: Creates files only within root boundaries

##### list_directory
- **Purpose**: List directory contents
- **Parameters**:
  - `path` (string): Directory path to list
  - `include_hidden` (boolean): Include hidden files
- **Returns**: Array of file/directory entries with metadata
- **Security**: Lists only within allowed root directories

##### search_files
- **Purpose**: Search for files by name or content
- **Parameters**:
  - `query` (string): Search query
  - `path` (optional): Search root path
  - `content_search` (boolean): Search file contents
- **Returns**: Matching files with context
- **Security**: Searches only within root boundaries

##### get_file_info
- **Purpose**: Get file metadata
- **Parameters**:
  - `path` (string): File path
- **Returns**: File stats (size, modified time, permissions, type)
- **Security**: Metadata access respects root boundaries

### 3. Root Management

#### Root Structure
```python
@dataclass
class Root:
    uri: str  # file:// URI
    name: str  # Human-readable name
    path: str  # Resolved filesystem path
```

#### Root Handling
- **Initialization**: Receive roots from client during handshake
- **Validation**: Ensure root paths exist and are accessible
- **Updates**: Handle `roots/list_changed` notifications
- **Path Resolution**: Resolve relative paths against appropriate roots

#### Security Validation
```python
def validate_path_against_roots(path: str, roots: List[Root]) -> str:
    """Validate and resolve path against allowed roots."""
    # Normalize path to prevent traversal attacks
    normalized = os.path.normpath(path)
    
    # Check if path is within any allowed root
    for root in roots:
        if is_path_within_root(normalized, root.path):
            return resolve_full_path(normalized, root.path)
    
    raise SecurityError(f"Path {path} is outside allowed roots")
```

### 4. Transport Configuration

#### stdio Transport (Default)
```python
async def run_stdio_server():
    """Run server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        server = create_file_server()
        await server.run(read_stream, write_stream)
```

#### SSE Transport (Optional)
```python
async def run_sse_server(host: str = "localhost", port: int = 3000):
    """Run server with SSE transport."""
    app = create_sse_app()
    server = create_file_server()
    await server.run_sse(app, host, port)
```

## Error Handling

### Error Types
1. **SecurityError**: Path outside root boundaries
2. **FileNotFoundError**: Requested file doesn't exist
3. **PermissionError**: Insufficient file system permissions
4. **ValidationError**: Invalid parameters or paths

### Error Response Format
```python
{
    "error": {
        "code": "SECURITY_ERROR",
        "message": "Path is outside allowed root directories",
        "details": {
            "path": "/etc/passwd",
            "allowed_roots": ["/home/user/workspace"]
        }
    }
}
```

## Configuration

### Server Configuration
```json
{
    "name": "file-server",
    "version": "1.0.0",
    "transport": {
        "type": "stdio",
        "sse": {
            "host": "localhost",
            "port": 3000
        }
    },
    "security": {
        "max_file_size": "10MB",
        "allowed_extensions": ["*"],
        "denied_extensions": [".key", ".pem"],
        "enable_content_search": true,
        "max_search_results": 100
    },
    "features": {
        "read_binary_files": true,
        "write_files": true,
        "create_directories": true,
        "delete_files": false
    }
}
```

### Default Roots
```json
{
    "default_roots": [
        {
            "uri": "file:///home/user/workspace",
            "name": "Workspace",
            "description": "Main development workspace"
        }
    ]
}
```

## Client Usage Examples

### Listing Resources
```python
# List all available file resources
resources = await client.list_resources()
for resource in resources:
    print(f"Resource: {resource.uri} - {resource.name}")
```

### Reading Files
```python
# Read file as resource
content = await client.read_resource("file://src/main.py")
print(content.contents)

# Read file using tool
result = await client.call_tool("read_file", {"path": "src/main.py"})
print(result.content)
```

### File Operations
```python
# List directory
files = await client.call_tool("list_directory", {
    "path": "src/",
    "include_hidden": False
})

# Search files
matches = await client.call_tool("search_files", {
    "query": "function main",
    "content_search": True
})

# Write file
await client.call_tool("write_file", {
    "path": "output.txt",
    "content": "Hello, MCP!"
})
```

## Security Considerations

### Best Practices
1. **Always validate paths** against root boundaries
2. **Sanitize inputs** to prevent injection attacks  
3. **Limit file sizes** to prevent resource exhaustion
4. **Restrict file types** based on use case requirements
5. **Log security events** for audit trails
6. **Implement rate limiting** for file operations

### Threat Mitigation
- **Directory Traversal**: Path normalization and root validation
- **Arbitrary File Access**: Strict root boundary enforcement
- **Resource Exhaustion**: File size limits and operation throttling
- **Information Disclosure**: Controlled error messages

## Implementation Checklist

- [ ] Core server setup with MCP Python SDK
- [ ] Resource handlers for file:// URIs
- [ ] Tool implementations for file operations
- [ ] Root management and path validation
- [ ] Security boundary enforcement
- [ ] Error handling and logging
- [ ] Configuration management
- [ ] Transport layer setup (stdio/SSE)
- [ ] Unit tests for security validation
- [ ] Integration tests with MCP client
- [ ] Documentation and examples

## Future Enhancements

1. **File Watching**: Real-time file change notifications
2. **Batch Operations**: Multiple file operations in single request
3. **Compression**: Automatic compression for large files
4. **Caching**: Intelligent file content caching
5. **Permissions**: Fine-grained file permission management
6. **Backup**: Automatic file backup before modifications