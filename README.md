# Jarvis

An intelligent AI agent orchestration system that dynamically creates specialized agents to accomplish complex tasks using MCP (Model Context Protocol) servers.

## Demo

![Jarvis Demo](docs/images/demo-screenshot.png)

## Overview

Jarvis analyzes your natural language queries and automatically creates specialized agents with appropriate MCP servers and instructions. When you provide a task, the system:

1. **Analyzes Intent**: A planner agent understands your goals
2. **Designs Agent**: Creates a specialized agent with relevant capabilities
3. **Configures Tools**: Automatically selects appropriate MCP servers
4. **Executes Tasks**: Runs the configured agent to accomplish your objectives

## Installation/Setup

### Prerequisites
- Python 3.11 or higher
- Node.js (for MCP servers)
- API keys for Gemini and OpenAI

### Setup (uv recommended)

**With uv:**
```bash
git clone https://github.com/mewtyunjay/jarvis.git
cd jarvis
uv sync
```

**With pip:**
```bash
git clone https://github.com/mewtyunjay/jarvis.git
cd jarvis
pip install -e .
```

### Environment Configuration
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## MCP Server Configuration

1. **Create MCP configuration:**
   ```bash
   cp mcp/mcp_config.example.json mcp/mcp_config.json
   ```

2. **Edit `mcp/mcp_config.json`** to configure your desired MCP servers and add API keys

3. **Generate tool mappings:**
   ```bash
   python scripts/discover_tools.py
   ```
   This creates `mcp/mcp_tools.json` which maps available tools from your configured MCP servers. **Run this every time you update your MCP configuration.**

## Usage

**Standard:**
```bash
python main.py
```

**With uv:**
```bash
uv run main.py
```

**Debug mode:**
```bash
python main.py --debug
```

Enter your query when prompted. Examples:
- "Check my calendar and send a meeting invite to participants of the last email I sent whenever I'm free"
- "Research the latest AI developments and create a report"

---

**WIP** - Execute with caution for operations that modify files, send communications, or access external services. Tools for Human-In-The-Loop in generated dynamically, so verify Planner Agent's output.