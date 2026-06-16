
"""
MCP Server for the South African Constitution Knowledge Graph.
Connects to the public TriplyDB SPARQL endpoint.
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("South African Constitution Server")

# Load environment variables from the current environment or a local .env file
load_dotenv()

SPARQL_ENDPOINT = os.getenv("SPARQL_ENDPOINT")
if not SPARQL_ENDPOINT:
    raise RuntimeError("SPARQL_ENDPOINT environment variable is not set. Set it in the environment or a .env file.")

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
                # Truncate long text for readability
                if len(text) > 200:
                    text = text[:200] + "..."
                results.append(f"{provision}: {text}")
            return "\n\n".join(results)
        except Exception as e:
            return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")