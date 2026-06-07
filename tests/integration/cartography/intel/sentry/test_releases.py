from unittest.mock import patch

import requests

import cartography.intel.sentry.organizations
import cartography.intel.sentry.releases
import tests.data.sentry.organizations
import tests.data.sentry.releases
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "100"
TEST_ORG_SLUG = "simpson-corp"
TEST_BASE_URL = "https://sentry.io/api/0"


@patch.object(
    cartography.intel.sentry.organizations,
    "get",
    return_value=tests.data.sentry.organizations.SENTRY_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.sentry.releases,
    "get",
    return_value=tests.data.sentry.releases.SENTRY_RELEASES,
)
def test_sync_sentry_releases(mock_releases, mock_orgs, neo4j_session):
    # Arrange: create org
    cartography.intel.sentry.organizations.sync(
        neo4j_session,
        requests.Session(),
        TEST_UPDATE_TAG,
        TEST_BASE_URL,
    )
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}

    # Act
    cartography.intel.sentry.releases.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_BASE_URL,
    )

    # Assert releases exist (id is org_id/version to avoid cross-org collisions)
    assert check_nodes(neo4j_session, "SentryRelease", ["id", "version"]) == {
        (f"{TEST_ORG_ID}/backend-api@1.0.0", "backend-api@1.0.0"),
        (f"{TEST_ORG_ID}/frontend-app@2.0.0", "frontend-app@2.0.0"),
    }

    # Assert RESOURCE relationship to org
    assert check_rels(
        neo4j_session,
        "SentryRelease",
        "id",
        "SentryOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_ORG_ID}/backend-api@1.0.0", TEST_ORG_ID),
        (f"{TEST_ORG_ID}/frontend-app@2.0.0", TEST_ORG_ID),
    }
