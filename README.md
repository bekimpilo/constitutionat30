# constitution@30


markdown
# 🇿🇦 South African Constitution – Knowledge Graph (Ch 1 & 2)

RDF/Turtle knowledge graph of the South African Constitution, 1996 – **Founding Provisions** (Sections 1–6) and **Bill of Rights** (Sections 7–39).

---

## 🚀 Quick Start

### Query via SPARQL (no install)
```bash
curl -X POST "https://api.triplydb.com/datasets/Od2og/za-constitution/sparql" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }"
Endpoint: https://api.triplydb.com/datasets/Od2og/za-constitution/sparql

Use with Claude (MCP Server)
bash
npx -y @smithery/cli install @yourusername/za-constitution-mcp --client claude

🧱 Ontology
Prefix	URI
saont:	https://od2og.africa/ontology/
sec:	https://od2og.africa/constitution/section/
ch:	https://od2og.africa/constitution/chapter/
dct:	http://purl.org/dc/terms/
Key properties: saont:hasPart, saont:orderIndex, saont:legalText, saont:references

🔍 Use Cases
GraphRAG – Ground AI answers in verifiable constitutional text with explicit cross‑references.

Fundamental Rights Impact Assessment (FRIA) – Automate compliance checks using the limitation clause (s36) and non‑derogable rights table (s37).

Semantic Search – Query by topic, keyword, or legal concept without manual page‑turning.

📜 License
Public domain / open data. No copyright claimed over the constitutional text.

🤝 Contributing
Issues and PRs welcome – extend to other chapters, refine references, or enhance the ontology.

Data sources (official gov.za):

Chapter 1: https://www.gov.za/documents/constitution/chapter-1-founding-provisions

Chapter 2: https://www.gov.za/documents/constitution/chapter-2-bill-rights

Maintainer: Beki Ndlovu
Issues: https://github.com/od2og/constitutionat30/issues

@2026
