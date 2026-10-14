import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI

from call_function import available_functions, call_function
from prompts import system_prompt


# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("OPENROUTER_API_KEY")

if api_key is None:
    raise RuntimeError("OPENROUTER_API_KEY is not set")


# Create OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Chatbot")

parser.add_argument(
    "user_prompt",
    type=str,
    help="User prompt",
)

parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable verbose output",
)

args = parser.parse_args()


# Create conversation
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": args.user_prompt},
]


# Agent loop
for _ in range(20):
    # Send request to the LLM
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=messages,
        tools=available_functions,
        temperature=0,
    )

    # Make sure usage information exists
    if response.usage is None:
        raise RuntimeError("Response usage data is missing")

    if args.verbose:
        print(f"Prompt tokens: {response.usage.prompt_tokens}")
        print(f"Response tokens: {response.usage.completion_tokens}")

    # Get assistant message
    message = response.choices[0].message

    # Add assistant message to conversation history
    messages.append(message)

    # If there are no tool calls, the agent is finished
    if not message.tool_calls:
        print(f"Final response:\n{message.content}")
        break

    # Execute requested tool calls
    for tool_call in message.tool_calls:
        result_message = call_function(tool_call, args.verbose)

        if not result_message.get("content"):
            raise RuntimeError("Function call returned empty content")

        if args.verbose:
            print(f"-> {result_message['content']}")

        # Add tool result to conversation history
        messages.append(result_message)

else:
    print(
        "Agent reached the maximum number of iterations "
        "without completing the task."
    )
    raise SystemExit(1)