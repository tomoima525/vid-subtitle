import asyncio
from agents import Agent, ItemHelpers, Runner, function_tool
from dotenv import load_dotenv

load_dotenv()

@function_tool
def how_many_jokes() -> int:
    return 2

async def main():
    agent = Agent(
        name="Joker",
        instructions="First call the `how_many_jokes` tool, then tell that many jokes.",
        tools=[how_many_jokes],
    )

    result = Runner.run_streamed(agent, input="Tell me jokes")
    print("==== Run starting ====")
    async for event in result.stream_events():
      # We'll ignore the raw responses event deltas
        if event.type == "raw_response_event":
            continue
        elif event.type == "agent_updated_stream_event":
            print(f"Agent updated: {event.new_agent.name}")
            continue
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print("-- Tool was called")
            elif event.item.type == "tool_call_output_item":
                print(f"-- Tool output: {event.item.output}")
            elif event.item.type == "message_output_item":
                print(f"-- Message output:\n {ItemHelpers.text_message_output(event.item)}")
            else:
                pass  # Ignore other event types

    print("=== Run complete ===")


def generate_subtitles_with_agent():
    asyncio.run(main())
    