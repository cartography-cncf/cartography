from unittest.mock import Mock

import cartography.intel.databricks.federation_policies
from tests.data.databricks.account import account_scoped
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.federation_policies import (
    DATABRICKS_ACCOUNT_FEDERATION_POLICIES,
)
from tests.data.databricks.federation_policies import DATABRICKS_SP_FEDERATION_POLICIES
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.databricks.test_account_service_principals import (
    _ensure_local_neo4j_has_test_account_service_principals,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _uc_list(uri, key, params=None):
    if uri.endswith("/federationPolicies") and "/servicePrincipals/" not in uri:
        return DATABRICKS_ACCOUNT_FEDERATION_POLICIES
    for scim_id, payload in DATABRICKS_SP_FEDERATION_POLICIES.items():
        if f"/servicePrincipals/{scim_id}/federationPolicies" in uri:
            return payload["policies"]
    return []


def test_load_databricks_federation_policies(neo4j_session):
    # Arrange
    api_session = Mock()
    api_session.account_uri.side_effect = lambda suffix: (
        f"/api/2.0/accounts/{DATABRICKS_ACCOUNT_ID}{suffix}"
    )
    api_session.uc_list.side_effect = _uc_list
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_account_service_principals(neo4j_session)

    # Act
    cartography.intel.databricks.federation_policies.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    # Assert policy nodes (account-wide + SP-scoped)
    assert check_nodes(
        neo4j_session,
        "DatabricksFederationPolicy",
        ["id", "name", "service_principal_id"],
    ) == {
        (account_scoped("uid-account-1"), "github-actions", None),
        (account_scoped("uid-sp-1"), "etl-oidc", "510001"),
    }

    # Assert Account -> Policy RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksFederationPolicy",
        "id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (account_scoped("uid-account-1"), DATABRICKS_ACCOUNT_ID),
        (account_scoped("uid-sp-1"), DATABRICKS_ACCOUNT_ID),
    }

    # Assert SP-scoped Policy -> ServicePrincipal OWNED_BY
    assert check_rels(
        neo4j_session,
        "DatabricksFederationPolicy",
        "id",
        "DatabricksAccountServicePrincipal",
        "id",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {
        (account_scoped("uid-sp-1"), account_scoped("510001")),
    }
