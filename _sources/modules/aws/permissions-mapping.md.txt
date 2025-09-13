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
