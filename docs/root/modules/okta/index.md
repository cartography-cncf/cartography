# Okta

The Okta module ingests organizations, users, groups, applications, trusted
origins, user, group, and application administration roles, user authentication
factors, devices, network zones, API token metadata, System Log streams, and
policies (global session, password, authentication, authenticator enrollment,
and profile enrollment) with their rules.
See the generated [Okta schema](schema.md) for the available properties and
relationships.

## OAuth Service App Privileges

An Okta OAuth service app can act only within both its admin role
(`OktaApplicationRole`) and its granted Okta API scopes
(`OktaApplication.granted_scopes`). For example, a service app with the Super
Administrator role but only `.read` scopes is read-only. Reading granted
scopes needs the `okta.appGrants.read` scope; see
[Permissions](config.md#permissions).

Service apps with an admin role, and whether they can make changes:

```cypher
MATCH (a:OktaApplication)-[:HAS_ROLE]->(r:OktaApplicationRole)
RETURN a.label, r.role_type, a.granted_scopes,
       any(s IN coalesce(a.granted_scopes, []) WHERE s ENDS WITH '.manage') AS can_write
```

OAuth apps that authenticate with a shared client secret instead of a private
key, and whether they require DPoP:

```cypher
MATCH (a:OktaApplication)
WHERE a.credentials_oauth_client_token_endpoint_auth_method STARTS WITH 'client_secret'
RETURN a.label, a.settings_oauth_client_application_type,
       a.settings_oauth_client_dpop_bound_access_tokens
```

`OktaOrganization.application_roles_synced` and `app_grants_synced` record
whether the last sync could read this data, so a missing role or scope can be
told apart from one the credential could not read.

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
