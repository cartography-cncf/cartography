# Databricks Queries

## Trace Databricks Repositories to GitHub

Databricks repositories connect to their GitHub source when the matching
repository is already present in the graph.

```cypher
MATCH (repo:DatabricksRepo)-[:SOURCED_FROM]->(github:GitHubRepository)
RETURN repo.path, repo.url, github.name
ORDER BY repo.path
```
