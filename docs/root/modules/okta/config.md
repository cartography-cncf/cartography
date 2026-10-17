# Okta Configuration

## Authentication

Cartography authenticates to Okta with either an OAuth service app or an API
token. Okta recommends the service app: its access tokens are short-lived and
limited to the granted scopes, and it is not tied to an admin user.

### OAuth service app

In the Okta Admin Console:

1. Go to **Applications** > **Applications** > **Create App Integration**. Open
   the **Classic experience** tab, choose **API Services**, and click **Next**.
   The recommended Okta Integration Wizard tab does not offer this flow.
1. Name the app, for example `Cartography`, choose **Use Okta-generated client
   ID**, and click **Save**. Copy the **Client ID**.
1. Switch the app to key authentication. Okta creates the app with a client
   secret, but
   [accepts only a private key](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/)
   when the app requests Okta API scopes. Add the key first, or Okta refuses
   the switch:
   1. Under **Public keys**, click **Edit** and then **Add key**. Paste your
      public key as a JWK, or click **Generate new key** and save the private
      key that Okta shows only once. Click **Done**, then **Save**, and note the
      key's **KID**.
   1. Under **Client Credentials**, click **Edit**, choose **Public key /
      Private key**, click **Save**, and confirm. Okta deletes the unused client
      secret.
1. On the **Okta API Scopes** tab, click **Grant** for each of these scopes:
   `okta.apiTokens.read`, `okta.apps.read`, `okta.authenticators.read`,
   `okta.devices.read`, `okta.groups.read`, `okta.logStreams.read`,
   `okta.networkZones.read`, `okta.policies.read`, `okta.roles.read`,
   `okta.trustedOrigins.read`, `okta.userTypes.read`, `okta.users.read`.
   To script this step, use the `okta_app_oauth_api_scope` resource of the
   Okta Terraform provider or the
   [application grants API](https://developer.okta.com/docs/api/openapi/okta-management/management/tag/ApplicationGrants/).
1. On the **Admin roles** tab, click **Edit assignments**, choose
   **Super Administrator**, and save. The app stays read-only; see
   [Admin role and scopes](#admin-role-and-scopes). Okta asks you to
   reauthenticate before it saves an admin role.

#### Admin role and scopes

Okta checks two things on every request from a service app: one of the access
token's scopes must allow the action, and the app's admin role must allow access
to the resource. The scopes limit what the app can do; the admin role limits
what it can see.

Cartography requests only read scopes, so the app cannot create, change, or
delete anything in Okta, whatever admin role it has. That also makes a service
app safer than an API token, which can do anything its creator can.

- **Super Administrator** (recommended): Cartography syncs every resource. The
  read scopes keep the app read-only.
- **Read-only Administrator**: Okta refuses this role log streams, admin role
  assignments, the Admin Console session settings, and Okta's own apps.
  Cartography skips those with a warning; see [Permissions](#permissions).

Leave **Require Demonstrating Proof of Possession (DPoP)** as it is.
Cartography sends DPoP proofs by default, which works whether or not the app
requires them. `--okta-disable-dpop` stops sending them; an app that requires
DPoP then rejects the token request with `invalid_dpop_proof`.

Okta refuses to issue an access token (`invalid_scope`) when Cartography
requests a scope that the app was not granted. To run with fewer scopes, list
the granted ones with `--okta-scopes`. The Okta sync fails without
`okta.users.read`, `okta.groups.read`, `okta.apps.read`,
`okta.authenticators.read`, `okta.trustedOrigins.read`, and
`okta.userTypes.read`. It skips the resources under
[Permissions](#permissions) whose scope is missing.

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

The OAuth scopes above apply to OAuth service apps. A service app also needs an
admin role that allows each request, and an API token gets whatever its
creator's admin role allows. With the Read-only Administrator role, Okta
refuses:

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
