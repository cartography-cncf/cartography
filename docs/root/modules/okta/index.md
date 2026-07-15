# Okta

The Okta module ingests organizations, users, groups, applications, trusted
origins, administration roles, and user authentication factors.

Okta nodes use legacy Cypher-based ingestion rather than formal
`CartographyNodeSchema` models. Schema introspection APIs may therefore return
empty results for Okta nodes. The [Okta schema](schema.md) documents the
available properties and relationships.

(cross-platform-integration-okta-to-aws)=
## Cross-Platform Integration: Okta to AWS

When Okta is configured as the SAML identity provider for AWS Identity Center,
Cartography can represent this access path:

```cypher
(:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML]->(:AWSRole)
```

Cartography links an `OktaUser` to an `AWSSSOUser` when
`AWSSSOUser.external_id` matches `OktaUser.id`. CloudTrail management events
record role assumptions from AWS Identity Center as `ASSUMED_ROLE_WITH_SAML`
relationships.

```{toctree}
config
schema
```
