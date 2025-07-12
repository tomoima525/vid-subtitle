import asyncio
from typing import Optional
import uuid
from agents import Agent, HandoffOutputItem, ItemHelpers, MessageOutputItem, Runner, TResponseInputItem, ToolCallItem, ToolCallOutputItem, function_tool, trace, RunContextWrapper
from dotenv import load_dotenv
from pydantic import BaseModel
from .core import add_subtitles, extract_subtitles_only, refine_subtitles
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


load_dotenv()

### Context

class AgentContext(BaseModel):
    video_file: Optional[str] = None
    language: Optional[str] = None
    instruction: Optional[str] = None
    subtitle_file: Optional[str] = None

### Tools

@function_tool
def add_subtitle(context: RunContextWrapper[AgentContext], video_file: str, language: str = "en") -> str:
    context.context.video_file = video_file
    context.context.language = language
    output_video_file = video_file.replace(".mp4", f"_subtitles_{language}.mp4")
    add_subtitles(video_file, output_video_file, language=language, verbose=True)
    return f"Subtitles added to video file"

@function_tool
def extract_subtitle(context: RunContextWrapper[AgentContext], video_file: str, language: str = "en") -> str:
    context.context.video_file = video_file
    context.context.language = language
    output_subtitle_file = video_file.replace(".mp4", f"_subtitles.srt")
    extract_subtitles_only(video_file, output_subtitle_file=output_subtitle_file, language=language, verbose=True)
    return f"Subtitles extracted from video file"

@function_tool
def refine_subtitle(context: RunContextWrapper[AgentContext], subtitle_file: str, instruction: str) -> str:
    context.context.subtitle_file = subtitle_file
    context.context.instruction = instruction
    output_subtitle_file = subtitle_file.replace(".srt", f"_refined.srt")
    refine_subtitles(subtitle_file, output_subtitle_file, instruction=instruction, verbose=True)
    return f"Subtitles refined."

### Agents
add_subtitle_agent = Agent[AgentContext](
    name="Add Subtitle Agent",
    handoff_description="You are a helpful assistant that adds subtitles to a video file.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        f"First ask user which video file to add subtitles to. Ask user if they have a preference for the language of the subtitles. Then call `add_subtitle` tool to add subtitles to the video."
    ),
    tools=[add_subtitle],
)

extract_subtitle_agent = Agent[AgentContext](
    name="Extract Subtitle Agent",
    handoff_description="You are a helpful assistant that extracts subtitles from a video file.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        f"First ask user which video file to extract subtitles from. Ask user if they have a preference for the language of the subtitles. Then call `extract_subtitle` tool to extract subtitles from the video."
    ),
    tools=[extract_subtitle],
)

refine_subtitle_agent = Agent[AgentContext](
    name="Refine Subtitle Agent",
    handoff_description="You are a helpful assistant that refines subtitles.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        f"First ask user which subtitle file to refine. Ask user for the instruction to refine the subtitles. Then call `refine_subtitle` tool to refine the subtitles."
    ),
    tools=[refine_subtitle],
)

agent = Agent[AgentContext](
    name="Subtitle Generator Agent",
    handoff_description="You are a triage agent that can delegate a task to the appropriate agent.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        f"First ask user what they would like to do: add subtitles to a video, extract subtitles from video, or refine subtitles. Then you determine the appropriate Agent to do the task."
    ),
    handoffs=[add_subtitle_agent, extract_subtitle_agent, refine_subtitle_agent],
)

async def main(debug: bool = False):
    context = AgentContext()
    current_agent: Agent[AgentContext] = agent
    input_items: list[TResponseInputItem] = []
    conversation_id = uuid.uuid4().hex[:16]

    while True:
        if len(input_items) == 0:
            user_input = "Start Agent."
        else:
            user_input = input("> ")
        with trace("Agent conversation", group_id=conversation_id):
            input_items.append({ "content": user_input, "role": "user" })
            result = await Runner.run(current_agent, input_items, context=context)
            for new_item in result.new_items:
                agent_name = new_item.agent.name
                if isinstance(new_item, MessageOutputItem):
                    print(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
                elif isinstance(new_item, HandoffOutputItem):
                    print(
                        f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}"
                    )
                elif isinstance(new_item, ToolCallItem):
                    print(f"{agent_name}: Calling a tool")
                elif isinstance(new_item, ToolCallOutputItem):
                    print(f"{agent_name}: Tool call output: {new_item.output}")
                elif new_item.type == "run_error_event":
                    print(f"=== Run error: {new_item.error} ===")
                else:
                    print(f"{agent_name}: Skipping item: {new_item.__class__.__name__}")

            input_items = result.to_input_list()
            current_agent = result.last_agent

def generate_subtitles_with_agent(debug: bool = False):
    asyncio.run(main(debug))
    