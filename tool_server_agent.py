"""
Tool Server with Subagent Example

Demonstrates the full server-based agent pattern where the tool server
has its own AI reasoning capabilities. The primary agent dispatches to
this server, which uses its own subagent to handle complex tasks.

This pattern enables:
- Isolated execution environments
- Specialized AI reasoning per tool server
- Complex multi-step tool chains
- Scalable, modular architecture

Learning objectives:
- Understand tool servers with their own AI capabilities
- See how primary agents dispatch to intelligent servers
- Learn the controller/dispatcher pattern
- Watch the server's internal agent reason in real time
"""

import sys
from shared.model import get_model
from shared.streaming import StreamingCallbackHandler

from mcp.server.mcpserver import MCPServer
from strands import Agent, tool

import re

# Create the MCP server on port 8001 so it doesn't collide with the
# calculator server (mcp_server.py) on port 8000.
mcp = MCPServer("Intelligent Analysis Server")


# Define tools that the server's internal agent can use. Each tool prints
# what it received and what it's returning so the operator running the
# server can see each step of the internal agent's reasoning in real time.
@tool
def load_data(source: str) -> str:
    """Load data from a source (simulated).
    
    Args:
        source: Data source identifier
    """
    print(f"          load_data(source={source!r})")
    # Simulated data loading
    data = {
        "sales": "Q1: $100k, Q2: $150k, Q3: $120k, Q4: $200k",
        "users": "Jan: 1000, Feb: 1200, Mar: 1500, Apr: 1800",
        "metrics": "Conversion: 3.2%, Retention: 85%, NPS: 72"
    }
    output = data.get(source, f"No data found for: {source}")
    print(f"          -> {output}")
    return output


@tool
def calculate_trend(values: str) -> str:
    """Calculate trend from a series of values (simulated).

    Tolerates labels and common units, including $ signs, % signs, and
    k/m/b multiplier suffixes — e.g., "Q1: $100k, Q2: $150k" parses to
    100000 and 150000.

    Args:
        values: Comma-separated values; each may include a label or units
    """
    print(f"          calculate_trend(values={values!r})")
    try:
        nums = []
        for v in values.split(","):
            # If labeled like "Q1: $100k", take the value portion after the colon.
            segment = v.split(":", 1)[-1]
            # Pull out the first number (with optional sign/decimal) and an
            # optional k/m/b suffix; ignore $, %, and other text.
            match = re.search(r"([-+]?\d+\.?\d*)\s*([kKmMbB])?", segment)
            if not match:
                continue
            num = float(match.group(1))
            multiplier = {"k": 1e3, "m": 1e6, "b": 1e9}.get(
                (match.group(2) or "").lower(), 1
            )
            nums.append(num * multiplier)
        if len(nums) < 2:
            output = "Need at least 2 values for trend"
        else:
            trend = "increasing" if nums[-1] > nums[0] else "decreasing"
            change = ((nums[-1] - nums[0]) / nums[0]) * 100
            output = f"Trend: {trend}, Change: {change:.1f}%"
    except Exception as e:
        output = f"Error calculating trend: {e}"
    print(f"          -> {output}")
    return output


@tool
def generate_summary(data: str, analysis: str) -> str:
    """Generate a summary combining data and analysis.
    
    Args:
        data: Raw data string
        analysis: Analysis results
    """
    print(f"          generate_summary(data={data!r}, analysis={analysis!r})")
    output = f"Summary Report:\nData: {data}\nAnalysis: {analysis}"
    print("          -> (returning summary)")
    return output


# Streaming handler for the internal agent — its reasoning will print to
# the server terminal as it runs, so the operator can watch it think.
internal_stream_handler = StreamingCallbackHandler()

# Create the server's internal agent with its own tools
# This agent handles complex reasoning within the tool server
#
# One agent instance is shared by every `analyze` call, so its conversation
# history carries over between calls (and between clients, if several connect).
# That is fine for a single-user local demo. A multi-tenant server would create
# a fresh Agent per request (or per session) so one caller's data never leaks
# into another caller's context.
internal_agent = Agent(
    model=get_model(),
    system_prompt="""You are a data analysis expert. When asked to analyze data:
    1. First load the relevant data using load_data
    2. Calculate trends if numeric data is present
    3. Generate a comprehensive summary
    Always be thorough and provide actionable insights.""",
    tools=[load_data, calculate_trend, generate_summary],
    callback_handler=internal_stream_handler,
)


# Expose the intelligent analysis capability via MCP
@mcp.tool(description="Perform AI-powered data analysis with automatic insights")
def analyze(data_source: str, question: str) -> str:
    """Analyze data using AI reasoning.
    
    The server's internal agent will:
    - Load relevant data
    - Perform calculations
    - Generate insights
    
    Args:
        data_source: Which data to analyze (sales, users, metrics)
        question: What you want to know about the data
    """
    # Header so the operator can see when the internal agent kicks in.
    print()
    print(f"  --- internal agent: analyze(data_source={data_source!r}) ---")
    prompt = f"Analyze the '{data_source}' data and answer: {question}"
    # NOTE: streams the model's response to stdout for local use.
    # A production service should filter/redact it before logging.
    internal_stream_handler.reset()
    result = internal_agent(prompt)
    print("\n  --- internal agent complete ---\n")
    return str(result)


@mcp.tool(description="Get available data sources")
def list_sources() -> str:
    """List available data sources for analysis."""
    return "Available sources: sales, users, metrics"


@mcp.tool(description="Simple calculation without AI")
def quick_calc(operation: str, a: float, b: float) -> str:
    """Perform a quick calculation.
    
    Args:
        operation: add, subtract, multiply, divide
        a: First number
        b: Second number
    """
    ops = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Error: division by zero"
    }
    result = ops.get(operation, "Unknown operation")
    return f"{a} {operation} {b} = {result}"


if __name__ == "__main__":
    print("Intelligent Analysis Server")
    print("=" * 40)
    print("This tool server has its own AI subagent")
    print("for complex data analysis tasks.")
    print()
    print("Available tools:")
    print("  - analyze: AI-powered data analysis")
    print("  - list_sources: Show available data")
    print("  - quick_calc: Simple calculations")
    print()
    print("Server running on http://localhost:8001/mcp/")
    print("Press Ctrl+C to stop\n")

    mcp.run(transport="streamable-http", port=8001)
