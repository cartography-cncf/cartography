# Terraform Schema

## TerraformWorkspace

Represents a single Terraform state file. One node per state file, keyed on the stable `lineage` UUID.

| Field | Description |
|-------|-------------|
| id | The `lineage` UUID from the state file |
| lineage | Same as id |
| terraform_version | Terraform CLI version that wrote the state |
| serial | Monotonically increasing state serial number |
| workspace_name | Derived from the state file's filename |
| source_uri | Full URI where the state file was read from |
| lastupdated | Cartography sync timestamp |

## TerraformResource

Represents a single `resource {}` block in a Terraform configuration (the logical resource, not a specific instance).

| Field | Description |
|-------|-------------|
| id | `{module}.{type}.{name}` or `{type}.{name}` when no module |
| resource_type | Terraform resource type, e.g. `aws_s3_bucket` |
| resource_name | Label within the Terraform config, e.g. `logs` |
| module_path | Module prefix, e.g. `module.eks`; empty string for root |
| mode | `managed` or `data` |
| provider | Normalized provider slug, e.g. `hashicorp/aws` |
| lastupdated | Cartography sync timestamp |

## TerraformResourceInstance

Represents a single instance within a `resource {}` block (one entry in `instances[]`). For resources without `count` or `for_each` this is 1:1 with `TerraformResource`.

| Field | Description |
|-------|-------------|
| id | `{resource_id}[{index_key}]` or `{resource_id}` when no index |
| index_key | The `count` index or `for_each` key; null when absent |
| attributes_id | Value of `attributes.id` or `attributes.arn` — the cloud resource identifier |
| resource_type | Same as parent `TerraformResource.resource_type` |
| tags_json | JSON-serialized tags map; null when empty |
| lastupdated | Cartography sync timestamp |

## TerraformOutput

Represents a single `output {}` value exported from the state file.

| Field | Description |
|-------|-------------|
| id | `{lineage}::{output_name}` |
| output_name | The output block label |
| value_type | Terraform type annotation, e.g. `string`, `object` |
| sensitive | `true` when the output is marked sensitive |
| value_json | JSON-serialized value; **always null when sensitive=true** |
| lastupdated | Cartography sync timestamp |

## Relationships

| Relationship | From | To | Description |
|---|---|---|---|
| `CONTAINS` | `TerraformWorkspace` | `TerraformResource` | All resources declared in this state file |
| `HAS_INSTANCE` | `TerraformResource` | `TerraformResourceInstance` | All instances of the resource block |
| `DEPENDS_ON` | `TerraformResource` | `TerraformResource` | Declared dependency edges from `instance.dependencies` |
| `HAS_OUTPUT` | `TerraformWorkspace` | `TerraformOutput` | All outputs exported by this state file |
| `MANAGES` | `TerraformResourceInstance` | AWS node | Cross-link to an existing AWS node when `attributes_id` matches |

### Supported MANAGES targets

| Terraform resource_type | Target Neo4j label |
|---|---|
| `aws_s3_bucket` | `S3Bucket` |
| `aws_instance` | `EC2Instance` |
| `aws_eks_cluster` | `EKSCluster` |
| `aws_db_instance` | `RDSInstance` |
| `aws_iam_role` | `AWSRole` |
| `aws_iam_policy` | `AWSManagedPolicy` |
| `aws_security_group` | `EC2SecurityGroup` |

## Example Queries

```cypher
// Is my S3 bucket managed by Terraform?
MATCH (b:S3Bucket {id: "my-logs-bucket"})<-[:MANAGES]-(i:TerraformResourceInstance)
RETURN b.id, i.id

// All unmanaged S3 buckets
MATCH (b:S3Bucket)
WHERE NOT (b)<-[:MANAGES]-(:TerraformResourceInstance)
RETURN b.id

// All resources in a workspace
MATCH (ws:TerraformWorkspace)-[:CONTAINS]->(r:TerraformResource)
RETURN ws.workspace_name, r.id, r.resource_type, r.mode
ORDER BY r.resource_type
```
