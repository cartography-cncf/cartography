# Okta overview

The Okta module ingests organizations, users, groups, applications, trusted
origins, user and group administration roles, and user authentication factors.
See the generated [Okta schema](schema.md) for the available properties and
relationships.

(cross-platform-integration-okta-to-aws)=
## Cross-platform integration: Okta to AWS

When Okta is configured as the SAML identity provider for AWS Identity Center,
run both the Okta and AWS modules to represent SCIM-provisioned identities and
their permitted AWS roles:

```cypher
(:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)<-[:ALLOWED_BY]-(:AWSRole)
```

The AWS Identity Center sync links an `OktaUser` to an `AWSSSOUser` when
`AWSSSOUser.external_id` matches `OktaUser.id`, and imports permitted role
assignments. CloudTrail management events record actual role use separately:

```cypher
(:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML]->(:AWSRole)
```

For Okta group-to-role mappings derived from group names, including
`AWSReservedSSO` roles, Cartography uses this path:

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
  identity model. Run the ontology module to materialize `User` nodes and
  `HAS_ACCOUNT` relationships.
- `MEMBER_OF` replaces `MEMBER_OF_OKTA_GROUP`. Cartography continues to write
  `MEMBER_OF_OKTA_GROUP` as a compatibility relationship until v1.0.0.

The Okta migration cleanup removes `OktaAdministrationRole` nodes and the
replaced `IDENTITY_OKTA`, Okta-derived `CAN_ASSUME_ROLE`,
`MEMBER_OF_OKTA_ROLE`, and `MAPS_TO` relationships. It leaves shared `Human`
nodes and the compatibility `MEMBER_OF_OKTA_GROUP` relationship intact. Update
queries that still use the replaced graph model before running this version.
