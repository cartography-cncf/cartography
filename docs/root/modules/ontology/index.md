# Ontology in Cartography

## What is an Ontology?

An ontology is a structured representation of concepts and relationships within a given domain. It enables semantic modeling of knowledge, making it easier to organize, analyze, and query data. In Cartography, the ontology defines entity (node) types and their relationships, using semantic labels and abstract nodes for better interoperability and extensibility.

A key benefit of this approach is that it enables cross-module queries and the export of data in a unified format. By providing a common semantic layer, different modules can interact seamlessly, and data from various sources can be normalized and exported consistently.

### Implementation in Cartography

Cartography implements ontology using two main concepts:
- **Semantic Label**: Each graph node can have one or more semantic labels describing its nature (e.g., `UserAccount`, `DNSRecord`).
- **Abstract Nodes**: Some nodes serve as abstract concepts to group similar entities or define common behaviors. This allows logic to be factored and ensures model consistency.

:::{seealso}
For more background and design rationale, see:
- [Unifying the Graph: Why We Introduced an Ontology in Cartography](https://medium.com/@jychp/unifying-the-graph-why-we-introduced-an-ontology-in-cartography-33b9301de22d)
- [RFC: Cartography Ontology Schema](https://github.com/cartography-cncf/cartography/discussions/1579)
:::

## How Ontology Works in Cartography

The `intel.ontology` module in Cartography manages ontology logic. It allows:
- Loading ontology definitions from JSON files
- Validating the consistency of entities and relationships
- Ensuring mapping between collected data and the defined semantic model

The module provides functions to traverse, enrich, and leverage the ontology during data ingestion. It plays a key role in normalizing entities from heterogeneous sources.

By default, nodes are created in the ontology based on data observed in various modules. For some node, such as User, Device, etc., you can specify "sources of truth" modules that will exclusively create those nodes. This allows for more controlled and accurate representation of certain entities.

**Example: User Nodes and Source of Truth**

If you set the `--ontology-users-source` parameter to `duo`, then a `User` node will be created for every account found in Duo. In contrast, for other integrations like Tailscale, only existing `User` nodes (those created by the source of truth) will be linked to Tailscale accounts. No new `User` nodes will be created from Tailscale data alone.

## Structure of Ontology JSON Files

Ontology files are located in `cartography/data/ontology/`. They use a structure like the following:

```json
{
    "module": {
        "nodes": {
            "NodeName": {
                "ontology_field": "corresponding_field_in_module_node"
            }
        },
        "rels": [
            {
                "__comment__": "These relationships are used to build links between ontology nodes to reflect observed nodes in the modules.",
                "query": "MATCH (u:User)-[:HAS_ACCOUNT]->(:TailscaleUser)-[:OWNS]-(:TailscaleDevice)<-[:OBSERVED_AS]-(d:Device) MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
                "iterative": false
            }
        ]
    }
}
```

- The top-level key (e.g., `tailscale`) groups integration-specific logic.
- The `nodes` section defines node types and their property mappings (this mapping is only used for ingestion).
- The `rels` section lists Cypher queries to connect nodes based on observed data.

This structure allows Cartography to flexibly describe how to map and relate entities from specific integrations into the unified ontology graph.

```{toctree}
config
schema
```
