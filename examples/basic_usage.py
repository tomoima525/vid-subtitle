"""
Basic usage examples for vid-subtitle library.
"""

import os
from vid_subtitle import add_subtitles, extract_subtitles_only, get_supported_languages, get_library_info


def main():
    """
    Demonstrate basic usage of the vid-subtitle library.
    """
    print("=== vid-subtitle Library Examples ===\n")
    
    # Show library information
    print("1. Library Information:")
    lib_info = get_library_info()
    for key, value in lib_info.items():
        print(f"   {key}: {value}")
    print()
    
    # Show supported languages (first 20)
    print("2. Supported Languages (first 20):")
    languages = get_supported_languages()
    print(f"   Total: {len(languages)} languages")
    print(f"   Sample: {', '.join(languages[:20])}")
    print()
    
    # Check if OpenAI API key is set
    print("3. Environment Check:")
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print("   ✓ OPENAI_API_KEY is set")
    else:
        print("   ✗ OPENAI_API_KEY is not set")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Example video file path (you need to provide your own video file)
    input_video = "input.mp4"  # Replace with your video file
    
    if not os.path.exists(input_video):
        print(f"\n4. Example Usage (requires video file):")
        print(f"   Video file '{input_video}' not found.")
        print("   To test the library, place a video file in this directory and update the path.")
        print("\n   Example code:")
        print("   ```python")
        print("   from vid_subtitle import add_subtitles")
        print("   ")
        print("   # Add subtitles to video")
        print("   result = add_subtitles(")
        print("       input_video='your_video.mp4',")
        print("       output_video='output_with_subtitles.mp4',")
        print("       language='en',")
        print("       verbose=True")
        print("   )")
        print("   ")
        print("   print(f'SRT file: {result[\"srt_file\"]}')") 
        print("   print(f'Output video: {result[\"output_video\"]}')") 
        print("   print(f'Estimated cost: ${result[\"transcription_cost\"]:.4f}')")
        print("   ```")
        return
    
    try:
        print(f"\n4. Processing Video: {input_video}")
        
        # Example 1: Extract subtitles only
        print("\n   Example 1: Extract subtitles only")
        result1 = extract_subtitles_only(
            input_video=input_video,
            language="en",
            verbose=True
        )
        
        print(f"   Results:")
        print(f"   - SRT file: {result1['srt_file']}")
        print(f"   - Estimated cost: ${result1['transcription_cost']:.4f}")
        print(f"   - Subtitle count: {result1['subtitle_stats']['subtitle_count']}")
        
        # Example 2: Add subtitles to video
        print("\n   Example 2: Add subtitles to video")
        output_video = "output_with_subtitles.mp4"
        
        result2 = add_subtitles(
            input_video=input_video,
            output_video=output_video,
            language="en",
            verbose=True
        )
        
        print(f"   Results:")
        print(f"   - Output video: {result2['output_video']}")
        print(f"   - SRT file: {result2['srt_file']}")
        print(f"   - Video duration: {result2['video_info']['duration']:.1f} seconds")
        print(f"   - Video resolution: {result2['video_info']['resolution']}")
        print(f"   - Estimated cost: ${result2['transcription_cost']:.4f}")
        
        print("\n✓ Examples completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        print("Make sure you have:")
        print("- FFmpeg installed")
        print("- Valid OpenAI API key")
        print("- Sufficient API credits")
        print("- Valid video file")


if __name__ == "__main__":
    main()
