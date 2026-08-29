## Permissions Mapping

### How to use Permissions Mapping
A GCP principal (GCPUser, GCPServiceAccount, or GCPGroup) can be assigned GCP roles which contain permissions that grant access to GCP resources. Cartography can map permission relationships between GCP principals and the resources they have permission to.

As mapping all permissions is infeasible both to calculate and store, Cartography will only map the relationships defined in the [permission relationship file](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/gcp_permission_relationships.yaml) which includes some default permission mappings including GCP Bucket read access.

You can specify your own permission mapping file using the `--gcp-permission-relationships-file` command line parameter

Permission relationship syncs depend on policy bindings being refreshed in the same GCP sync run. In the normal GCP sync flow, those policy bindings come from the CAI-backed policy bindings sync, which passes the current policy-binding context directly into permission relationship evaluation.

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

#### IAM conditions on permission edges

GCP IAM bindings can carry a [condition](https://cloud.google.com/iam/docs/conditions-overview) (a CEL expression, e.g. restricting access to business hours or a resource tag). These bindings used to be dropped, which understated access. They are now retained and the resulting permission edge is annotated so you can reason about conditional access. GCP evaluates conditions at request time, so cartography cannot statically decide whether the condition holds.

- `has_condition` (bool) - `true` when every binding that grants the edge is conditional. If any matching binding grants the access unconditionally, this is `false`.
- `condition_title` (string) - the title(s) of the matching condition(s).
- `condition_expression` (string) - the CEL expression(s) of the matching condition(s).

Exclude conditionally-gated access from an analysis:
```cypher
MATCH (p:GCPPrincipal)-[r:CAN_READ]->(b:GCPBucket)
WHERE NOT r.has_condition
RETURN p.email, b.id
```

> Note: conditional grants are always evaluated per-resource (row-by-row), so they carry their condition metadata; broad unconditional grants are bulk-loaded and set `has_condition = false` explicitly (clearing any stale metadata if the same edge was previously conditional).

#### Supported principal types

Permission edges are created for `user:`, `serviceAccount:` (including GKE Workload Identity service accounts of the form `serviceAccount:{project}.svc.id.goog[...]`), and `group:` members. Other member types are retained for visibility rather than dropped:

- `allUsers` / `allAuthenticatedUsers` set `is_public = true` on the `GCPPolicyBinding` (these never resolve to a real principal node).
- Workload Identity Federation members (`principal://` / `principalSet://`) are recorded in `GCPPolicyBinding.wif_pools`.
- `domain:{domain}` members are recorded in `GCPPolicyBinding.domains`.

#### Expanding group permissions to members

A `group:` member resolves to a `GoogleWorkspaceGroup`, which also carries the `GCPPrincipal` label, so the permission edge attaches directly to the group node. Group membership is already in the graph as `(:GoogleWorkspaceUser)-[:MEMBER_OF]->(:GoogleWorkspaceGroup)` (and `INHERITED_MEMBER_OF` for nested groups), so you expand a group's permissions to its effective members by traversing those edges, no separate materialization is needed:

```cypher
MATCH (u:GoogleWorkspaceUser)-[:MEMBER_OF|INHERITED_MEMBER_OF]->(g:GCPPrincipal)-[r:CAN_READ]->(b:GCPBucket)
RETURN u.email AS user, g.email AS via_group, b.id AS bucket
```
