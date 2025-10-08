#!/usr/bin/env python3
"""
MCP File Server Implementation

A Model Context Protocol server that provides secure local file access
through resources and tools, with root-based security boundaries.
"""

import asyncio
import json
import os
import pathlib
import signal
from dataclasses import dataclass
from typing import Dict, List
import mimetypes
import base64
import glob
import sys

import mcp.types as types
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server


@dataclass
class Root:
    """Represents a root directory boundary for file access."""

    uri: str
    name: str
    path: str


class SecurityError(Exception):
    """Raised when a security boundary is violated."""

    pass


class FileServer:
    """MCP Server for secure file system access."""

    def __init__(self):
        self.server = Server("vid-subtitle")
        self.roots: List[Root] = []
        self.max_file_size = 100 * 1024 * 1024  # 100MB default
        self.max_directory_depth = 10
        self.denied_extensions = {".key", ".pem", ".p12", ".pfx", ".env", ".secret"}
        self.transport_config = {"type": "stdio"}  # Default transport config

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP handlers for resources and tools."""

        # Resource handlers
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List all available file resources."""
            resources = []

            for root in self.roots:
                # Add root directory as resource
                resources.append(
                    types.Resource(
                        uri=f"file://{root.path}",
                        name=f"{root.name} (Directory)",
                        description=f"Directory: {root.path}",
                        mimeType="inode/directory",
                    )
                )

                # Add files in root as resources
                try:
                    for file_path in self._list_files_recursive(root.path):
                        if self._is_allowed_file(file_path):
                            rel_path = os.path.relpath(file_path, root.path)
                            resources.append(
                                types.Resource(
                                    uri=f"file://{file_path}",
                                    name=rel_path,
                                    description=f"File: {file_path}",
                                    mimeType=mimetypes.guess_type(file_path)[0]
                                    or "application/octet-stream",
                                )
                            )
                except (OSError, PermissionError):
                    continue

            return resources

        @self.server.read_resource()
        async def handle_read_resource(uri: types.AnyUrl) -> str:
            """Read a file resource by URI."""
            if not str(uri).startswith("file://"):
                raise ValueError("Only file:// URIs are supported")

            # Extract path from URI
            file_path = str(uri)[7:]  # Remove "file://" prefix
            validated_path = self._validate_path(file_path)

            return await self._read_file_content(validated_path)

        # Tool handlers
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available file operation tools."""
            return [
                types.Tool(
                    name="read_file",
                    description="Read the contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to read",
                            }
                        },
                        "required": ["path"],
                    },
                ),
                types.Tool(
                    name="write_file",
                    description="Write content to a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to write",
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file",
                            },
                            "encoding": {
                                "type": "string",
                                "description": "File encoding",
                                "default": "utf-8",
                            },
                        },
                        "required": ["path", "content"],
                    },
                ),
                types.Tool(
                    name="list_directory",
                    description="List contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path to list",
                            },
                            "include_hidden": {
                                "type": "boolean",
                                "description": "Include hidden files",
                                "default": False,
                            },
                        },
                        "required": ["path"],
                    },
                ),
                types.Tool(
                    name="search_files",
                    description="Search for files by name or content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "path": {
                                "type": "string",
                                "description": "Root path for search",
                                "default": ".",
                            },
                            "content_search": {
                                "type": "boolean",
                                "description": "Search file contents",
                                "default": False,
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum results",
                                "default": 100,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                types.Tool(
                    name="get_file_info",
                    description="Get information about a file or directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file or directory",
                            }
                        },
                        "required": ["path"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict
        ) -> list[types.TextContent]:
            """Handle tool calls for file operations."""

            if name == "read_file":
                return await self._tool_read_file(arguments)
            elif name == "write_file":
                return await self._tool_write_file(arguments)
            elif name == "list_directory":
                return await self._tool_list_directory(arguments)
            elif name == "search_files":
                return await self._tool_search_files(arguments)
            elif name == "get_file_info":
                return await self._tool_get_file_info(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        # Note: Notifications in MCP Python SDK should be sent from within tools
        # using ctx.session.send_resource_list_changed() or similar methods


    def _validate_path(self, path: str) -> str:
        """Validate path against root boundaries."""
        if not self.roots:
            raise SecurityError("No root directories configured")

        # Normalize path to prevent traversal attacks
        normalized_path = os.path.normpath(path)

        # Convert to absolute path
        if not os.path.isabs(normalized_path):
            # Try to resolve against each root
            for root in self.roots:
                candidate_path = os.path.join(root.path, normalized_path)
                candidate_path = os.path.normpath(candidate_path)

                if self._is_path_within_root(candidate_path, root.path):
                    return candidate_path
        else:
            # Check if absolute path is within any root
            for root in self.roots:
                if self._is_path_within_root(normalized_path, root.path):
                    return normalized_path

        raise SecurityError(f"Path '{path}' is outside allowed root directories")

    def _is_path_within_root(self, path: str, root_path: str) -> bool:
        """Check if path is within root directory."""
        try:
            # Convert to pathlib for reliable comparison
            path_obj = pathlib.Path(path).resolve()
            root_obj = pathlib.Path(root_path).resolve()

            # Check if path is relative to root
            return str(path_obj).startswith(str(root_obj))
        except (OSError, ValueError):
            return False

    def _is_allowed_file(self, file_path: str) -> bool:
        """Check if file extension is allowed."""
        _, ext = os.path.splitext(file_path.lower())
        return ext not in self.denied_extensions

    def _list_files_recursive(self, directory: str, max_depth: int = None) -> List[str]:
        """Recursively list files in directory with depth limit."""
        if max_depth is None:
            max_depth = self.max_directory_depth

        files = []

        def _walk(current_dir: str, current_depth: int):
            if current_depth > max_depth:
                return

            try:
                for entry in os.listdir(current_dir):
                    if entry.startswith("."):
                        continue

                    entry_path = os.path.join(current_dir, entry)

                    if os.path.isfile(entry_path):
                        files.append(entry_path)
                    elif os.path.isdir(entry_path):
                        _walk(entry_path, current_depth + 1)
            except (OSError, PermissionError):
                pass

        _walk(directory, 0)
        return files

    async def _read_file_content(self, file_path: str) -> str:
        """Read file content with binary detection."""
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError(
                    f"File too large: {file_size} bytes (max: {self.max_file_size})"
                )

            # Try to read as text first
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                # If text fails, read as binary and encode as base64
                with open(file_path, "rb") as f:
                    binary_content = f.read()
                    return f"data:application/octet-stream;base64,{base64.b64encode(binary_content).decode()}"

        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied: {file_path}")

    # Tool implementation methods
    async def _tool_read_file(self, arguments: dict) -> list[types.TextContent]:
        """Read file tool implementation."""
        path = arguments["path"]
        validated_path = self._validate_path(path)

        if not self._is_allowed_file(validated_path):
            raise SecurityError(f"File type not allowed: {path}")

        content = await self._read_file_content(validated_path)

        return [types.TextContent(type="text", text=content)]

    async def _tool_write_file(self, arguments: dict) -> list[types.TextContent]:
        """Write file tool implementation."""
        path = arguments["path"]
        content = arguments["content"]
        encoding = arguments.get("encoding", "utf-8")

        validated_path = self._validate_path(path)

        if not self._is_allowed_file(validated_path):
            raise SecurityError(f"File type not allowed: {path}")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(validated_path), exist_ok=True)

        try:
            with open(validated_path, "w", encoding=encoding) as f:
                f.write(content)

            return [
                types.TextContent(
                    type="text", text=f"File written successfully: {validated_path}"
                )
            ]

        except Exception as e:
            raise RuntimeError(f"Failed to write file: {e}")

    async def _tool_list_directory(self, arguments: dict) -> list[types.TextContent]:
        """List directory tool implementation."""
        path = arguments["path"]
        include_hidden = arguments.get("include_hidden", False)

        validated_path = self._validate_path(path)

        if not os.path.isdir(validated_path):
            raise ValueError(f"Path is not a directory: {validated_path}")

        try:
            entries = []
            for entry in os.listdir(validated_path):
                if not include_hidden and entry.startswith("."):
                    continue

                entry_path = os.path.join(validated_path, entry)
                stat = os.stat(entry_path)

                entry_info = {
                    "name": entry,
                    "path": entry_path,
                    "type": "directory" if os.path.isdir(entry_path) else "file",
                    "size": stat.st_size if os.path.isfile(entry_path) else None,
                    "modified": stat.st_mtime,
                    "permissions": oct(stat.st_mode)[-3:],
                }
                entries.append(entry_info)

            return [types.TextContent(type="text", text=json.dumps(entries, indent=2))]

        except Exception as e:
            raise RuntimeError(f"Failed to list directory: {e}")

    async def _tool_search_files(self, arguments: dict) -> list[types.TextContent]:
        """Search files tool implementation."""
        query = arguments["query"]
        search_path = arguments.get("path", ".")
        content_search = arguments.get("content_search", False)
        max_results = arguments.get("max_results", 100)

        validated_path = self._validate_path(search_path)
        results = []

        try:
            # Name-based search using glob
            pattern = f"*{query}*"
            for root in self.roots:
                if self._is_path_within_root(validated_path, root.path):
                    search_pattern = os.path.join(validated_path, "**", pattern)

                    for match in glob.glob(search_pattern, recursive=True):
                        if len(results) >= max_results:
                            break

                        if os.path.isfile(match) and self._is_allowed_file(match):
                            results.append(
                                {
                                    "path": match,
                                    "type": "name_match",
                                    "context": os.path.basename(match),
                                }
                            )

            # Content-based search if requested
            if content_search and len(results) < max_results:
                for root in self.roots:
                    if self._is_path_within_root(validated_path, root.path):
                        for file_path in self._list_files_recursive(validated_path):
                            if len(results) >= max_results:
                                break

                            if not self._is_allowed_file(file_path):
                                continue

                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content = f.read()
                                    if query.lower() in content.lower():
                                        # Find context around match
                                        lines = content.split("\n")
                                        for i, line in enumerate(lines):
                                            if query.lower() in line.lower():
                                                context_lines = lines[
                                                    max(0, i - 1) : i + 2
                                                ]
                                                results.append(
                                                    {
                                                        "path": file_path,
                                                        "type": "content_match",
                                                        "line": i + 1,
                                                        "context": "\n".join(
                                                            context_lines
                                                        ),
                                                    }
                                                )
                                                break
                            except (UnicodeDecodeError, PermissionError):
                                continue

            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")

    async def _tool_get_file_info(self, arguments: dict) -> list[types.TextContent]:
        """Get file info tool implementation."""
        path = arguments["path"]
        validated_path = self._validate_path(path)

        try:
            stat = os.stat(validated_path)

            info = {
                "path": validated_path,
                "name": os.path.basename(validated_path),
                "type": "directory" if os.path.isdir(validated_path) else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "created": stat.st_ctime,
                "permissions": oct(stat.st_mode)[-3:],
                "mode": stat.st_mode,
                "exists": True,
            }

            if os.path.isfile(validated_path):
                info["mime_type"] = mimetypes.guess_type(validated_path)[0]
                info["allowed"] = self._is_allowed_file(validated_path)

            return [types.TextContent(type="text", text=json.dumps(info, indent=2))]

        except FileNotFoundError:
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"exists": False, "path": validated_path}, indent=2
                    ),
                )
            ]
        except Exception as e:
            raise RuntimeError(f"Failed to get file info: {e}")

    def set_roots(self, roots: List[Dict[str, str]]):
        """Set root directories from client."""
        self.roots = []
        for root_data in roots:
            if root_data["uri"].startswith("file://"):
                path = root_data["uri"][7:]  # Remove "file://" prefix
                if os.path.exists(path) and os.path.isdir(path):
                    self.roots.append(
                        Root(
                            uri=root_data["uri"],
                            name=root_data.get("name", os.path.basename(path)),
                            path=os.path.abspath(path),
                        )
                    )

    def load_config(self, config_path: str):
        """Load configuration from file."""
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)

            # Set roots from config
            if "roots" in config:
                self.set_roots(config["roots"])

            # Set security settings
            security = config.get("security", {})
            self.max_file_size = security.get("max_file_size", 10485760)
            self.max_directory_depth = security.get("max_directory_depth", 10)

            denied_ext = security.get("denied_extensions", [])
            self.denied_extensions = set(denied_ext)

            # Store transport config for later use
            self.transport_config = config.get("transport", {"type": "stdio"})

    async def run(self, transport_type="stdio", host="localhost", port=3000):
        """Run the server with specified transport."""
        # Set default roots if none configured
        if not self.roots:
            current_dir = os.getcwd()
            self.set_roots(
                [{"uri": f"file://{current_dir}", "name": "Current Directory"}]
            )

        if transport_type == "stdio":
            await self._run_stdio()
        elif transport_type == "sse":
            await self._run_sse(host, port)
        else:
            raise ValueError(f"Unsupported transport type: {transport_type}")

    async def _run_stdio(self):
        """Run the server with stdio transport."""
        import os

        print("🚀 MCP File Server starting with STDIO transport")
        print(f"📍 Process ID: {os.getpid()}")
        print("📡 Transport: Standard Input/Output (stdio)")
        print("🔗 Communication: Server communicates through stdin/stdout")
        print(f"📁 Root directories: {len(self.roots)} configured")
        for root in self.roots:
            print(f"   - {root.name}: {root.path}")
        print("⚡ Server ready for MCP client connections via stdio")
        print("🔄 Press Ctrl+C to stop the server")


        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="vid-subtitle",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(
                                resources_changed=True,
                                tools_changed=True,
                            ),
                            experimental_capabilities={},
                        ),
                    ),
                )

        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
            print("📴 Server stopped gracefully")
        except Exception as e:
            print(f"❌ Server error: {e}")
            raise

    async def _run_sse(self, host="localhost", port=3000):
        """Run the server with Server-Sent Events (HTTP) transport."""
        import os
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        from sse_starlette import EventSourceResponse
        import uvicorn

        print("🚀 MCP File Server starting with SSE transport")
        print(f"📍 Process ID: {os.getpid()}")
        print("📡 Transport: Server-Sent Events (HTTP)")
        print(f"🌐 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"🔗 Connection URL: http://{host}:{port}/sse")
        print(f"📁 Root directories: {len(self.roots)} configured")
        for root in self.roots:
            print(f"   - {root.name}: {root.path}")
        print("⚡ Server ready for MCP client connections via HTTP")
        print("🔄 Press Ctrl+C to stop the server")


        # Create SSE endpoint
        async def handle_sse(request):
            async def event_stream():
                transport = SseServerTransport("/message")

                async with transport.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    await self.server.run(
                        streams[0],
                        streams[1],
                        InitializationOptions(
                            server_name="vid-subtitle",
                            server_version="1.0.0",
                            capabilities=self.server.get_capabilities(
                                notification_options=NotificationOptions(
                                    resources_changed=True,
                                    tools_changed=True,
                                ),
                                experimental_capabilities={},
                            ),
                        ),
                    )

            return EventSourceResponse(event_stream())

        # Create Starlette app
        app = Starlette(
            routes=[
                Route("/sse", handle_sse),
            ]
        )

        try:
            # Create and run uvicorn server
            config = uvicorn.Config(app, host=host, port=port, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()

        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
            print("📴 HTTP server stopped gracefully")
        except Exception as e:
            print(f"❌ Server error: {e}")
            raise


async def main():
    """Main entry point for the file server."""
    server = FileServer()

    # Configure from command line or config file
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        server.load_config(config_path)

    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
