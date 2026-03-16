from unittest.mock import patch

import cartography.intel.ubuntu.cves
import cartography.intel.ubuntu.feed
import cartography.intel.ubuntu.notices
import tests.data.ubuntu.cves
import tests.data.ubuntu.notices
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_URL = "https://fake-ubuntu-api.example.com"


def _load_cves_first(neo4j_session):
    """Load feed and CVE nodes so that notice relationships can be created."""
    cartography.intel.ubuntu.feed.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    with patch.object(
        cartography.intel.ubuntu.cves,
        "_fetch_cves",
        return_value=iter([tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE]),
    ):
        cartography.intel.ubuntu.cves.sync(
            neo4j_session,
            TEST_API_URL,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG},
        )


@patch.object(
    cartography.intel.ubuntu.notices,
    "_fetch_notices",
    return_value=iter([tests.data.ubuntu.notices.UBUNTU_NOTICES_RESPONSE]),
)
def test_sync_ubuntu_notices(mock_api, neo4j_session):
    """
    Ensure that notice nodes are created with correct properties.
    """
    _load_cves_first(neo4j_session)

    cartography.intel.ubuntu.notices.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    expected_nodes = {
        ("USN-6600-1", "libfoo vulnerability"),
        ("USN-6700-1", "libbar vulnerability"),
    }
    assert (
        check_nodes(neo4j_session, "UbuntuSecurityNotice", ["id", "title"])
        == expected_nodes
    )


@patch.object(
    cartography.intel.ubuntu.notices,
    "_fetch_notices",
    return_value=iter([tests.data.ubuntu.notices.UBUNTU_NOTICES_RESPONSE]),
)
def test_sync_ubuntu_notices_cve_relationships(mock_api, neo4j_session):
    """
    Ensure that Notice-to-CVE ADDRESSES relationships are created correctly.
    """
    _load_cves_first(neo4j_session)

    cartography.intel.ubuntu.notices.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    expected_rels = {
        ("USN-6600-1", "USV|CVE-2024-1234"),
        ("USN-6600-1", "USV|CVE-2024-5678"),
        ("USN-6700-1", "USV|CVE-2024-5678"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UbuntuSecurityNotice",
            "id",
            "UbuntuCVE",
            "id",
            "ADDRESSES",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.ubuntu.notices,
    "_fetch_notices",
    return_value=iter([tests.data.ubuntu.notices.UBUNTU_NOTICES_RESPONSE]),
)
def test_sync_ubuntu_notices_feed_relationship(mock_api, neo4j_session):
    """
    Ensure that Notice-to-Feed RESOURCE relationships are created correctly.
    """
    _load_cves_first(neo4j_session)

    cartography.intel.ubuntu.notices.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    expected_rels = {
        ("ubuntu-security-cve-feed", "USN-6600-1"),
        ("ubuntu-security-cve-feed", "USN-6700-1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UbuntuCVEFeed",
            "id",
            "UbuntuSecurityNotice",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )
