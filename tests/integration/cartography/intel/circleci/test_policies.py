from unittest.mock import patch

import requests

import cartography.intel.circleci.policies
import tests.data.circleci.policies
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_ORG_ID = "org-1111-aaaa"


@patch.object(
    cartography.intel.circleci.policies,
    "get_decision_settings",
    return_value=tests.data.circleci.policies.CIRCLECI_DECISION_SETTINGS,
)
@patch.object(
    cartography.intel.circleci.policies,
    "get_policy_bundle",
    return_value=tests.data.circleci.policies.CIRCLECI_POLICY_BUNDLE,
)
def test_load_circleci_policies(mock_bundle, mock_settings, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)

    # Act
    cartography.intel.circleci.policies.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG_ID,
    )

    # Assert policies exist with the decision-enabled flag folded in
    assert check_nodes(
        neo4j_session, "CircleCIPolicy", ["id", "name", "decision_enabled"]
    ) == {
        (
            f"{TEST_ORG_ID}:config:require_security_scan",
            "require_security_scan",
            True,
        ),
        (
            f"{TEST_ORG_ID}:config:block_unapproved_orbs",
            "block_unapproved_orbs",
            True,
        ),
    }
    assert check_rels(
        neo4j_session,
        "CircleCIPolicy",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_ORG_ID}:config:require_security_scan", TEST_ORG_ID),
        (f"{TEST_ORG_ID}:config:block_unapproved_orbs", TEST_ORG_ID),
    }
