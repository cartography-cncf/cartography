## Okta Configuration

.. _okta_config:

Follow these steps to analyze Okta objects with Cartography.

1. Prepare your Okta API token.
    1. Generate your API token by following the steps from the Okta [Create An API Token documentation](https://developer.okta.com/docs/guides/create-an-api-token/overview/)
    1. Populate an environment variable with the API token. You can pass the environment variable name via CLI with the `--okta-api-key-env-var` parameter.
    1. Use the CLI `--okta-org-id` parameter with the organization ID that you wish to query. The organization ID is the first part of the Okta URL for your organization.
	1. If you are using Okta to [administer AWS as a SAML provider](https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC) then the module will automatically match OktaGroups to the AWSRole they control access for.
		- If you are using a regex other than the standard okta group to role regex `^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$` defined in [Step 5: Enabling Group Based Role Mapping in Okta](https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC)  then you can specify your regex with the `--okta-saml-role-regex` parameter.
