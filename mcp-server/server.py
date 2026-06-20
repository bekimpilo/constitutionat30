"""
MCP Server for the South African Constitution Knowledge Graph.
Deployed on Railway with FastAPI wrapper, health check, and server card.
"""

import os
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

# ============================================
# MCP TOOLS 
# ============================================

from tools import register_tools

register_tools(mcp, SPARQL_ENDPOINT)


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