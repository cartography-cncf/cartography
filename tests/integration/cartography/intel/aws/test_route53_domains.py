from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.route53_domains
from cartography.intel.aws.route53_domains import sync
from tests.data.aws import route53_domains as test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 234567890


def _cleanup_domains(neo4j_session):
    neo4j_session.run("MATCH (n:Route53RegisteredDomain) DETACH DELETE n")
    neo4j_session.run("MATCH (n:AWSDNSZone) DETACH DELETE n")


@patch.object(
    cartography.intel.aws.route53_domains,
    "get_registered_domains",
    return_value=test_data.LIST_DOMAINS_RESPONSE,
)
def test_sync_route53_registered_domains(mock_get_domains, neo4j_session):
    _cleanup_domains(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Matching public zone for example.com; orphan.test has no zone.
    neo4j_session.run(
        """
        MERGE (z:AWSDNSZone{id: $zone_id})
        SET z.name = $name, z.zoneid = $zone_id, z.lastupdated = $update_tag
        """,
        zone_id="/hostedzone/ZEXAMPLECOM",
        name="example.com",
        update_tag=TEST_UPDATE_TAG,
    )

    sync(
        neo4j_session,
        boto3_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "Route53RegisteredDomain",
        ["id", "name", "auto_renew", "transfer_lock"],
    ) == {
        ("example.com", "example.com", True, True),
        ("orphan.test", "orphan.test", False, False),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "Route53RegisteredDomain",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "example.com"),
        (TEST_ACCOUNT_ID, "orphan.test"),
    }

    assert check_rels(
        neo4j_session,
        "AWSDNSZone",
        "name",
        "Route53RegisteredDomain",
        "id",
        "REGISTERED_DOMAIN",
        rel_direction_right=True,
    ) == {
        ("example.com", "example.com"),
    }


@patch.object(
    cartography.intel.aws.route53_domains,
    "get_registered_domains",
    return_value=test_data.LIST_DOMAINS_RESPONSE[:1],
)
def test_cleanup_stale_route53_registered_domains(mock_get_domains, neo4j_session):
    _cleanup_domains(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    with patch.object(
        cartography.intel.aws.route53_domains,
        "get_registered_domains",
        return_value=test_data.LIST_DOMAINS_RESPONSE,
    ):
        sync(
            neo4j_session,
            boto3_session,
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )

    sync(
        neo4j_session,
        boto3_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG_2,
        {"UPDATE_TAG": TEST_UPDATE_TAG_2, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "Route53RegisteredDomain",
        ["id"],
    ) == {
        ("example.com",),
    }
