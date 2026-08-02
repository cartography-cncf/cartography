# Syft Queries

## Browse the dependency tree

```cypher
MATCH path = (p:SyftPackage)-[:DEPENDS_ON*1..5]->(dep:SyftPackage)
WHERE NOT exists((p)<-[:DEPENDS_ON]-())
RETURN path
```

## Find packages that depend on a specific package

```cypher
MATCH (upstream:SyftPackage)-[:DEPENDS_ON*1..10]->(dep:SyftPackage {name: 'lodash'})
RETURN DISTINCT upstream.name
```

## Find root packages

```cypher
MATCH (p:SyftPackage)
WHERE NOT exists((p)<-[:DEPENDS_ON]-())
RETURN p.name
```

## Find nested packages

```cypher
MATCH (p:SyftPackage)
WHERE exists((p)<-[:DEPENDS_ON]-())
RETURN p.name
```
