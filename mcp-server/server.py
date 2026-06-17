"""
MCP Server for the South African Constitution Knowledge Graph.
Deployed on Railway with FastAPI wrapper, health check, and server card.
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

# Read SPARQL endpoint from environment, with fallback default
SPARQL_ENDPOINT = os.getenv(
    "SPARQL_ENDPOINT",
    "https://api.triplydb.com/datasets/Od2og/za-constitution/sparql"
)

print(f"🔗 Using SPARQL endpoint: {SPARQL_ENDPOINT}")


# ============================================
# MCP TOOLS
# ============================================

@mcp.tool()
async def query_constitution(sparql_query: str) -> str:
    """
    Execute a SPARQL query against the South African Constitution knowledge graph.
    The user's natural language question should be converted to SPARQL before calling this tool.

    Args:
        sparql_query: The SPARQL query string (e.g., "SELECT ?s WHERE { ?s a saont:Section }").
    
    Returns:
        JSON string containing the query results.
    """
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
    """
    Retrieve the full legal text of a specific section or provision by its identifier.

    Args:
        section_id: The section identifier (e.g., "sec:21", "sec:23_2_a", "sec:36_1").

    Returns:
        The legal text of the specified provision.
    """
    query = f"""
    PREFIX saont: <https://od2og.africa/ontology/>
    PREFIX sec: <https://od2og.africa/constitution/section/>

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
    """
    Search for sections or provisions that contain a specific keyword in their legal text.

    Args:
        keyword: The keyword to search for (e.g., "privacy", "labour", "detention").

    Returns:
        A list of matching provision identifiers and their legal texts.
    """
    query = f"""
    PREFIX saont: <https://od2og.africa/ontology/>
    PREFIX sec: <https://od2og.africa/constitution/section/>

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


# ============================================
# FASTAPI WRAPPER (for Railway deployment)
# ============================================

# Create the FastAPI app
app = FastAPI(title="SA Constitution MCP Server")

# Mount the MCP server under /mcp
app.mount("/mcp", mcp.streamable_http_app())


# ----- Server Card (/.well-known/mcp) -----
@app.get("/.well-known/mcp")
async def serve_server_card():
    """Serve the MCP server card for discovery (exact template format)."""
    railway_url = "https://mcp.od2og.africa/"

    card = {
        "serverInfo": {
            "name": "South African Constitution Server",
            "version": "1.0.0"
        },
        "authentication": {
            "required": False,
            "schemes": []
        },
        "tools": [
            {
                "name": "query_constitution",
                "description": "Execute a SPARQL query against the South African Constitution knowledge graph. Converts natural language questions to SPARQL.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sparql_query": {
                            "type": "string",
                            "description": "The SPARQL query string to execute (e.g., 'SELECT ?s WHERE { ?s a saont:Section }')"
                        }
                    },
                    "required": ["sparql_query"]
                }
            },
            {
                "name": "get_section_text",
                "description": "Retrieve the full legal text of a specific section or provision by its identifier.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "section_id": {
                            "type": "string",
                            "description": "The section identifier (e.g., 'sec:21', 'sec:23_2_a', 'sec:36_1')"
                        }
                    },
                    "required": ["section_id"]
                }
            },
            {
                "name": "find_sections_by_keyword",
                "description": "Search for sections or provisions that contain a specific keyword in their legal text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "The keyword to search for (e.g., 'privacy', 'labour', 'detention')"
                        }
                    },
                    "required": ["keyword"]
                }
            }
        ],
        "resources": [],
        "prompts": []
    }

    return Response(content=json.dumps(card, indent=2), media_type="application/json")


# ----- Health Check (/health) -----
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway and Smithery monitoring."""
    return {
        "status": "healthy",
        "endpoint": SPARQL_ENDPOINT,
        "server": "South African Constitution MCP Server",
        "version": "1.0.0"
    }


# ----- Root (/) -----
@app.get("/")
async def root():
    """Root endpoint – provides server information."""
    railway_url = "https://mcp.od2og.africa/"
    return {
        "server": "South African Constitution MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "mcp": f"{railway_url}/mcp",
            "server_card": f"{railway_url}/.well-known/mcp",
            "health": f"{railway_url}/health"
        },
        "documentation": "https://github.com/od2og/constitutionat30"
    }


# ============================================
# RUN THE SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)