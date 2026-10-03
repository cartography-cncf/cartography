# Okta Configuration

## Authentication

Cartography supports two ways to authenticate to Okta.

### OAuth 2.0 client credentials (recommended)

[OAuth for Okta](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/) uses an API Services app with the `client_credentials` grant and `private_key_jwt` client authentication. Access is scoped, there is no long-lived shared token, and this is the only option in orgs whose authorization server rejects SSWS tokens.

1. In the Okta Admin Console, go to **Applications > Create App Integration > API Services** and create an app for Cartography.
1. In the app's **Client Credentials** section, set client authentication to **Public key / Private key**, generate a key, and save the private key (JWK JSON or PEM).
1. On the app's **Okta API Scopes** tab, grant the read-only scopes Cartography requests: `okta.users.read`, `okta.groups.read`, `okta.apps.read`, `okta.trustedOrigins.read`, `okta.authenticators.read`, and `okta.userTypes.read`.
1. On the app's **Admin roles** tab, assign **Read-only Administrator**. Service apps need an admin role in addition to scopes.
1. Store the private key in an environment variable.

### API token (legacy)

Generate an API token by following Okta's [Create an API Token guide](https://developer.okta.com/docs/guides/create-an-api-token/overview/). Store the token in an environment variable.

## Configure Cartography

Provide these options:

- `--okta-org-id`: Organization ID to query. This is the first part of the Okta organization URL.

Then, for OAuth 2.0 client credentials:

- `--okta-client-id`: Client ID of the API Services app.
- `--okta-private-key-env-var`: Name of the environment variable containing the app's private key.
- `--okta-dpop`: Pass this if the app has **Require Demonstrating Proof of Possession (DPoP) header in token requests** enabled.

Or, for a legacy API token:

- `--okta-api-key-env-var`: Name of the environment variable containing the API token.

If both are provided, OAuth 2.0 client credentials take precedence.

## Run Cartography

```bash
export OKTA_PRIVATE_KEY='<private-key>'
cartography \
  --selected-modules okta \
  --okta-org-id '<organization-id>' \
  --okta-client-id '<client-id>' \
  --okta-private-key-env-var OKTA_PRIVATE_KEY
```

Or, with a legacy API token:

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
