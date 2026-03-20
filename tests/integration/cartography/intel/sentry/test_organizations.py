from unittest.mock import patch

import requests

import cartography.intel.sentry.organizations
import tests.data.sentry.organizations
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://sentry.io/api/0"


@patch.object(
    cartography.intel.sentry.organizations,
    "get",
    return_value=tests.data.sentry.organizations.SENTRY_ORGANIZATIONS,
)
def test_sync_sentry_organizations(mock_api, neo4j_session):
    api_session = requests.Session()

    cartography.intel.sentry.organizations.sync(
        neo4j_session,
        api_session,
        TEST_UPDATE_TAG,
        TEST_BASE_URL,
    )

    assert check_nodes(neo4j_session, "SentryOrganization", ["id", "slug"]) == {
        ("100", "simpson-corp"),
    }

    # Verify semantic label
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {
        ("100",),
    }
