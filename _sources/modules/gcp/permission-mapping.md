## Permissions Mapping

### How to use Permissions Mapping
A GCP principal (GCPUser, GCPServiceAccount, or GCPGroup) can be assigned GCP roles which contain permissions that grant access to GCP resources. Cartography can map permission relationships between GCP principals and the resources they have permission to.

As mapping all permissions is infeasible both to calculate and store, Cartography will only map the relationships defined in the [permission relationship file](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/gcp_permission_relationships.yaml) which includes some default permission mappings including GCP Bucket read access.

You can specify your own permission mapping file using the `--gcp-permission-relationships-file` command line parameter

#### Permission Mapping File
The [permission relationship file](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/gcp_permission_relationships.yaml) is a yaml file that specifies what permission relationships should be created in the graph. It consists of RPR (Resource Permission Relationship) sections that are going to map specific permissions between GCP principals and resources
```yaml
- target_label: GCPBucket
  permissions:
  - storage.objects.get
  relationship_name: CAN_READ
```
Each RPR consists of
- target_label (string) - The node Label that permissions will be built for
- permissions (list(string)) - The list of permissions to map. If any of these permissions are present between a resource and a principal then the relationship is created.
- relationship_name (string) - The name of the relationship cartography will create

It can also be used to abstract many different permissions into one. This example combines all of the permissions that would allow a GCP Bucket to be managed.
```yaml
- target_label: GCPBucket
  permissions:
  - storage.objects.get
  - storage.objects.create
  - storage.objects.update
  - storage.objects.delete
  relationship_name: CAN_MANAGE
```
If a principal has any of the permissions it will be mapped
