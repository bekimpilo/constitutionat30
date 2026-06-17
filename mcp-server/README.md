## 📘 MCP Server

# 🇿🇦 South African Constitution – MCP Server

MCP server that exposes the Constitution knowledge graph to AI assistants (Claude, etc.) via SPARQL.

---

## 🚀 Install

### Via Smithery (1‑line)
```bash
npx -y @smithery/cli install @od2og/za-constitution-mcp --client claude
Manual
bash
git clone https://github.com/od2og/za-constitution-kg.git
cd constitutionat30/mcp-server
pip install -r requirements.txt
python server.py
⚙️ Configuration
Copy .env.example to .env and edit the SPARQL endpoint if needed:

text
SPARQL_ENDPOINT=https://api.triplydb.com/datasets/Od2og/za-constitution/sparql
Default points to the public TriplyDB endpoint.

🛠️ Tools
Tool	Description
query_constitution	Execute any SPARQL query
get_section_text	Look up a specific provision (e.g., sec:21)
find_sections_by_keyword	Search by keyword


📦 Dependencies
mcp – MCP SDK

httpx – Async HTTP client

python-dotenv – Environment config

📜 License
Public domain / open data

Maintainer: Beki Ndlovu
Issues: https://github.com/od2og/constitutionat30/issues
