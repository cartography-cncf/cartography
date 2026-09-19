# Jira Queries

## Accounts in API-reported admin groups

```cypher
MATCH (u:JiraUser)-[:MEMBER_OF]->(g:JiraGroup)-[:ADMIN_OF]->(t:JiraTenant)
WHERE u.active = true
RETURN t.name, u.display_name, u.email, g.name, g.admin_access_types
```

This lists active accounts in admin/site-admin groups reported by Jira. It is
not an exhaustive effective-global-permission evaluation.

## Configured project browse and administration grants

```cypher
MATCH (u:JiraUser)-[:MEMBER_OF*0..2]->(holder)
      -[:HAS_PERMISSION]->(grant:JiraPermissionGrant)
      -[:APPLIES_TO]->(p:JiraProject)
WHERE u.active = true
  AND grant.permission IN ['BROWSE_PROJECTS', 'ADMINISTER_PROJECTS']
RETURN DISTINCT u.display_name, u.email, p.key, grant.permission, grant.holder_type
```

The path covers direct user holders, group holders, direct role actors, and
members of groups acting in project roles. Results describe configured grants;
conditional holders and additional Jira access restrictions must be evaluated
separately. Team-managed project role membership is visible through `ROLE_OF`,
without an inferred permission-scheme grant.
