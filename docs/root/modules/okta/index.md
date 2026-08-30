# Okta

The Okta module ingests organizations, users, groups, applications, trusted
origins, user and group administration roles, and user authentication factors.
See the generated [Okta schema](schema.md) for the available properties and
relationships.

(cross-platform-integration-okta-to-aws)=
## Cross-Platform Integration: Okta to AWS

When Okta is configured as the SAML identity provider for AWS Identity Center,
run both the Okta and AWS modules. The AWS Identity Center sync links the
SCIM-provisioned identity to its permitted AWS roles:

```cypher
(:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)<-[:ALLOWED_BY]-(:AWSRole)
```

Cartography links an `OktaUser` to an `AWSSSOUser` when
`AWSSSOUser.external_id` matches `OktaUser.id`. The AWS Identity Center sync
creates this link and imports permitted role assignments. CloudTrail management
events record actual role use separately:

```cypher
(:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML]->(:AWSRole)
```

For direct Okta group-to-IAM-role mapping, Cartography uses this path:

```cypher
(:OktaUser)-[:MEMBER_OF]->(:OktaGroup)-[:ALLOWED_BY]->(:AWSRole)
```

See [AWS identity and access](../aws/identity-access.md) for permission-set,
group-assignment, and observed-use queries.

## Graph model migration

This module uses the shared Cartography ontology:

- `OktaUserRole` and `OktaGroupRole` replace `OktaAdministrationRole` and use
  `HAS_ROLE` relationships.
- `User` and `HAS_ACCOUNT` replace the deprecated `Human` and `IDENTITY_OKTA`
  identity model.
- `MEMBER_OF` replaces `MEMBER_OF_OKTA_GROUP`. Cartography continues to write
  `MEMBER_OF_OKTA_GROUP` as a compatibility relationship until v1.0.0.

The Okta cleanup removes the replaced nodes and relationships. Update queries
that still use `OktaAdministrationRole`, `Human`, or `IDENTITY_OKTA` before
running this version.

```{toctree}
config
schema
```
