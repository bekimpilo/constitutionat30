"""
MCP Server for the South African Constitution Knowledge Graph.
Deployed on Railway with static server card support.
"""

import os
import json
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("South African Constitution Server")

# Read SPARQL endpoint from environment
SPARQL_ENDPOINT = os.getenv(
    "SPARQL_ENDPOINT",
    "https://api.triplydb.com/datasets/Od2og/za-constitution/sparql"
)

print(f"🔗 Using SPARQL endpoint: {SPARQL_ENDPOINT}")


# ------------------ MCP Tools ------------------

@mcp.tool()
async def query_constitution(sparql_query: str) -> str:
    """Execute a SPARQL query against the South African Constitution knowledge graph."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                SPARQL_ENDPOINT,
                data={"query": sparql_query},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return f"HTTP error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error executing query: {str(e)}"


@mcp.tool()
async def get_section_text(section_id: str) -> str:
    """Retrieve the full legal text of a specific provision by its identifier."""
    query = f"""
    PREFIX saont: <https://od2og.africa/ontology/>
    SELECT ?text WHERE {{
        <{section_id}> saont:legalText ?text .
    }}
    LIMIT 1
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                SPARQL_ENDPOINT,
                data={"query": query},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            response.raise_for_status()
            data = response.json()
            bindings = data.get("results", {}).get("bindings", [])
            if bindings:
                return bindings[0].get("text", {}).get("value", "No text found.")
            return "No text found for that identifier."
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def find_sections_by_keyword(keyword: str) -> str:
    """Search for provisions containing a specific keyword in their legal text."""
    query = f"""
    PREFIX saont: <https://od2og.africa/ontology/>
    SELECT ?provision ?text WHERE {{
        ?provision saont:legalText ?text .
        FILTER(REGEX(LCASE(?text), LCASE("{keyword}"), "i"))
    }}
    LIMIT 20
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                SPARQL_ENDPOINT,
                data={"query": query},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            response.raise_for_status()
            data = response.json()
            bindings = data.get("results", {}).get("bindings", [])
            if not bindings:
                return f"No provisions found containing '{keyword}'."
            
            results = []
            for row in bindings:
                provision = row.get("provision", {}).get("value", "Unknown")
                text = row.get("text", {}).get("value", "")
                if len(text) > 200:
                    text = text[:200] + "..."
                results.append(f"{provision}: {text}")
            return "\n\n".join(results)
        except Exception as e:
            return f"Error: {str(e)}"


# ------------------ FastAPI Wrapper (for Railway) ------------------

# Create a combined ASGI app
app = FastAPI(title="SA Constitution MCP Server")

# Mount the MCP server under /mcp
app.mount("/mcp", mcp.streamable_http_app())


# Serve the server card at /.well-known/mcp
@app.get("/.well-known/mcp")
async def serve_server_card():
    """Serve the MCP server card for discovery."""
    railway_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "https://your-railway-app.railway.app")
    card = {
        "$schema": "https://schema.smithery.ai/mcp/server-card/0.0.1/schema.json",
        "name": "South African Constitution Server",
        "description": "MCP server for querying the South African Constitution (Ch 1 & 2) via SPARQL.",
        "version": "1.0.0",
        "author": {
            "name": "Od2og",
            "url": "https://od2og.africa"
        },
        "homepage": "https://github.com/od2og/constitutionat30",
        "repository": {
            "type": "git",
            "url": "https://github.com/od2og/constitutionat30"
        },
        "license": "MIT",
        "transport": {
            "type": "streamable-http",
            "url": f"{railway_url}/mcp"
        },
        "capabilities": {
            "tools": [
                {"name": "query_constitution", "description": "Execute any SPARQL query."},
                {"name": "get_section_text", "description": "Look up a specific provision."},
                {"name": "find_sections_by_keyword", "description": "Search by keyword."}
            ]
        },
        "configuration": {
            "schema": {
                "type": "object",
                "properties": {
                    "sparqlEndpoint": {
                        "type": "string",
                        "description": "SPARQL endpoint URL"
                    }
                }
            }
        }
    }
    return Response(content=json.dumps(card, indent=2), media_type="application/json")


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {"status": "healthy", "endpoint": SPARQL_ENDPOINT}


@app.get("/")
async def root():
    """Root endpoint – redirects to server info."""
    return {
        "message": "South African Constitution MCP Server",
        "endpoint": "/mcp",
        "server_card": "/.well-known/mcp",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)