## Permissions Mapping

### How to use Permissions Mapping
An AWSPrincipal contains AWSPolicies which contain AWSPolicyStatements which grant permission to resources. Cartography can map in permission relationships between IAM Pricipals (AWSPrincipal  nodes) and the resources they have permission to.

As mapping all permissions is infeasible both to calculate and store Cartography will only map in the relationships defined in the [permission relationship file](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml) which includes some default permission mappings including s3 read access.

You can specify your own permission mapping file using the `--permission-relationships-file` command line parameter

#### Permission Mapping File
The [permission relationship file](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml) is a yaml file that specifies what permission relationships should be created in the graph. It consists of RPR (Resource Permission Relationship) sections that are going to map specific permissions between AWSPrincipals and resources
```yaml
- target_label: S3Bucket
  permissions:
  - S3:GetObject
  relationship_name: CAN_READ
```
Each RPR consists of
- ResourceType (string) - The node Label that permissions will be built for
- Permissions (list(string)) - The list of permissions to map. If any of these permissions are present between a resource and a permission then the relationship is created.
- RelationshipName - (string) - The name of the relationship cartography will create

It can also be used to absract many different permissions into one. This example combines all of the permissions that would allow a dynamodb table to be queried.
```yaml
- target_label: DynamoDBTable
  permissions:
  - dynamodb:BatchGetItem
  - dynamodb:GetItem
  - dynamodb:GetRecords
  - dynamodb:Query
  relationship_name: CAN_QUERY
```
If a principal has any of the permission it will be mapped

### IAM policy conditions on permission edges

IAM policy statements can carry a `Condition` block (for example, restricting access to a corporate IP range or requiring MFA). AWS evaluates conditions at request time, so Cartography cannot statically decide whether a conditional grant resolves to allow or deny. Instead, every permission edge is annotated so you can reason about conditional access yourself:

- `has_condition` (bool) - `true` when *every* matching Allow statement that grants the edge is gated by a `Condition`. If any matching Allow grants the access unconditionally, this is `false`.
- `condition_keys` (list of string) - the IAM condition context keys referenced by those conditions, e.g. `["aws:SourceIp", "aws:MultiFactorAuthPresent"]`.
- `conditions` (string) - the raw condition operator maps as a JSON string, for full-fidelity inspection.

Exclude conditionally-gated access from an analysis:
```cypher
MATCH (p:AWSPrincipal)-[r:CAN_READ]->(b:S3Bucket)
WHERE NOT r.has_condition
RETURN p.arn, b.arn
```

Find buckets only reachable when an IP-range condition holds:
```cypher
MATCH (p:AWSPrincipal)-[r:CAN_READ]->(b:S3Bucket)
WHERE r.has_condition AND 'aws:SourceIp' IN r.condition_keys
RETURN p.arn, b.arn, r.conditions
```

> Note: conditions on `Deny` statements are not yet modeled; a conditional `Deny` is currently treated as an absolute deny when computing edges.
