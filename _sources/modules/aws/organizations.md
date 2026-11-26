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

### Service control policies

When the organization has all features enabled, Cartography syncs its service
control policies (SCPs) as `AWSServiceControlPolicy` nodes. Each policy keeps
its raw policy document in `content`, and each statement in that document is an
`AWSServiceControlPolicyStatement` node. AWS managed policies such as
`FullAWSAccess` have the same ID in every organization, so policy IDs use
`{org_id}/{policy_id}`.

```cypher
(:AWSOrganization)-[:RESOURCE]->(:AWSServiceControlPolicy)
(:AWSServiceControlPolicy)-[:APPLIES_TO]->(:AWSOrganizationRoot)
(:AWSServiceControlPolicy)-[:APPLIES_TO]->(:AWSOrganizationalUnit)
(:AWSServiceControlPolicy)-[:APPLIES_TO]->(:AWSAccount)
(:AWSServiceControlPolicy)-[:STATEMENT]->(:AWSServiceControlPolicyStatement)
```

`APPLIES_TO` is the direct attachment. An account is also governed by every
SCP attached to its parent OUs and root. Only active accounts are placed in the
hierarchy, so the inherited results below cover active accounts; suspended and
closed accounts show only SCPs attached to them directly.

SCPs do not affect the organization's management account, even when they are
attached to the root or to the management account itself. Exclude it when
asking which accounts a policy governs.

Find the SCPs that govern each account, directly or through its parents:

```cypher
MATCH (account:AWSAccount)-[:PARENT*0..]->(target)<-[:APPLIES_TO]-(scp:AWSServiceControlPolicy)
MATCH (org:AWSOrganization {id: scp.org_id})
WHERE account.id <> org.management_account_id
RETURN account.id, account.name, collect(DISTINCT scp.name) AS service_control_policies
ORDER BY account.name
```

Find deny statements that restrict regions:

```cypher
MATCH (scp:AWSServiceControlPolicy)-[:STATEMENT]->(statement:AWSServiceControlPolicyStatement)
WHERE statement.effect = 'Deny'
  AND statement.condition CONTAINS 'aws:RequestedRegion'
RETURN scp.org_id, scp.name, statement.sid, statement.condition
```

Cartography does not yet evaluate SCPs when it computes effective permissions.

### Failure-safe cleanup

Cartography cleans up Organizations hierarchy data only after successfully
enumerating the complete hierarchy. If the Organizations API is unavailable,
access is denied, or enumeration is incomplete, cleanup is skipped so that a
transient failure does not erase the previously known hierarchy.

If the hierarchy syncs but the service control policies cannot be enumerated,
for example because a delegated administrator is not allowed to read policies,
Cartography keeps the previously synced policies and skips policy cleanup.
Policies are read with the same account that synced the hierarchy, which is the
management account when it is among the synced accounts. Cartography does not
retry other accounts for policies alone, to avoid repeated denied Organizations
calls from member accounts.

Organizations cleanup removes stale placement metadata, roots, OUs, service
control policies, and hierarchy relationships. It does not delete `AWSAccount` nodes or their
account-scoped resources when accounts move, leave the organization, or become
inactive.

For reliable hierarchy syncs, use credentials for the management account or a
delegated administrator account. See [AWS Configuration](config.md)
for credential and multi-account behavior.
