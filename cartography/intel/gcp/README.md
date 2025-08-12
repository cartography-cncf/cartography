# CloudScope-GCP

Author: Sapna Mohanta

CloudScope-GCP is a GCP ingestion demo intended to show how cloud metadata can be collected
and mapped into a Neo4j graph. The layout and schema are aligned with CNCF Cartography's
intake model so it can be adapted into an upstream contribution.

## Quick start (no secrets included)
1. Copy `.env.example` to `.env` and fill in your own values (do not commit secrets).
2. Install dependencies: `pip install -r requirements.txt`
3. Start Neo4j (example):
   `docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.14`
4. Run ingestion: `python -m gcp_ingestion.gcp_resources`

## Files of interest
- `gcp_ingestion/gcp_resources.py` -- main ingestion logic
- `gcp_ingestion/schema.yaml` -- schema example for nodes and relationships
- `CONTRIBUTING_CLOUDSCOPE.md` -- guide showing how to upstream into Cartography

## Cartography alignment
- Schema and node names are chosen to be compatible with Cartography conventions.
- Use the CONTRIBUTING guide to prepare code for upstreaming.

## Demo
See `docs/demo_run.gif` and `docs/neo4j_query_example.png` for visual walkthroughs.
