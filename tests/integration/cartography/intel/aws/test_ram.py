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
