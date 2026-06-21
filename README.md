 Root README.md (Overall Project)
markdown
# 🇿🇦 South African Constitution – Knowledge Graph

**Machine‑readable RDF/Turtle knowledge graph** of the Constitution of the Republic of South Africa, 1996 – covering **Chapter 1 (Founding Provisions, Sections 1–6)** and **Chapter 2 (Bill of Rights, Sections 7–39)**.

This project makes South Africa’s constitutional text available as **linked data** for AI systems, legal research, compliance automation, and GraphRAG applications.

---

## 🔗 Live Endpoints

| Service | URL |
|---------|-----|
| **MCP Server** | `https://mcp.od2og.africa/mcp` |
| **SPARQL Endpoint** | `https://api.triplydb.com/datasets/Od2og/za-constitution/sparql` |
| **Server Card** | `https://mcp.od2og.africa/.well-known/mcp` |
| **Health Check** | `https://mcp.od2og.africa/health` |

---

## 🧱 Ontology Overview

The graph uses a lightweight legal ontology with the following key classes and properties:

| Prefix | URI |
|--------|-----|
| `saont:` | `https://od2og.africa/ontology/` |
| `sec:`   | `https://od2og.africa/constitution/section/` |
| `ch:`    | `https://od2og.africa/constitution/chapter/` |
| `dct:`   | `http://purl.org/dc/terms/` |

| Class / Property | Description |
|------------------|-------------|
| `saont:Chapter` / `saont:Section` | Top‑level containers |
| `saont:Provision` | Individual subsections and lettered items |
| `saont:hasPart` / `saont:partOf` | Hierarchical nesting |
| `saont:orderIndex` | Preserves document order |
| `saont:legalText` | Verbatim legal text |
| `saont:references` | Cross‑references between sections |
| `dct:identifier` | Human‑readable citations (e.g., `"section 23(2)(a)"`) |

---

## 🔍 Use Cases

- **GraphRAG** – Ground AI answers in verifiable, cited constitutional provisions with explicit cross‑references.
- **Fundamental Rights Impact Assessment (FRIA)** – Automate compliance checks using the limitation clause (s36) and the non‑derogable rights table (s37).
- **Semantic Legal Research** – Query by topic, concept, or relationship without manual page‑turning.
- **Legal Tech & Compliance** – Integrate constitutional rights checks into policy, contract, or AI system assessments.

---

## 🚀 Quick Start

### Query via SPARQL (curl)
```bash
curl -X POST "https://api.triplydb.com/datasets/Od2og/za-constitution/sparql" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }"
Use with Claude Desktop (MCP)
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
Restart Claude and ask questions like:

"What does section 23 say about labour rights?"

"Which provisions protect privacy?"

"List all non‑derogable rights."

📂 Repository Structure
text
za-constitution-kg/
├── constitution.ttl              # Core RDF/Turtle knowledge graph
├── mcp-server/                   # MCP server source code
│   ├── server.py
│   ├── requirements.txt
│   └── .env.example
├── .well-known/
│   └── mcp                       # Server discovery card
├── nixpacks.toml                 # Railway build configuration
└── README.md
📜 License
Source text: Official South African Government constitution (public domain).

RDF modelling: Offered freely under the same public‑domain principles. No copyright claimed over the constitutional text.

🤝 Contributing
Issues and pull requests are welcome – especially for:

Adding remaining chapters (Ch 3 and beyond).

Refining cross‑reference resolution.

Extending the ontology with additional legal relations.

🔗 Links
SPARQL-Endpoint: https://api.triplydb.com/datasets/Od2og/za-constitution/sparql

MCP-Server(self-hosted): https://mcp.od2og.africa/mcp

Smithery: [![smithery badge](https://smithery.ai/badge/constitutionat30/rsa)](https://smithery.ai/servers/constitutionat30/rsa)

Maintainer: Beki Ndlovu
Contact: bekisesa@gmail.com

