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

## Conventions

### Python Object Naming Conventions

* **Node classes** should end with `Schema`
* **Relationship classes** should end with `Rel`
* **Node property classes** should end with `Properties`
* **Relationship property classes** should end with `RelProperties`

### Sub-Resources

A *sub-resource* is a specific type of composition relationship in which a node "belongs to" a higher-level entity such as an Account, Subscription, etc.

Examples:

* In **AWS**, the parent is typically an `AWSAccount`.
* In **Azure**, it's a `Tenant` or `Subscription`.
* In **GCP**, it's a `GCPProject`.

To define a sub-resource relationship, use the `sub_resource_relationship` property on the node class. It must follow these constraints:

* The target node matcher must have `set_in_kwargs=True` (required for auto-cleanup functionality).
* All `sub_resource_relationship`s must:

  * Use the label `RESOURCE`
  * Have the direction set to `INWARD`
* Each module:

  * **Must have at least one root node** (a node without a `sub_resource_relationship`)
  * **Must have at most one root node**

### Common Relationship Types

While you're free to define custom relationships, using standardized types improves maintainability and facilitates querying and analysis.

#### Composition

* `(:Parent)-[:CONTAINS]->(:Child)`
* `(:Parent)-[:HAS]->(:Child)`

#### Tagging

* `(:Entity)-[:TAGGED]->(:Tag)`

#### Group Membership

* `(:Element)-[:MEMBER_OF]->(:Group)`
* `(:Element)-[:ADMIN_OF]->(:Group)`
    ```{note}
    If an element is an admin, both relationships (`MEMBER_OF` and `ADMIN_OF`) should be present for consistency.
    ```

#### Ownership

* `(:Entity)-[:OWNS]->(:OtherEntity)`

#### Permissions (ACL)

* `(:Actor)-[:CAN_ACCESS]->(:Entity)`
* `(:Actor)-[:CAN_READ]->(:Entity)`
* `(:Actor)-[:CAN_WRITE]->(:Entity)`
* `(:Actor)-[:CAN_ADD]->(:Entity)`
* `(:Actor)-[:CAN_DELETE]->(:Entity)`


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

```{include} ../modules/entra/schema.md
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
