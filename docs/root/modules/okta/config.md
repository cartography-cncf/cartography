## Okta Configuration

Follow these steps to analyze Okta objects with Cartography. Two
authentication methods are supported: OAuth 2.0 client credentials
(recommended) and a legacy SSWS API token.

### Option A (recommended): OAuth 2.0 client credentials

Uses [OAuth for Okta](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/)
with an API Services app: scoped, no long-lived shared token, and works in
orgs that require `private_key_jwt` client authentication.

1. In the Okta Admin console, go to **Applications > Create App Integration >
   API Services** and create an app for Cartography.
1. In the app's **Client Credentials** section, set client authentication to
   **Public key / Private key**, generate a key, and save the private key
   (JWK JSON or PEM).
1. On the app's **Okta API Scopes** tab, grant the read-only scopes Cartography
   requests: `okta.users.read`, `okta.groups.read`, `okta.apps.read`,
   `okta.trustedOrigins.read`, `okta.authenticators.read`, and
   `okta.userTypes.read`.
1. On the app's **Admin roles** tab, assign **Read-only Administrator**
   (service apps need a role in addition to scopes).
1. Populate an environment variable with the private key and pass its name via
   `--okta-private-key-env-var`. Pass the app's client ID via
   `--okta-client-id` and your organization ID via `--okta-org-id`.
1. If the app has **Require Demonstrating Proof of Possession (DPoP) header in
   token requests** enabled, also pass `--okta-dpop`.

### Option B (legacy): SSWS API token

1. Prepare your Okta API token.
    1. Generate your API token by following the steps from the Okta [Create An API Token documentation](https://developer.okta.com/docs/guides/create-an-api-token/overview/)
    1. Populate an environment variable with the API token. You can pass the environment variable name via CLI with the `--okta-api-key-env-var` parameter.
    1. Use the CLI `--okta-org-id` parameter with the organization ID that you wish to query. The organization ID is the first part of the Okta URL for your organization.
    1. If you are using an Okta preview environment or another Okta region, use `--okta-base-domain` to set the base domain (e.g., `--okta-base-domain oktapreview.com`). The default is `okta.com`.
	1. If you are using Okta to [administer AWS as a SAML provider](https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC) then the module will automatically match OktaGroups to the AWSRole they control access for.
		- If you are using a regex other than the standard okta group to role regex `^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$` defined in [Step 5: Enabling Group Based Role Mapping in Okta](https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC)  then you can specify your regex with the `--okta-saml-role-regex` parameter.
