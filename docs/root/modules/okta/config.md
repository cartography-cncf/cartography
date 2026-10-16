# Okta Configuration

## Authentication

Cartography authenticates to Okta with either an OAuth service app or an API
token. Okta recommends the service app: its access tokens are short-lived and
limited to the granted scopes, and it is not tied to an admin user.

### OAuth service app

1. Create an API Services app by following Okta's
   [Implement OAuth for Okta with a service app](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/)
   guide. Set client authentication to **Public key / Private key** and add a
   key. Okta does not accept a client secret for its management API.
1. Save the private key, as a PEM or a JWK, and note its key ID (`kid`).
1. On the **Okta API Scopes** tab, grant these scopes:
   `okta.apiTokens.read`, `okta.apps.read`, `okta.authenticators.read`,
   `okta.devices.read`, `okta.groups.read`, `okta.logStreams.read`,
   `okta.networkZones.read`, `okta.policies.read`, `okta.roles.read`,
   `okta.trustedOrigins.read`, `okta.userTypes.read`, `okta.users.read`.
1. On the **Admin roles** tab, assign the **Read-only Administrator** role.
   Okta requires both the scope and an admin role that allows the request.

Okta refuses to issue an access token (`invalid_scope`) when Cartography
requests a scope that the app was not granted. To run with fewer scopes, list
the granted ones with `--okta-scopes`. The Okta sync fails without
`okta.users.read`, `okta.groups.read`, `okta.apps.read`,
`okta.authenticators.read`, `okta.trustedOrigins.read`, and
`okta.userTypes.read`. It skips the resources under
[Permissions](#permissions) whose scope is missing.

Okta requires DPoP-bound tokens on new service apps by default, and Cartography
sends DPoP proofs automatically. If the app does not require DPoP, pass
`--okta-disable-dpop` to stop sending them.

### API token

Generate an API token by following Okta's [Create an API Token guide](https://developer.okta.com/docs/guides/create-an-api-token/overview/). Store the token in an environment variable.

### Permissions

Cartography only reads from Okta. An API token acts with the admin roles of the
user who created it, so create it as a read-only administrator.

Some resources need permissions that older tokens or OAuth clients may not have.
When Okta refuses one of these requests, Cartography logs a warning, skips that
resource, and continues the rest of the Okta sync:

| Resource | OAuth scope |
| --- | --- |
| Admin role assignments (`OktaUserRole`, `OktaGroupRole`) | `okta.roles.read` |
| Devices (`OktaDevice`) | `okta.devices.read` |
| API token metadata (`OktaApiToken`) | `okta.apiTokens.read` |
| Log streams (`OktaLogStream`) | `okta.logStreams.read` |
| Network zones (`OktaNetworkZone`) | `okta.networkZones.read` |
| Policies and policy rules (`OktaPolicy`, `OktaPolicyRule`) | `okta.policies.read` |
| Okta Admin Console session settings on `OktaOrganization` | `okta.apps.read` |

Authentication and profile enrollment policies, and the Admin Console session
settings, exist only in Okta Identity Engine orgs. Classic Engine orgs sync the
other policy types.

The OAuth scopes above apply to OAuth service apps. An API token instead gets
whatever its creator's admin role allows. A token created by a read-only
administrator may be refused for:

- Log streams and the Admin Console session settings.
- Admin role assignments.
- Okta's own apps, such as the Admin Console and Dashboard. Policies assigned to
  them are still synced, but without `first_party_app_names`.

Okta DISA STIG checks that need refused data are not evaluated for that org,
instead of reporting a pass: System Log streaming, the Admin Console session
timeout, and API tokens owned by super administrators.

If the API token is restricted to network zones, run Cartography from an IP
address in one of those zones. From anywhere else, Okta rejects the token as
invalid (`E0000011`).

## Configure Cartography

Provide these options:

- `--okta-org-id`: Organization ID to query. This is the first part of the Okta organization URL.

For an OAuth service app:

- `--okta-client-id`: Client ID of the service app.
- `--okta-private-key-env-var`: Name of the environment variable containing the private key.
- `--okta-private-key-id`: Key ID (`kid`) of the key. Not needed when the private key is a JWK that includes its `kid`.

For an API token:

- `--okta-api-key-env-var`: Name of the environment variable containing the API token.

When both are set, Cartography uses the OAuth service app.

## Run Cartography

With an OAuth service app:

```bash
export OKTA_PRIVATE_KEY="$(cat okta-service-app.pem)"
cartography \
  --selected-modules okta \
  --okta-org-id '<organization-id>' \
  --okta-client-id '<client-id>' \
  --okta-private-key-env-var OKTA_PRIVATE_KEY \
  --okta-private-key-id '<key-id>'
```

With an API token:

```bash
export OKTA_API_TOKEN='<api-token>'
cartography \
  --selected-modules okta \
  --okta-org-id '<organization-id>' \
  --okta-api-key-env-var OKTA_API_TOKEN
```

## Advanced Configuration

For an Okta preview environment or another region, set `--okta-base-domain`. The default is `okta.com`.

When Okta administers AWS as a [SAML provider](https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC), Cartography matches Okta groups to the AWS roles they control. If your group names do not use the standard `^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$` pattern from [Enabling Group Based Role Mapping in Okta](https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC), provide your pattern with `--okta-saml-role-regex`.
