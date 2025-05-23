# Cartography Schema

## ℹ️ Quick notes on notation
- **Bolded words** in the schema tables indicate that this field is indexed, so your queries will run faster if you use these fields.

- This isn't proper Neo4j syntax, but for the purpose of this document we will use this notation:

	```
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeB, NodeTypeC, NodeTypeD, NodeTypeE)
	```

	to mean a shortened version of this:

	```
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeB)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeC)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeD)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeE)
	```

	In words, this means that `NodeTypeA` has `RELATIONSHIP_R` pointing to `NodeTypeB`, and `NodeTypeA` has `RELATIONSHIP_R` pointing to `NodeTypeC`.

- In these docs, more specific nodes will be decorated with `GenericNode::SpecificNode` notation. For example, if we have a `Car` node and a `RaceCar` node, we will refer to the `RaceCar` as `Car::RaceCar`.


```{include} ../modules/_cartography-metadata/schema.md
```

```{include} ../modules/anthropic/schema.md
```

```{include} ../modules/aws/schema.md
```

```{include} ../modules/azure/schema.md
```

```{include} ../modules/bigfix/schema.md
```

```{include} ../modules/cloudflare/schema.md
```

```{include} ../modules/crowdstrike/schema.md
```

```{include} ../modules/cve/schema.md
```

```{include} ../modules/digitalocean/schema.md
```

```{include} ../modules/duo/schema.md
```

```{include} ../modules/gcp/schema.md
```

```{include} ../modules/github/schema.md
```

```{include} ../modules/gsuite/schema.md
```

```{include} ../modules/jamf/schema.md
```

```{include} ../modules/kandji/schema.md
```

```{include} ../modules/kubernetes/schema.md
```

```{include} ../modules/lastpass/schema.md
```

```{include} ../modules/oci/schema.md
```

```{include} ../modules/okta/schema.md
```

```{include} ../modules/openai/schema.md
```

```{include} ../modules/pagerduty/schema.md
```

```{include} ../modules/semgrep/schema.md
```

```{include} ../modules/snipeit/schema.md
```

```{include} ../modules/tailscale/schema.md
```
