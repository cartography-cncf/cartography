# Okta Configuration

## Authentication

Generate an API token by following Okta's [Create an API Token guide](https://developer.okta.com/docs/guides/create-an-api-token/overview/). Store the token in an environment variable.

## Configure Cartography

Provide these options:

- `--okta-api-key-env-var`: Name of the environment variable containing the API token.
- `--okta-org-id`: Organization ID to query. This is the first part of the Okta organization URL.

## Run Cartography

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
