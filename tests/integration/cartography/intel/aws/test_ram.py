import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ram
from cartography.intel.aws.ram import sync
from tests.data.aws.ram import GET_RAM_PRINCIPALS
from tests.data.aws.ram import GET_RAM_RESOURCE_SHARES
from tests.data.aws.ram import GET_RAM_RESOURCES
from tests.data.aws.ram import TEST_SHARE_ARN
from tests.data.aws.ram import TEST_TGW_ARN
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ram,
    "get_ram_resource_shares",
    return_value=GET_RAM_RESOURCE_SHARES,
)
@patch.object(
    cartography.intel.aws.ram, "get_ram_principals", return_value=GET_RAM_PRINCIPALS
)
@patch.object(
    cartography.intel.aws.ram, "get_ram_resources", return_value=GET_RAM_RESOURCES
)
def test_sync_ram(
    mock_get_resources, mock_get_principals, mock_get_shares, neo4j_session
):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    # A Transit Gateway shared through the resource share.
    neo4j_session.run(
        """
        MERGE (t:AWSTransitGateway{id: $arn})
        SET t.arn = $arn, t.lastupdated = $update_tag
        """,
        arn=TEST_TGW_ARN,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: the resource share node exists, carrying the external-principals flag.
    assert check_nodes(
        neo4j_session,
        "AWSRAMResourceShare",
        ["arn", "name", "allow_external_principals"],
    ) == {(TEST_SHARE_ARN, "shared-transit-gateway", True)}

    # Assert: the share belongs to the account that owns it.
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSRAMResourceShare",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(TEST_ACCOUNT_ID, TEST_SHARE_ARN)}

    # Assert: one principal association per principal, including the non-account one.
    assert check_nodes(
        neo4j_session, "AWSRAMPrincipalAssociation", ["principal", "external"]
    ) == {
        ("000000000001", False),
        ("999999999999", True),
        ("arn:aws:organizations::000000000000:ou/o-abcd1234/ou-abcd-12345678", False),
    }

    # Assert: every association points back at its resource share.
    assert check_rels(
        neo4j_session,
        "AWSRAMPrincipalAssociation",
        "principal",
        "AWSRAMResourceShare",
        "arn",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        ("000000000001", TEST_SHARE_ARN),
        ("999999999999", TEST_SHARE_ARN),
        (
            "arn:aws:organizations::000000000000:ou/o-abcd1234/ou-abcd-12345678",
            TEST_SHARE_ARN,
        ),
    }

    # Assert: account principals resolve to AWSAccount nodes, including the account
    # outside the organization, which is created by the composite node pattern.
    # The organizational-unit principal matches no account and yields no relationship.
    assert check_rels(
        neo4j_session,
        "AWSRAMPrincipalAssociation",
        "principal",
        "AWSAccount",
        "id",
        "SHARED_WITH",
        rel_direction_right=True,
    ) == {
        ("000000000001", "000000000001"),
        ("999999999999", "999999999999"),
    }

    # Assert: the shared resource is recorded and linked to the Transit Gateway.
    assert check_nodes(
        neo4j_session, "AWSRAMResourceAssociation", ["resource_arn", "resource_type"]
    ) == {(TEST_TGW_ARN, "ec2:TransitGateway")}

    assert check_rels(
        neo4j_session,
        "AWSRAMResourceAssociation",
        "resource_arn",
        "AWSTransitGateway",
        "arn",
        "SHARES",
        rel_direction_right=True,
    ) == {(TEST_TGW_ARN, TEST_TGW_ARN)}


@patch.object(cartography.intel.aws.ram, "get_ram_resources", return_value=[])
@patch.object(cartography.intel.aws.ram, "get_ram_principals", return_value=[])
@patch.object(
    cartography.intel.aws.ram,
    "get_ram_resource_shares",
    side_effect=[
        cartography.intel.aws.ram.RAMRegionUnreadable("AccessDeniedException"),
        [],
    ],
)
def test_sync_ram_unreadable_region_preserves_data(
    mock_get_shares, mock_get_principals, mock_get_resources, neo4j_session
):
    """
    A region that cannot be read must not converge previously synced RAM data to empty:
    cleanup is skipped so the last known good state survives, even though the other region
    synced successfully and returned nothing.
    """
    # Arrange: a share already in the graph from an earlier, successful run.
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MATCH (a:AWSAccount{id: $account_id})
        MERGE (s:AWSRAMResourceShare{id: $arn})
        SET s.arn = $arn, s.lastupdated = $old_tag
        MERGE (a)-[r:RESOURCE]->(s)
        SET r.lastupdated = $old_tag
        """,
        account_id=TEST_ACCOUNT_ID,
        arn=TEST_SHARE_ARN,
        old_tag=TEST_UPDATE_TAG,
    )

    # Act: the first region cannot be read, the second is readable and empty.
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION, "us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: the stale share is still there rather than cleaned up.
    assert check_nodes(neo4j_session, "AWSRAMResourceShare", ["arn"]) == {
        (TEST_SHARE_ARN,)
    }


@patch.object(cartography.intel.aws.ram, "get_ram_resources", return_value=[])
@patch.object(cartography.intel.aws.ram, "get_ram_principals", return_value=[])
@patch.object(
    cartography.intel.aws.ram,
    "get_ram_resource_shares",
    side_effect=cartography.intel.aws.ram.RAMRegionUnreadable("AccessDeniedException"),
)
def test_sync_ram_all_regions_unreadable_does_not_raise(
    mock_get_shares, mock_get_principals, mock_get_resources, neo4j_session, caplog
):
    """
    An account where RAM is denied in every region — typically a service control policy —
    must not abort the account's sync: the modules that run after this one still need to
    execute. It is logged as an error, and cleanup is skipped so nothing is deleted.
    """
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MATCH (a:AWSAccount{id: $account_id})
        MERGE (s:AWSRAMResourceShare{id: $arn})
        SET s.arn = $arn, s.lastupdated = $old_tag
        MERGE (a)-[r:RESOURCE]->(s)
        SET r.lastupdated = $old_tag
        """,
        account_id=TEST_ACCOUNT_ID,
        arn=TEST_SHARE_ARN,
        old_tag=TEST_UPDATE_TAG,
    )

    with caplog.at_level(logging.ERROR):
        sync(
            neo4j_session,
            MagicMock(),
            [TEST_REGION, "us-east-1"],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG + 1,
            {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
        )

    assert "Could not read RAM data in any of the 2 requested regions" in caplog.text
    # Cleanup was skipped, so the previously synced share is still present.
    assert check_nodes(neo4j_session, "AWSRAMResourceShare", ["arn"]) == {
        (TEST_SHARE_ARN,)
    }
