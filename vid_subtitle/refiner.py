"""
Subtitle refinement module for improving subtitle accuracy.
"""

import re
from typing import Dict, Any, List

from openai import OpenAI
from pydantic import BaseModel

from .utils import get_openai_api_key, validate_file_exists
from .utils import VidSubtitleError

class RefinedSubtitle(BaseModel):
  refined_subtitle: str

class SubtitleRefinementError(VidSubtitleError):
    """Raised when subtitle refinement fails."""
    pass


def refine_subtitle_text(subtitle_file_path: str, instruction: str) -> str:
    """
    Refine subtitle text using OpenAI API.
    """

        # Step 1: Validate inputs
    if not validate_file_exists(subtitle_file_path):
            raise VidSubtitleError(f"Subtitle file not found: {subtitle_file_path}")
        
    try:
      api_key = get_openai_api_key()
      client = OpenAI(api_key=api_key)

      file = open(subtitle_file_path, "r")
      subtitle_text = file.read()
      file.close()
      
      response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that refines subtitles. You will need to refine the subtitle file based on the instruction. Do not change the format of the subtitle data. Do not add any other text to the output."},
            {"role": "user", "content": f"###Instruction###\n {instruction}\n\n###Subtitle###\n {subtitle_text}"}
        ],
        response_format=RefinedSubtitle
      )
      refined_subtitle = response.choices[0].message.parsed
      return refined_subtitle.refined_subtitle

    except Exception as e:
        raise SubtitleRefinementError(f"Failed to refine subtitle text: {str(e)}") from e


def save_subtitle_text(refined_subtitle_text: str, output_subtitle_file_path: str) -> None:
    """
    Save refined subtitle text to a file.
    """
    with open(output_subtitle_file_path, "w") as file:
        file.write(refined_subtitle_text)