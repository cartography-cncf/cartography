## AWS Organizations

Cartography models an AWS organization separately from normal account-scoped
resource syncs. The hierarchy consists of `AWSOrganization`,
`AWSOrganizationRoot`, `AWSOrganizationalUnit`, and `AWSAccount` nodes.

### Account lifecycle and placement

Accounts discovered through AWS Organizations retain the lifecycle information
returned by AWS:

- `state` is the current AWS Organizations lifecycle state.
- `status` is the legacy status value. AWS recommends using `state`.
- `joined_method` and `joined_timestamp` describe how and when the account
  joined.
- `org_id` identifies the organization that contains the account.

Configured sync accounts are marked `inscope=true`. An account discovered only
through AWS Organizations is not automatically marked in scope. Use `org_id`
and the placement relationships when querying organization membership.

Only active organization accounts are placed beneath a root or organizational
unit and receive a synced AWS account root principal. Suspended and closed
accounts remain as `AWSAccount` nodes with their organization metadata, but
they are not attached to the active root/OU hierarchy.

Placement is represented in both directions:

```cypher
(:AWSOrganizationRoot)-[:RESOURCE]->(:AWSAccount)
(:AWSOrganizationalUnit)-[:RESOURCE]->(:AWSAccount)
(:AWSAccount)-[:PARENT]->(:AWSOrganizationRoot)
(:AWSAccount)-[:PARENT]->(:AWSOrganizationalUnit)
```

Organizational units can be nested beneath a root or another OU. Root and OU
IDs are scoped to an organization, so Cartography IDs use `{org_id}/{root_id}`
and `{org_id}/{ou_id}`.

Find active account placement:

```cypher
MATCH (org:AWSOrganization)-[:RESOURCE]->(root:AWSOrganizationRoot)
MATCH path = (root)-[:RESOURCE*1..]->(account:AWSAccount)
RETURN org.id, account.id, account.name, account.state,
       [node IN nodes(path) WHERE node:AWSOrganizationalUnit | node.name] AS organizational_units
ORDER BY org.id, account.name
```

Find organization accounts that are retained but not currently placed in the
active hierarchy:

```cypher
MATCH (account:AWSAccount)
WHERE account.org_id IS NOT NULL
  AND NOT (account)-[:PARENT]->(:AWSOrganizationRoot)
  AND NOT (account)-[:PARENT]->(:AWSOrganizationalUnit)
RETURN account.org_id, account.id, account.name, account.state, account.status
ORDER BY account.org_id, account.name
```

### Failure-safe cleanup

Cartography cleans up Organizations hierarchy data only after successfully
enumerating the complete hierarchy. If the Organizations API is unavailable,
access is denied, or enumeration is incomplete, cleanup is skipped so that a
transient failure does not erase the previously known hierarchy.

Organizations cleanup removes stale placement metadata, roots, OUs, and
hierarchy relationships. It does not delete `AWSAccount` nodes or their
account-scoped resources when accounts move, leave the organization, or become
inactive.

For reliable hierarchy syncs, use credentials for the management account or a
delegated administrator account. See [AWS Configuration](config.md)
for credential and multi-account behavior.
