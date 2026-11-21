# AIBOM Examples

## Find production images containing AI agents

```cypher
MATCH (source:AIBOMSource)-[:SCANNED_IMAGE]->(image:Image)
MATCH (source)-[:HAS_COMPONENT]->(component:AIBOMComponent:AIAgent)
RETURN source.image_uri, image._ont_digest, collect(component.name) AS agents
```

## Find components detected in an image

```cypher
MATCH (image:Image)<-[:DETECTED_IN]-(component:AIBOMComponent)
RETURN image._ont_digest, component.category, component.name
ORDER BY component.category, component.name
```

## Find components detected in a repository

```cypher
MATCH (source:AIBOMSource)-[:SCANNED_REPOSITORY]->(repository)
MATCH (source)-[:HAS_COMPONENT]->(component:AIBOMComponent)
WHERE repository:GitHubRepository OR repository:GitLabProject
RETURN labels(repository), source.source_key, component.category, component.name
ORDER BY source.source_key, component.category, component.name
```

## Inspect component relationships

```cypher
MATCH (source:AIBOMSource)-[:HAS_COMPONENT]->(source_component:AIBOMComponent)
MATCH (source_component)-[relationship]->(target_component:AIBOMComponent)
WHERE type(relationship) IN ['USES_MODEL', 'USES_TOOL', 'EXPOSES_TOOL', 'CUSTOM']
RETURN
  source.source_key,
  source_component.name,
  type(relationship),
  target_component.name
ORDER BY source_component.name, type(relationship), target_component.name
```

## Group equivalent components across rebuilds

```cypher
MATCH (component:AIBOMComponent)
RETURN
  component.logical_id,
  collect(DISTINCT component.name) AS names,
  count(*) AS detections
ORDER BY detections DESC
```
