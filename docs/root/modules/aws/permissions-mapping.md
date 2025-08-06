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
- RelationshipName (string) - The name of the relationship cartography will create
- **[OPTIONAL]** ConditionalRelations (list(string)) - Additional relations the node label must have when defining relationships. Defaults to None.
- **[OPTIONAL]** resource_arn_schema (string) - The schema pattern for constructing resource ARNs from node properties. Uses `{{property}}` placeholders to reference node properties. Defaults to '{{arn}}'.

#### Resource ARN Schema
The `resource_arn_schema` field allows you to define how resource ARNs should be constructed from target node properties. This is useful when the node's `arn` property doesn't match the format expected by IAM policies. Like in the case of EC2 instances.

**Examples:**
- `"{{arn}}"` - Uses the node's `arn` property directly (default)
- `"arn:aws:ec2:{{region}}:*:instance/{{instanceid}}"` - Constructs EC2 instance ARNs from separate properties
- `"arn:aws:s3:::{{bucketname}}/*"` - Constructs S3 bucket ARNs from the bucket name property

The system will automatically extract the required properties from the node and construct the ARN for permission evaluation.

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

This example shows how to map SSM access permissions for EC2 instances with conditional relationships and custom resource ARN schema.
```yaml
- target_label: EC2Instance
  permissions:
  - ssm:StartSession
  relationship_name: CAN_SSM_ACCESS
  conditional_target_relations:
  - HAS_INFORMATION
  resource_arn_schema: "arn:aws:ec2:{{region}}:*:instance/{{instanceid}}"
```
