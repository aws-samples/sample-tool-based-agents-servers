"""
MCP Agent - Stdio Transport Example

An agent that connects to an MCP server using stdio transport.
This example uses the AWS Documentation MCP server from awslabs.

Learning objectives:
- Understand stdio transport for MCP
- See how to use published MCP servers
- Learn about managed vs manual lifecycle
"""

import time
from shared.model import get_model
from shared.input_utils import get_multiline_input
from shared.streaming import StreamingCallbackHandler
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient


# Create MCP client with stdio transport
# This uses the AWS Documentation MCP server as an example
mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# Streaming callback handler announces each MCP tool the agent calls and
# streams the model's response token-by-token.
stream_handler = StreamingCallbackHandler()


def main():
    """Run the agent with AWS docs MCP server."""
    print("MCP Agent (AWS Documentation)")
    print("=" * 40)
    print("Connecting to AWS Documentation MCP Server...")
    print("Type 'quit' to exit")
    print("Tip: You can paste multi-line prompts!\n")

    # Managed approach - pass MCP client directly to agent
    # Lifecycle is handled automatically
    agent = Agent(
        model=get_model(),
        system_prompt="""You are a helpful AWS documentation assistant.
        Use the available tools to search and read AWS documentation.
        Provide accurate information with references.""",
        tools=[mcp_client],
        callback_handler=stream_handler,
    )

    while True:
        user_input = get_multiline_input("You: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if not user_input:
            continue

        # NOTE: streams the model's response to stdout for local use.
        # A production service should filter/redact it before logging.
        stream_handler.reset()
        print("\nAgent: ", end="", flush=True)
        start_time = time.time()
        agent(user_input)
        elapsed = time.time() - start_time
        print(f"\n({elapsed:.1f}s)\n")


if __name__ == "__main__":
    main()
