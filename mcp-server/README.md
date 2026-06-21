
# 🇿🇦 South African Constitution Knowledge Graph – MCP Server

**Model Context Protocol (MCP) server** that exposes the South African Constitution knowledge graph to AI assistants  via SPARQL.

This server provides three tools that let agents query constitutional provisions, retrieve legal text, and search by keyword – all through natural language.

---

## 🚀 Quick Install

### Via Smithery (1‑line)
```bash
npx -y @smithery/cli install @od2og/za-constitution-mcp --client claude
Manual Installation
bash
git clone https://github.com/od2og/constitutionat30
cd constitutionat30/mcp-server
pip install -r requirements.txt
python server.py
🛠️ Available Tools
Tool	Description
sparql	Execute any SPARQL query against the full knowledge graph.
get_text	Retrieve the exact legal text of a provision by its identifier (e.g., sec:21, sec:23_2_a).
search	Find all provisions containing a keyword (e.g., privacy, labour, detention).
All tools are read‑only, idempotent, and safe – they never modify data.

⚙️ Configuration
The server reads configuration from environment variables.

Create a .env file in this directory (copy from .env.example):

env
# Public base URL of your server (required)
PUBLIC_BASE_URL=https://mcp.od2og.africa

# SPARQL endpoint (defaults to public TriplyDB)
SPARQL_ENDPOINT=https://api.triplydb.com/datasets/Od2og/za-constitution/sparql

# Log level (INFO, DEBUG, WARNING)
LOG_LEVEL=INFO
🔗 Connect to Claude Desktop
Add this to your claude_desktop_config.json:

json
{
  "mcpServers": {
    "za-constitution": {
      "type": "streamable-http",
      "url": "https://mcp.od2og.africa/mcp"
    }
  }
}
Or, if running locally:

json
{
  "mcpServers": {
    "za-constitution": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-server/server.py"]
    }
  }
}
Restart Claude Desktop.

🧪 Example Queries
Once connected, you can ask Claude:

You ask	What the server does
"What does section 23 say about labour rights?"	Calls get_text with sec:23
"Which provisions protect privacy?"	Calls search with privacy
"Find all sections that reference section 36."	Calls sparql with a custom query
📦 Dependencies
mcp – MCP SDK

httpx – Async HTTP client

python-dotenv – Environment configuration

fastapi – Web framework

uvicorn – ASGI server

All are listed in requirements.txt.

🧠 Architecture
text
User (Claude)
    ↓
Claude Desktop / MCP Client
    ↓
MCP Server (this repo) – /mcp endpoint
    ↓
SPARQL Endpoint (TriplyDB)
    ↓
Constitution Knowledge Graph (RDF)
The server is a stateless, read‑only proxy that translates MCP tool calls into SPARQL queries and returns results.

🚀 Deployment
This server is designed to run on Railway using Nixpacks. The nixpacks.toml file in the project root defines the build and start commands.

Deploy manually:

bash
railway up
📜 License
Public domain / open data.

Maintainer: Beki Ndlovu
Issues: https://github.com/od2og/constitutionat30/issues