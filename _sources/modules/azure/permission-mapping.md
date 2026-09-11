## Permissions Mapping

### How to use Permissions Mapping
An Azure principal (EntraUser, EntraGroup, or EntraServicePrincipal) can be assigned Azure roles which contain permissions that grant access to Azure resources. Cartography can map permission relationships between Azure principals and the resources they have permission to.

As mapping all permissions is infeasible both to calculate and store, Cartography will only map the relationships defined in the [permission relationship file](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/azure_permission_relationships.yaml) which includes some default permission mappings including SQL Server read access.

You can specify your own permission mapping file using the `--azure-permission-relationships-file` command line parameter

#### Permission Mapping File
The [permission relationship file](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/azure_permission_relationships.yaml) is a yaml file that specifies what permission relationships should be created in the graph. It consists of RPR (Resource Permission Relationship) sections that are going to map specific permissions between Azure principals and resources
```yaml
- target_label: AzureSQLServer
  permissions:
  - Microsoft.Sql/servers/read
  relationship_name: CAN_READ
```
Each RPR consists of
- target_label (string) - The node Label that permissions will be built for
- permissions (list(string)) - The list of permissions to map. If any of these permissions are present between a resource and a principal then the relationship is created.
- relationship_name (string) - The name of the relationship cartography will create

It can also be used to abstract many different permissions into one. This example combines all of the permissions that would allow a SQL server to be managed.
```yaml
- target_label: AzureSQLServer
  permissions:
  - Microsoft.Sql/servers/read
  - Microsoft.Sql/servers/write
  - Microsoft.Sql/servers/delete
  relationship_name: CAN_MANAGE
```
If a principal has any of the permissions it will be mapped
