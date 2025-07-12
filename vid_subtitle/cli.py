"""
Command-line interface for vid-subtitle library.
"""

import argparse
import sys

from .core import add_subtitles, extract_subtitles_only, get_supported_languages, get_library_info, add_subtitle_file, refine_subtitles
from .agent import generate_subtitles_with_agent
from .utils import VidSubtitleError


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Add subtitles to videos using OpenAI Whisper API and FFmpeg",
        prog="vid-subtitle"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add subtitles command
    add_parser = subparsers.add_parser('add', help='Add subtitles to a video')
    add_parser.add_argument('input_video', help='Input video file (MP4 or MOV)')
    add_parser.add_argument('output_video', help='Output video file with subtitles')
    add_parser.add_argument('-l', '--language', default='en', 
                           help='Language code for transcription (default: en)')
    add_parser.add_argument('-v', '--verbose', action='store_true',
                           help='Enable verbose output')
    
    # Extract subtitles only command
    extract_parser = subparsers.add_parser('extract', help='Extract subtitles only (no video output)')
    extract_parser.add_argument('input_video', help='Input video file (MP4 or MOV)')
    extract_parser.add_argument('-o', '--output', help='Output SRT file (optional)')
    extract_parser.add_argument('-l', '--language', default='en',
                               help='Language code for transcription (default: en)')
    extract_parser.add_argument('-v', '--verbose', action='store_true',
                               help='Enable verbose output')
    
    # Embed subtitles command
    embed_parser = subparsers.add_parser('embed', help='Embed existing subtitles into video')
    embed_parser.add_argument('input_video', help='Input video file (MP4 or MOV)')
    embed_parser.add_argument('subtitle_file', help='Input SRT subtitle file')
    embed_parser.add_argument('output_video', help='Output video file with subtitles')
    embed_parser.add_argument('-v', '--verbose', action='store_true',
                             help='Enable verbose output')
    
    # Info command
    subparsers.add_parser('info', help='Show library information')
    
    # Languages command
    subparsers.add_parser('languages', help='List supported languages')

    # Refine subtitles command
    refine_parser = subparsers.add_parser('refine', help='Refine subtitles')
    refine_parser.add_argument('subtitle_file', help='Input SRT subtitle file')
    refine_parser.add_argument('output_subtitle_file', help='Output SRT subtitle file with refined subtitles')
    refine_parser.add_argument('-i', '--instruction', help="Instruction for refining subtitles")
    refine_parser.add_argument('-v', '--verbose', action='store_true',
                              help='Enable verbose output')

    # Agent command
    agent_parser = subparsers.add_parser('agent', help='Use Agent to generate subtitles')
    agent_parser.add_argument('-d', '--debug', action='store_true',
                              help='Enable debug mode')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'add':
            print(f"Adding subtitles to {args.input_video}...")
            result = add_subtitles(
                input_video=args.input_video,
                output_video=args.output_video,
                language=args.language,
                verbose=args.verbose
            )
            
            print(f"\n✓ Success!")
            print(f"Output video: {result['output_video']}")
            print(f"SRT file: {result['srt_file']}")
            print(f"Estimated cost: ${result['transcription_cost']:.4f}")
            
        elif args.command == 'extract':
            print(f"Extracting subtitles from {args.input_video}...")
            result = extract_subtitles_only(
                input_video=args.input_video,
                output_srt=args.output,
                language=args.language,
                verbose=args.verbose
            )
            
            print(f"\n✓ Success!")
            print(f"SRT file: {result['srt_file']}")
            print(f"Subtitle count: {result['subtitle_stats']['subtitle_count']}")
            print(f"Estimated cost: ${result['transcription_cost']:.4f}")
            
        elif args.command == 'embed':
            print(f"Embedding subtitles into {args.input_video}...")
            result = add_subtitle_file(
                input_video=args.input_video,
                subtitle_file=args.subtitle_file,
                output_video=args.output_video,
                verbose=args.verbose
            )
            
            print(f"\n✓ Success!")
            print(f"Output video: {result['output_video']}")
            print(f"Subtitle file used: {result['subtitle_file']}")
            print(f"Estimated processing time: {result['processing_time']:.1f} seconds")
            
        elif args.command == 'info':
            info = get_library_info()
            print("vid-subtitle Library Information:")
            print(f"Version: {info['version']}")
            print(f"Supported video formats: {', '.join(info['supported_video_formats'])}")
            print(f"Supported subtitle formats: {', '.join(info['supported_subtitle_formats'])}")
            print(f"Supported languages: {info['supported_languages']}")
            print(f"Requires FFmpeg: {info['requires_ffmpeg']}")
            print(f"Requires OpenAI API key: {info['requires_openai_api_key']}")
            
        elif args.command == 'languages':
            languages = get_supported_languages()
            print(f"Supported languages ({len(languages)} total):")
            
            # Print in columns
            cols = 6
            for i in range(0, len(languages), cols):
                row = languages[i:i+cols]
                print("  " + "  ".join(f"{lang:>3}" for lang in row))
        
        elif args.command == 'refine':
            print(f"Refining subtitles in {args.subtitle_file}...")
            result = refine_subtitles(
                subtitle_file_path=args.subtitle_file,
                output_subtitle_file_path=args.output_subtitle_file,
                instruction=args.instruction,
                verbose=args.verbose
            )
            
            print(f"\n✓ Success!")
            print(f"Output subtitle file: {result['output_subtitle_file']}")

        elif args.command == 'agent':
            print("Using Agent to generate subtitles...")
            result = generate_subtitles_with_agent(debug=args.debug);
        return 0
        
    except VidSubtitleError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
