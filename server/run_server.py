#!/usr/bin/env python3
"""
MCP File Server Launcher

Simple script to start the MCP file server with configuration.
"""

from mcp_server import FileServer
import sys
import asyncio
from pathlib import Path

# Add the server directory to Python path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))


async def main():
    """Main launcher function."""
    # Default config path
    config_path = server_dir / "config.json"
    transport_override = None
    host_override = None
    port_override = None

    # Parse command line arguments
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--transport" and i + 1 < len(sys.argv):
            transport_override = sys.argv[i + 1]
            i += 2
        elif arg == "--host" and i + 1 < len(sys.argv):
            host_override = sys.argv[i + 1]
            i += 2
        elif arg == "--port" and i + 1 < len(sys.argv):
            port_override = int(sys.argv[i + 1])
            i += 2
        elif arg.startswith("--"):
            print(f"Unknown option: {arg}")
            print(
                "Usage: python run_server.py [config.json] [--transport stdio|sse] [--host localhost] [--port 3000]"
            )
            sys.exit(1)
        else:
            config_path = Path(arg)
            i += 1

    print("🎯 MCP File Server Launcher")
    print(f"📄 Config: {config_path}")

    server = FileServer()

    # Load configuration if file exists
    if config_path.exists():
        server.load_config(str(config_path))
        print(f"✅ Loaded configuration from {config_path}")
    else:
        print("⚠️  Using default configuration (current directory as root)")

    # Determine transport settings
    transport_config = getattr(server, "transport_config", {"type": "stdio"})
    transport_type = transport_override or transport_config.get("type", "stdio")

    if transport_type == "sse":
        sse_config = transport_config.get("sse", {})
        host = host_override or sse_config.get("host", "localhost")
        port = port_override or sse_config.get("port", 3000)

        print("🚀 Transport: Server-Sent Events (HTTP)")
        print(f"🌐 Host: {host}")
        print(f"🔌 Port: {port}")
        await server.run(transport_type="sse", host=host, port=port)
    else:
        print("🚀 Transport: Standard Input/Output (stdio)")
        await server.run(transport_type="stdio")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
        print("📴 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
