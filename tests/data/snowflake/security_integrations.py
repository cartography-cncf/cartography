"""Raw Snowflake security integration rows.

``SNOWFLAKE_SECURITY_INTEGRATIONS`` is shaped as `SHOW SECURITY INTEGRATIONS` returns it
and ``SNOWFLAKE_SECURITY_INTEGRATION_DETAILS`` as `DESC INTEGRATION` returns it once
folded into one dict per integration by ``SnowflakeClient.describe``.
"""

from typing import Any

# A throwaway base64 blob standing in for an identity provider's signing certificate.
# Only its SHA-256 fingerprint is ever stored on the node.
# Base64 of some stand-in DER bytes. It has to actually decode, because the
# fingerprint is taken over the certificate bytes rather than over this text, so
# that it matches the standard X.509 SHA-256 fingerprint an operator would
# compare against.
SNOWFLAKE_SAML_CERTIFICATE_DER = b"springfield-nuclear-saml-signing-certificate-der"
SNOWFLAKE_SAML_CERTIFICATE = (
    "c3ByaW5nZmllbGQtbnVjbGVhci1zYW1sLXNpZ25pbmctY2VydGlmaWNhdGUtZGVy"
)

SNOWFLAKE_SECURITY_INTEGRATIONS: list[dict[str, Any]] = [
    {
        "name": "SPRINGFIELD_OKTA_SAML",
        "type": "SAML2",
        "category": "SECURITY",
        "enabled": "true",
        "comment": "Workforce sign-in for the plant",
        "created_on": "1784400000.000000000 0",
    },
    {
        "name": "DUFF_OAUTH_INTEGRATION",
        "type": "EXTERNAL_OAUTH - CUSTOM",
        "category": "SECURITY",
        "enabled": "true",
        "comment": "",
        "created_on": "1784500000.000000000 0",
    },
    {
        "name": "SPRINGFIELD_SCIM",
        "type": "SCIM - OKTA",
        "category": "SECURITY",
        "enabled": "true",
        "comment": "",
        "created_on": "1784600000.000000000 0",
    },
]

SNOWFLAKE_SECURITY_INTEGRATION_DETAILS: dict[str, Any] = {
    "SPRINGFIELD_OKTA_SAML": {
        "saml2_issuer": "http://www.okta.com/exkspringfield",
        "saml2_sso_url": "https://springfield.okta.com/app/snowflake/sso/saml",
        "saml2_provider": "OKTA",
        "saml2_x509_cert": SNOWFLAKE_SAML_CERTIFICATE,
        "network_policy": "PLANT_NETWORK_POLICY",
    },
    "DUFF_OAUTH_INTEGRATION": {
        "external_oauth_issuer": "https://auth.duff.example.com/",
        "external_oauth_jws_keys_url": "https://auth.duff.example.com/.well-known/jwks",
        "external_oauth_audience_list": "https://springfield-nuclear.snowflakecomputing.com",
        # ENABLE lets any token holder request any role their user has, which widens
        # every token issued by this provider.
        "external_oauth_any_role_mode": "ENABLE",
        "oauth_client_type": "PUBLIC",
        "oauth_redirect_uri": "https://duff.example.com/callback",
        "oauth_issue_refresh_tokens": "true",
        "oauth_refresh_token_validity": "7776000",
        # Snowflake returns the client secret masked; it is never stored either way.
        "oauth_client_secret": "****",
    },
    "SPRINGFIELD_SCIM": {
        "scim_client": "OKTA",
        # The external provisioner acts as this role, so whatever it can create in
        # Snowflake is bounded by that role.
        "run_as_role": "USERADMIN",
        "network_policy": "",
    },
}
