"""
MCP Server for the South African Constitution Knowledge Graph.
Deployed on Railway with FastAPI wrapper, health check, and server card.
"""

import os
import re
import json
import logging
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env
load_dotenv()

# Configure logging. LOG_LEVEL can be overridden via env (e.g. "DEBUG" while
# diagnosing an issue, "INFO"/"WARNING" in normal production use).
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("sa_constitution_server")

# Initialize the MCP server
mcp = FastMCP("South African Constitution Server")

# Read SPARQL endpoint from environment, with fallback default
SPARQL_ENDPOINT = os.getenv(
    "SPARQL_ENDPOINT",
    "https://api.triplydb.com/datasets/Od2og/za-constitution/sparql"
)

# Public base URL of this server, used in the server card / root endpoint.
# This is your custom domain (not Railway's auto-generated *.up.railway.app
# address). Required — no hardcoded fallback, since baking a specific
# domain into source code is what we're trying to avoid here.
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
if not PUBLIC_BASE_URL:
    raise RuntimeError(
        "PUBLIC_BASE_URL environment variable must be set "
        "(e.g. 'https://mcp.od2og.africa') so the server card and root "
        "endpoint can advertise the correct public address."
    )
PUBLIC_BASE_URL = PUBLIC_BASE_URL.rstrip("/")

logger.info("Using SPARQL endpoint: %s", SPARQL_ENDPOINT)

# Valid prefixed-name pattern for section identifiers, e.g. "sec:21", "sec:23_2_a"
SECTION_ID_PATTERN = re.compile(r"^[A-Za-z_][\w]*:[\w]+$")


def _escape_sparql_string_literal(value: str) -> str:
    """Escape a value for safe inclusion inside a double-quoted SPARQL string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


# ============================================
# MCP TOOLS 
# ============================================

@mcp.tool(
    name="sparql",
    description="Execute a SPARQL query against the South African Constitution knowledge graph.",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sparql(sparql_query: str) -> str:
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
            logger.warning("sparql HTTP error %s: %s", e.response.status_code, e.response.text)
            return f"HTTP error: {e.response.status_code}"
        except Exception:
            logger.exception("sparql failed for query: %s", sparql_query)
            return "Error executing query."


@mcp.tool(
    name="get_text",
    description="Retrieve the full legal text of a specific provision by its identifier (e.g., 'sec:21', 'sec:23_2_a').",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_text(section_id: str) -> str:
    """
    Retrieve the full legal text of a specific section or provision by its identifier.

    Args:
        section_id: The section identifier as a SPARQL prefixed name
            (e.g., "sec:21", "sec:23_2_a", "sec:36_1").

    Returns:
        The legal text of the specified provision.
    """
    if not SECTION_ID_PATTERN.match(section_id):
        return (
            "Invalid section_id format. Expected a prefixed name like 'sec:21' "
            "or 'sec:23_2_a'."
        )

    # NOTE: section_id is a SPARQL prefixed name (e.g. "sec:21"), so it must be
    # used as-is, NOT wrapped in angle brackets. Angle brackets denote a full
    # IRI in SPARQL, which would bypass the PREFIX declaration entirely and
    # never match anything in the graph.
    query = f"""
    PREFIX saont: <https://od2og.africa/ontology/>
    PREFIX sec: <https://od2og.africa/constitution/section/>

    SELECT ?text WHERE {{
        {section_id} saont:legalText ?text .
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
        except Exception:
            logger.exception("get_text failed for section_id: %s", section_id)
            return "Error retrieving section text."


@mcp.tool(
    name="search",
    description="Search all constitutional provisions for a keyword (e.g., 'privacy', 'labour', 'detention') and return matching texts.",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def search(keyword: str) -> str:
    """
    Search for sections or provisions that contain a specific keyword in their legal text.

    Args:
        keyword: The keyword to search for (e.g., "privacy", "labour", "detention").

    Returns:
        A list of matching provision identifiers and their legal texts.
    """
    safe_keyword = _escape_sparql_string_literal(keyword)
    query = f"""
    PREFIX saont: <https://od2og.africa/ontology/>
    PREFIX sec: <https://od2og.africa/constitution/section/>

    SELECT ?provision ?text WHERE {{
        ?provision saont:legalText ?text .
        FILTER(REGEX(LCASE(?text), LCASE("{safe_keyword}"), "i"))
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
        except Exception:
            logger.exception("search failed for keyword: %s", keyword)
            return "Error executing keyword search."


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
                "name": "sparql",
                "description": "Execute a SPARQL query against the South African Constitution knowledge graph.",
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
                "name": "get_text",
                "description": "Retrieve the full legal text of a specific provision by its identifier (e.g., 'sec:21', 'sec:23_2_a').",
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
                "name": "search",
                "description": "Search all constitutional provisions for a keyword (e.g., 'privacy', 'labour', 'detention') and return matching texts.",
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


# ----- Server Card (exact path for Smithery) -----
@app.get("/.well-known/mcp/server-card.json")
async def serve_server_card_exact():
    """Serve the MCP server card at the exact path Smithery expects."""
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
                "name": "sparql",
                "description": "Execute a SPARQL query against the South African Constitution knowledge graph.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sparql_query": {
                            "type": "string",
                            "description": "The SPARQL query string to execute"
                        }
                    },
                    "required": ["sparql_query"]
                }
            },
            {
                "name": "get_text",
                "description": "Retrieve the full legal text of a specific provision by its identifier.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "section_id": {
                            "type": "string",
                            "description": "The section identifier (e.g., 'sec:21')"
                        }
                    },
                    "required": ["section_id"]
                }
            },
            {
                "name": "search",
                "description": "Search for provisions containing a specific keyword.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "The keyword to search for"
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
    """Health check endpoint for Railway and Smithery monitoring.

    Actually pings the SPARQL endpoint with a cheap ASK query so that a
    backend outage is reflected here, rather than always reporting healthy.
    """
    sparql_ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                SPARQL_ENDPOINT,
                data={"query": "ASK { ?s ?p ?o }"},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            sparql_ok = response.status_code == 200
    except Exception:
        logger.exception("Health check: SPARQL endpoint unreachable")
        sparql_ok = False

    payload = {
        "status": "healthy" if sparql_ok else "degraded",
        "endpoint": SPARQL_ENDPOINT,
        "sparql_reachable": sparql_ok,
        "server": "South African Constitution MCP Server",
        "version": "1.0.0"
    }
    return JSONResponse(content=payload, status_code=200 if sparql_ok else 503)


@app.get("/")
async def root():
    """Root endpoint – provides server information."""
    return {
        "server": "South African Constitution MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "mcp": f"{PUBLIC_BASE_URL}/mcp",
            "server_card": f"{PUBLIC_BASE_URL}/.well-known/mcp",
            "server_card_json": f"{PUBLIC_BASE_URL}/.well-known/mcp/server-card.json",
            "health": f"{PUBLIC_BASE_URL}/health"
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