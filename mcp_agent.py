"""
MCP Agent - Client Example

An agent that connects to an MCP server to use its tools.
Make sure to run mcp_server.py first before running this client.

Learning objectives:
- Understand how to connect to MCP servers
- See how MCP tools integrate with Strands agents
- Learn about different transport options
"""

import sys
import time
from shared.input_utils import get_multiline_input
from shared.streaming import StreamingCallbackHandler
from mcp.client.streamable_http import streamable_http_client
from strands import Agent
from strands.tools.mcp import MCPClient
from shared.model import get_model

# Model is pinned centrally in shared/model.py (get_model) so all labs share
# one active Bedrock model. Override with the STRANDS_MODEL_ID env var.
MODEL = get_model()

# Which server to connect to. Defaults to the calculator server on 8000.
# Pass a URL as the first argument to point at another server, e.g. the
# intelligent analysis server: python mcp_agent.py http://localhost:8001/mcp/
# Dev-only client: the URL is used as-is without validation.
SERVER_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/mcp/"


def create_http_transport():
    """Create a streamable HTTP transport to connect to the MCP server."""
    return streamable_http_client(SERVER_URL)


# Create the MCP client
mcp_client = MCPClient(create_http_transport)

# Streaming callback handler announces each MCP tool the agent calls and
# streams the model's response token-by-token.
stream_handler = StreamingCallbackHandler()


def main():
    """Run the MCP-connected agent interactively."""
    print("MCP Agent (Server Tools)")
    print("=" * 40)
    print(f"Connecting to MCP server at {SERVER_URL}")
    print("Make sure the target server is running!")
    print("Type 'quit' to exit")
    print("Tip: You can paste multi-line prompts!\n")

    # Use context manager to manage MCP connection lifecycle
    with mcp_client:
        # Get tools from the MCP server
        tools = mcp_client.list_tools_sync()
        print(f"Loaded {len(tools)} tool(s) from server:")
        for t in tools:
            print(f"  - {t.tool_name}")
        print()

        # Create agent with MCP tools
        agent = Agent(
            model=MODEL,
            system_prompt="""You are a helpful calculator assistant.
            Use the available math tools to perform calculations.
            Always show your work and explain the result.""",
            tools=tools,
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
