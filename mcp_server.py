"""
MCP Server - Calculator Example

A simple MCP server that provides calculator tools.
Run this server first, then connect with the mcp_agent.py client.

Learning objectives:
- Understand how to create an MCP server
- See how tools are exposed via the MCP protocol
- Learn about server transports (stdio, HTTP, SSE)
"""

from mcp.server.mcpserver import MCPServer

# Create an MCP server with a descriptive name.
# Runs on port 8000 — the intelligent server (tool_server_agent.py) uses 8001,
# so the two can run side by side without colliding.
mcp = MCPServer("Calculator Server")


@mcp.tool(description="Add two numbers together")
def add(x: float, y: float) -> float:
    """Add two numbers and return the result."""
    return x + y


@mcp.tool(description="Subtract the second number from the first")
def subtract(x: float, y: float) -> float:
    """Subtract y from x and return the result."""
    return x - y


@mcp.tool(description="Multiply two numbers together")
def multiply(x: float, y: float) -> float:
    """Multiply two numbers and return the result."""
    return x * y


@mcp.tool(description="Divide the first number by the second")
def divide(x: float, y: float) -> str:
    """Divide x by y and return the result."""
    if y == 0:
        return "Error: Division by zero"
    return str(x / y)


@mcp.tool(description="Calculate the power of a number")
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base ** exponent


if __name__ == "__main__":
    print("Starting Calculator MCP Server...")
    print("Server running on http://localhost:8000/mcp/")
    print("Press Ctrl+C to stop\n")
    
    # Run with streamable HTTP transport for easy testing
    mcp.run(transport="streamable-http", port=8000)
