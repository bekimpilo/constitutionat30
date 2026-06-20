import re
import httpx
from mcp.server.fastmcp import FastMCP

SECTION_ID_PATTERN = re.compile(r"^[A-Za-z_][\w]*:[\w]+$")


def _escape_sparql_string_literal(value: str) -> str:
    """Escape a value for safe inclusion inside a double-quoted SPARQL string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def register_tools(mcp: FastMCP, sparql_endpoint: str) -> None:
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
        """Execute a SPARQL query against the South African Constitution knowledge graph."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    sparql_endpoint,
                    data={"query": sparql_query},
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                return f"HTTP error: {e.response.status_code}"
            except Exception:
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
        """Retrieve the full legal text of a specific section or provision by its identifier."""
        if not SECTION_ID_PATTERN.match(section_id):
            return (
                "Invalid section_id format. Expected a prefixed name like 'sec:21' "
                "or 'sec:23_2_a'."
            )

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
                    sparql_endpoint,
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
        """Search for provisions containing a specific keyword."""
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
                    sparql_endpoint,
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
                return "Error executing keyword search."
