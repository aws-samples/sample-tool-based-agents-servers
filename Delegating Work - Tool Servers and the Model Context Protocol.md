# Delegating Work: Tool Servers and the Model Context Protocol

*Moving tool execution out of your agent and into dedicated servers for isolation, scale, and specialized reasoning with MCP Servers as the bridge*

---

This is the third post in our series on [AWS Prescriptive Guidance for Agentic AI Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/). Each post focuses on the concepts and patterns behind a single agent type, paired with a [hands-on sample on GitHub](README.md).

## Introduction

In the [previous post](https://github.com/aws-samples/sample-tool-based-agents-functions/blob/main/Extending%20AI%20Agents%20with%20Custom%20Tools%20and%20Functions.md), we gave agents tools with the `@tool` decorator. Those tools run *inline*, in the same process as the agent. That's perfect for a calculator or a weather lookup, but it ties the tool's lifecycle, dependencies, and credentials to the agent itself.

Some work doesn't belong inline. A tool that queries a production database, runs GPU-bound inference, or performs a multi-step analysis is better off in its own process; one you can isolate, scale, secure, and update independently. The answer is to move tool execution onto a **tool server** and let the agent act as a controller that dispatches to it.

By the end of this post, you'll understand:
- How server-based tools differ from inline tools
- How the Model Context Protocol (MCP) standardizes agent-to-server communication
- Why a tool server might run its own AI subagent
- When delegating execution to a server is worth the extra moving parts

---

## The Road to Tool Servers: A Brief History

Tool servers are a recent consolidation of two older ideas: that an LLM can call tools, and that tools should be decoupled from the thing that calls them. The standard that ties them together is called the Model Context Protocol or  MCP.

### Inline function calling (2023-2024)

As we covered in the [last post](https://github.com/aws-samples/sample-tool-based-agents-functions/blob/main/Extending%20AI%20Agents%20with%20Custom%20Tools%20and%20Functions.md), providers turned tool calling into a first-class API feature in 2023, [OpenAI's function calling](https://openai.com/index/function-calling-and-other-api-updates/) in June, followed by others. But every one of those tools ran wherever the agent ran. If your agent process could reach a resource, so could every tool; if it couldn't, none of them could. Isolation, independent scaling, and per-tool credentials were all the developer's problem to solve by hand.

### The integration explosion

As teams wired agents into real systems: databases, internal APIs, file stores, other models, etc. each integration was bespoke. Every framework wrapped tools differently, so a connector built for one agent stack rarely worked with another. The community ended up rebuilding the same database or filesystem connectors over and over, once per framework.

### Standardization with MCP (November 2024)

Anthropic's [Model Context Protocol](https://www.anthropic.com/news/model-context-protocol), released in [November 2024](https://modelcontextprotocol.io), gave users a common language. MCP defines how a server *advertises* its tools (and other context like resources and prompts) and how any MCP-compatible client *discovers and calls* them. Write a server once, and any MCP-aware agent can use it; conversely, an agent can consume a growing library of published servers without custom glue. Because the server is a separate process reached over a transport (stdio, HTTP, or SSE), tool execution is now naturally decoupled from the agent.

---

## Inline Tools vs. Server-Based Tools

The shift is about *where the tool runs and who owns it*, not about what the agent can do.

| Inline tools | Server-based tools |
|--------------|--------------------|
| Run in the agent's process | Run on an external server |
| Share the agent's resources and credentials | Dedicated infrastructure, isolated credentials |
| Simple, stateless operations | Complex, stateful, or resource-intensive work |
| One tool invocation at a time | Can chain multiple tools, or run a subagent |
| Agent owns all the logic | Server can own its own logic and reasoning |

The agent doesn't know the difference at call time, what changes is everything around that tool: lifecycle, blast radius, and who can change it.

---

## How MCP Connects Them

<img src="images/tool-based-agents-servers.png" width="600" alt="Diagram of a tool-based agent for servers: the agent shell dispatches a task to an external tool server, which executes it (optionally via its own subagent) and returns the result for the agent's LLM to synthesize." />

MCP follows a simple discovery-then-invoke loop:

1. **Discovery**: the agent connects to a server and asks what tools it offers
2. **Schema**: the server returns tool definitions — names, descriptions, parameters
3. **Invocation**: the agent calls a tool by name with arguments
4. **Response**: the server executes the tool and returns the result

Because discovery happens at connection time, you can add a tool to a server and connected agents pick it up without any client change. And because the protocol is shared, you can mix servers you wrote with servers the community published.

---

## When the Server Has Its Own Brain

An interesting version of this pattern is a tool server that runs its **own AI subagent**. Instead of exposing twenty low-level tools to the primary agent, the server exposes one high-level action, `analyze`, and behind it, an internal agent with its own prompt and tools does the multi-step work.

This directly fixes *tool sprawl*. When a single agent accumulates dozens of tools, reasoning slows down, similar tools compete for selection, and every call drags the full toolset through the context window. Delegating to a subagent keeps the primary agent's choices few and high-level, while domain detail stays isolated on the server. The primary agent becomes a lightweight controller; the heavy, specialized lifting happens elsewhere and can be scaled and secured on its own terms.

---

## When to Use Tool-Based Server Agents

Reach for a tool server when execution needs to be isolated, scaled, governed, or specialized beyond what an inline tool can offer.

| Use Case | Example |
|----------|---------|
| **Model chains** | Combining an LLM, a vision model, and code execution behind one action |
| **AI automation pipelines** | An orchestrator agent dispatching to several specialized servers |
| **DevOps assistants** | A script-runner server that executes in an isolated environment |
| **Financial computation** | Simulation or optimization that runs on dedicated compute |
| **Multimodal tools** | Combining audio, documents, and actions in one server |

### When to Use Something Else

If your tool is a simple, stateless function with no special credentials or scaling needs, ie. a calculator, a unit converter, a formatter, keep it inline with the `@tool` decorator from the [previous post](https://github.com/aws-samples/sample-tool-based-agents-functions/blob/main/Extending%20AI%20Agents%20with%20Custom%20Tools%20and%20Functions.md). A server adds a process boundary, a transport, and deployment overhead; only take that on when isolation, scale, governance, or specialized reasoning earns it.

---

## What's Next

You now understand how moving tools onto a server changes their lifecycle, why MCP makes that portable, and when a server should run its own subagent. The natural next step is to see it run. The **[companion sample](README.md)** builds a calculator MCP server, connects an agent to it, consumes a published server over stdio, and stands up an intelligent server with its own subagent.

So far our agents have worked with text and structured tools. But what about software meant for humans? For example, browsers, desktop apps, forms? In the [next post](https://github.com/aws-samples/sample-computer-use-agents/blob/main/Agents%20That%20Use%20Computers%20-%20Browsers%2C%20Desktops%2C%20and%20the%20GUI%20Frontier.md), we'll explore computer-use agents that can see and operate graphical interfaces.

---

## Resources

- [Companion sample: Tool-Based Agents for Servers](README.md)
- [AWS Prescriptive Guidance - Tool-based agents for servers](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/tool-based-agents-for-servers.html)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Strands Agents Documentation](https://strandsagents.com/)
- [Amazon Bedrock User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)

---

**Tim Sitze** is a Solutions Architect at Amazon Web Services, where he works with cybersecurity ISVs to design and scale their products on AWS. He specializes in security, AI/ML, IoT and data platform architectures, and has partnered on workloads spanning identity threat intelligence, agentic AI, and cloud-native security operations. Tim is based in the Washington, D.C. area.  
