import hashlib
from unittest.mock import patch

import cartography.intel.snowflake.security_integrations
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.security_integrations import SNOWFLAKE_SAML_CERTIFICATE_DER
from tests.data.snowflake.security_integrations import (
    SNOWFLAKE_SECURITY_INTEGRATION_DETAILS,
)
from tests.data.snowflake.security_integrations import SNOWFLAKE_SECURITY_INTEGRATIONS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

OKTA_SAML_ID = "SPRINGFIELD.NUCLEAR/security_integration/SPRINGFIELD_OKTA_SAML"
DUFF_OAUTH_ID = "SPRINGFIELD.NUCLEAR/security_integration/DUFF_OAUTH_INTEGRATION"
SPRINGFIELD_SCIM_ID = "SPRINGFIELD.NUCLEAR/security_integration/SPRINGFIELD_SCIM"

USERADMIN_ROLE_ID = "SPRINGFIELD.NUCLEAR/role/USERADMIN"
PLANT_NETWORK_POLICY_ID = "SPRINGFIELD.NUCLEAR/network_policy/PLANT_NETWORK_POLICY"


def _details_for(client, name):
    return SNOWFLAKE_SECURITY_INTEGRATION_DETAILS[name]


def _ensure_local_neo4j_has_test_security_integrations(neo4j_session) -> None:
    """Seed the security integrations secrets and external access point back at."""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    cartography.intel.snowflake.security_integrations.load_security_integrations(
        neo4j_session,
        cartography.intel.snowflake.security_integrations.transform(
            SNOWFLAKE_SECURITY_INTEGRATIONS,
            SNOWFLAKE_SECURITY_INTEGRATION_DETAILS,
            SNOWFLAKE_ACCOUNT_ID,
        ),
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.security_integrations,
    "get_details",
    side_effect=_details_for,
)
@patch.object(
    cartography.intel.snowflake.security_integrations,
    "get",
    return_value=SNOWFLAKE_SECURITY_INTEGRATIONS,
)
def test_sync_snowflake_security_integrations(mock_get, mock_details, neo4j_session):
    # Arrange: the role the SCIM client acts as and the network policy restricting SAML
    # sign-in are owned by other syncs, so seed both.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MERGE (r:SnowflakeRole{id: $role_id}) SET r.lastupdated = $tag "
        "MERGE (p:SnowflakeNetworkPolicy{id: $policy_id}) SET p.lastupdated = $tag",
        role_id=USERADMIN_ROLE_ID,
        policy_id=PLANT_NETWORK_POLICY_ID,
        tag=TEST_UPDATE_TAG,
    )

    # Act
    complete = cartography.intel.snowflake.security_integrations.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the protocol is derived from the type whatever provider suffix it
    # carries, and ANY_ROLE_MODE is surfaced because it decides whether a token holder
    # can pick any role their user has.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeSecurityIntegration",
        [
            "id",
            "name",
            "protocol",
            "enabled",
            "external_oauth_any_role_mode",
            "oauth_client_type",
        ],
    ) == {
        (OKTA_SAML_ID, "SPRINGFIELD_OKTA_SAML", "SAML", True, None, None),
        (DUFF_OAUTH_ID, "DUFF_OAUTH_INTEGRATION", "OIDC", True, "ENABLE", "PUBLIC"),
        (SPRINGFIELD_SCIM_ID, "SPRINGFIELD_SCIM", "SCIM", True, None, None),
    }
    # Only the fingerprint of the signing certificate is stored, never the body.
    # Hashed over the decoded certificate bytes, not over the base64 text, so the
    # value matches `openssl x509 -noout -fingerprint -sha256`.
    expected_fingerprint = hashlib.sha256(SNOWFLAKE_SAML_CERTIFICATE_DER).hexdigest()
    assert check_nodes(
        neo4j_session,
        "SnowflakeSecurityIntegration",
        ["id", "saml2_x509_cert_fingerprint"],
    ) == {
        (OKTA_SAML_ID, expected_fingerprint),
        (DUFF_OAUTH_ID, None),
        (SPRINGFIELD_SCIM_ID, None),
    }
    # No property anywhere on the node holds the OAuth client secret DESC returned.
    assert not [
        key
        for record in neo4j_session.run(
            "MATCH (i:SnowflakeSecurityIntegration) RETURN properties(i) AS props",
        )
        for key in record["props"]
        if "client_secret" in key
    ]
    assert check_nodes(neo4j_session, "IdentityProvider", ["id"]) >= {
        (OKTA_SAML_ID,),
        (DUFF_OAUTH_ID,),
        (SPRINGFIELD_SCIM_ID,),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSecurityIntegration",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (OKTA_SAML_ID, SNOWFLAKE_ACCOUNT_ID),
        (DUFF_OAUTH_ID, SNOWFLAKE_ACCOUNT_ID),
        (SPRINGFIELD_SCIM_ID, SNOWFLAKE_ACCOUNT_ID),
    }
    # The SCIM provisioner's privileges are bounded by the role it runs as.
    assert check_rels(
        neo4j_session,
        "SnowflakeSecurityIntegration",
        "id",
        "SnowflakeRole",
        "id",
        "RUNS_AS_ROLE",
        rel_direction_right=True,
    ) == {(SPRINGFIELD_SCIM_ID, USERADMIN_ROLE_ID)}
    assert check_rels(
        neo4j_session,
        "SnowflakeSecurityIntegration",
        "id",
        "SnowflakeNetworkPolicy",
        "id",
        "GOVERNED_BY",
        rel_direction_right=True,
    ) == {(OKTA_SAML_ID, PLANT_NETWORK_POLICY_ID)}
