## AWS Identity and Access Investigations

Cartography distinguishes configured permission from observed role use. This
matters for IAM and AWS Identity Center investigations because a principal can
be permitted to assume many roles while using only a subset.

### CloudTrail role-assumption evidence

CloudTrail management events produce relationships that summarize observed
role assumptions during the configured lookback window.

Standard `AssumeRole` events connect an AWS principal to an IAM role:

```cypher
(:AWSPrincipal)-[:ASSUMED_ROLE {
  times_used,
  first_seen,
  last_seen,
  lastused
}]->(:AWSRole)
```

SAML assumptions connect an Identity Center user to the role that was used:

```cypher
(:AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML {
  times_used,
  first_seen_in_time_window,
  last_used,
  lastupdated
}]->(:AWSRole)
```

GitHub Actions web-identity assumptions use the same window-oriented property
names:

```cypher
(:GitHubRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY {
  times_used,
  first_seen_in_time_window,
  last_used,
  lastupdated
}]->(:AWSRole)
```

Generic web-identity providers are not currently modeled by that relationship.
Take care with the property names: the standard, SAML, and web-identity
relationships do not use one common timestamp vocabulary.

### Identity Center assignments

`AWSIdentityCenter` owns `AWSPermissionSet` nodes. A permission set creates an
`AWSRole` in each account where it is assigned:

```cypher
(:AWSIdentityCenter)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)
(:AWSPermissionSet)-[:ASSIGNED_TO_ROLE]->(:AWSRole)
```

Users and groups receive `HAS_ROLE` summary relationships to permission sets.
These show that the permission set is available, but they do not identify the
specific account assignment. Account-specific role access is represented by
`ALLOWED_BY`:

```cypher
(:AWSSSOUser)-[:HAS_ROLE]->(:AWSPermissionSet)
(:AWSSSOGroup)-[:HAS_ROLE]->(:AWSPermissionSet)
(:AWSRole)-[:ALLOWED_BY]->(:AWSSSOUser)
(:AWSRole)-[:ALLOWED_BY]->(:AWSSSOGroup)
```

`AWSSSOUser` access includes direct assignments and assignments inherited
through `AWSSSOGroup` membership. The AWS Identity Center
`list_account_assignments_for_principal` API resolves group membership
server-side. As a result, a user can have direct `HAS_ROLE` and `ALLOWED_BY`
edges even when the underlying assignment was made only to a group. Keep the
`MEMBER_OF` and group assignment paths when the assignment source matters.

Find a user's permitted account roles and the permission sets that created
them:

```cypher
MATCH (user:AWSSSOUser {id: $user_id})<-[:ALLOWED_BY]-(role:AWSRole)
MATCH (permission_set:AWSPermissionSet)-[:ASSIGNED_TO_ROLE]->(role)
MATCH (account:AWSAccount)-[:RESOURCE]->(role)
RETURN account.id, account.name, role.arn,
       permission_set.name, permission_set.arn
ORDER BY account.name, permission_set.name
```

Show group paths that can explain inherited access:

```cypher
MATCH (user:AWSSSOUser {id: $user_id})-[:MEMBER_OF]->(group:AWSSSOGroup)
MATCH (group)-[:HAS_ROLE]->(permission_set:AWSPermissionSet)
MATCH (permission_set)-[:ASSIGNED_TO_ROLE]->(role:AWSRole)
WHERE (role)-[:ALLOWED_BY]->(user)
RETURN group.display_name, permission_set.name, role.arn
ORDER BY group.display_name, permission_set.name
```

### Permitted access versus actual use

`ALLOWED_BY` represents permitted account-role access. CloudTrail-derived
`ASSUMED_ROLE_WITH_SAML` represents actual use. Compare them to find permitted
roles that were not observed during the lookback window:

```cypher
MATCH (user:AWSSSOUser {id: $user_id})<-[:ALLOWED_BY]-(role:AWSRole)
WHERE NOT (user)-[:ASSUMED_ROLE_WITH_SAML]->(role)
MATCH (account:AWSAccount)-[:RESOURCE]->(role)
RETURN account.id, role.arn
ORDER BY account.id, role.arn
```

The absence of an observed edge is not proof that a role has never been used.
It is limited by CloudTrail availability, event coverage, and the configured
lookback window.

Summarize observed use:

```cypher
MATCH (user:AWSSSOUser)-[usage:ASSUMED_ROLE_WITH_SAML]->(role:AWSRole)
RETURN user.user_name, role.arn, usage.times_used,
       usage.first_seen_in_time_window, usage.last_used
ORDER BY usage.last_used DESC
```

### Okta and Entra federation

Federated identity paths connect external identity providers to Identity
Center users:

```cypher
(:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)
(:UserAccount)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)
(:EntraUser)-[:CAN_SIGN_ON_TO]->(:AWSSSOUser)
(:EntraServicePrincipal)-[:FEDERATES_TO]->(:AWSIdentityCenter)
```

For an Okta user, combine federation, permitted access, and actual use:

```cypher
MATCH (external:OktaUser)-[:CAN_ASSUME_IDENTITY]->(user:AWSSSOUser)
OPTIONAL MATCH (user)<-[:ALLOWED_BY]-(permitted:AWSRole)
OPTIONAL MATCH (user)-[usage:ASSUMED_ROLE_WITH_SAML]->(used:AWSRole)
RETURN external.login, user.user_name,
       collect(DISTINCT permitted.arn) AS permitted_roles,
       collect(DISTINCT {
         role: used.arn,
         times_used: usage.times_used,
         last_used: usage.last_used
       }) AS observed_role_use
```

For Entra, begin with `EntraUser-[:CAN_SIGN_ON_TO]->AWSSSOUser` and apply the
same permission and usage patterns.
