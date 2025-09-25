from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.route53
from cartography.intel.aws.route53 import sync
from tests.data.aws.ec2.load_balancers import LOAD_BALANCER_DATA
from tests.data.aws.route53 import GET_ZONES_SAMPLE_RESPONSE
from tests.data.aws.route53 import GET_ZONES_WITH_SUBZONE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_ec2_records(neo4j_session):
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        LOAD_BALANCER_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.route53,
    "get_zones",
    return_value=GET_ZONES_SAMPLE_RESPONSE,
)
def test_sync_route53(mock_get_zones, neo4j_session):
    """
    Test that Route53 sync correctly creates DNS zones, records, and relationships
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_test_ec2_records(neo4j_session)

    # Create IP nodes that DNS records will point to
    neo4j_session.run(
        """
        UNWIND $ip_addresses as ip
        MERGE (ip_node:Ip{id: ip})
        ON CREATE SET ip_node.firstseen = timestamp(), ip_node.ip = ip
        SET ip_node.lastupdated = $update_tag
        """,
        ip_addresses=["1.2.3.4", "5.6.7.8", "9.10.11.12", "2001:db8::1", "2001:db8::2"],
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

    # Assert
    assert check_nodes(
        neo4j_session, "AWSDNSZone", ["zoneid", "name", "privatezone"]
    ) == {
        ("/hostedzone/HOSTED_ZONE", "example.com", False),
    }, "DNS Zones don't exist"

    assert check_nodes(neo4j_session, "AWSDNSZone", ["zoneid", "name"]) == {
        ("/hostedzone/HOSTED_ZONE", "example.com"),
    }, "DNS Zones don't exist"

    assert check_nodes(neo4j_session, "AWSDNSRecord", ["id", "name", "type"]) == {
        ("/hostedzone/HOSTED_ZONE/example.com/A", "example.com", "A"),
        ("/hostedzone/HOSTED_ZONE/ipv6.example.com/AAAA", "ipv6.example.com", "AAAA"),
        ("/hostedzone/HOSTED_ZONE/example.com/NS", "example.com", "NS"),
        (
            "/hostedzone/HOSTED_ZONE/_b6e76e6a1b6853211abcdef123454.example.com/CNAME",
            "_b6e76e6a1b6853211abcdef123454.example.com",
            "CNAME",
        ),
        (
            "/hostedzone/HOSTED_ZONE/elbv2.example.com/ALIAS",
            "elbv2.example.com",
            "ALIAS",
        ),
        (
            "/hostedzone/HOSTED_ZONE/aliasv6.example.com/ALIAS_AAAA",
            "aliasv6.example.com",
            "ALIAS",
        ),
        (
            "/hostedzone/HOSTED_ZONE/www.example.com/WEIGHTED_CNAME",
            "www.example.com",
            "CNAME",
        ),
        (
            "/hostedzone/HOSTED_ZONE/_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws/A",
            "_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws",
            "A",
        ),
        (
            "/hostedzone/HOSTED_ZONE/hello.what.example.com/A",
            "hello.what.example.com",
            "A",
        ),
    }, "DNS records don't exist"

    # DNS zones -- AWS account
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSDNSZone",
        "zoneid",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "/hostedzone/HOSTED_ZONE")
    }, "DNS zones aren't connected to AWS account"

    # DNS zones -- AWS account
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "AWSDNSZone",
        "zoneid",
        "MEMBER_OF_DNS_ZONE",
        rel_direction_right=True,
    ) == {
        ("/hostedzone/HOSTED_ZONE/example.com/A", "/hostedzone/HOSTED_ZONE"),
        ("/hostedzone/HOSTED_ZONE/example.com/NS", "/hostedzone/HOSTED_ZONE"),
        (
            "/hostedzone/HOSTED_ZONE/_b6e76e6a1b6853211abcdef123454.example.com/CNAME",
            "/hostedzone/HOSTED_ZONE",
        ),
        ("/hostedzone/HOSTED_ZONE/elbv2.example.com/ALIAS", "/hostedzone/HOSTED_ZONE"),
        (
            "/hostedzone/HOSTED_ZONE/aliasv6.example.com/ALIAS_AAAA",
            "/hostedzone/HOSTED_ZONE",
        ),
        (
            "/hostedzone/HOSTED_ZONE/www.example.com/WEIGHTED_CNAME",
            "/hostedzone/HOSTED_ZONE",
        ),
        (
            "/hostedzone/HOSTED_ZONE/_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws/A",
            "/hostedzone/HOSTED_ZONE",
        ),
        (
            "/hostedzone/HOSTED_ZONE/hello.what.example.com/A",
            "/hostedzone/HOSTED_ZONE",
        ),
        ("/hostedzone/HOSTED_ZONE/ipv6.example.com/AAAA", "/hostedzone/HOSTED_ZONE"),
    }, "DNS records aren't connected to DNS zones"

    assert check_nodes(neo4j_session, "NameServer", ["id", "name"]) == {
        (
            "ec2-1-2-3-4.us-east-2.compute.amazonaws.com",
            "ec2-1-2-3-4.us-east-2.compute.amazonaws.com",
        ),
    }, "Name servers don't exist"

    # DNS records -- Name servers
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "NameServer",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (
            "/hostedzone/HOSTED_ZONE/example.com/NS",
            "ec2-1-2-3-4.us-east-2.compute.amazonaws.com",
        ),
    }, "DNS records don't point to name servers"

    # DNS zones -- Name servers
    assert check_rels(
        neo4j_session,
        "AWSDNSZone",
        "zoneid",
        "NameServer",
        "id",
        "NAMESERVER",
        rel_direction_right=True,
    ) == {
        ("/hostedzone/HOSTED_ZONE", "ec2-1-2-3-4.us-east-2.compute.amazonaws.com"),
    }, "DNS zones don't point to name servers"

    # DNS records -- DNS records
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "AWSDNSRecord",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (
            "/hostedzone/HOSTED_ZONE/_b6e76e6a1b6853211abcdef123454.example.com/CNAME",
            "/hostedzone/HOSTED_ZONE/_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws/A",
        ),
        (
            "/hostedzone/HOSTED_ZONE/www.example.com/WEIGHTED_CNAME",
            "/hostedzone/HOSTED_ZONE/hello.what.example.com/A",
        ),
    }, "DNS records don't point to other DNS records"

    # DNS records -- IP addresses
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "Ip",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        ("/hostedzone/HOSTED_ZONE/example.com/A", "1.2.3.4"),
        (
            "/hostedzone/HOSTED_ZONE/_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws/A",
            "5.6.7.8",
        ),
        ("/hostedzone/HOSTED_ZONE/hello.what.example.com/A", "9.10.11.12"),
        ("/hostedzone/HOSTED_ZONE/ipv6.example.com/AAAA", "2001:db8::1"),
        ("/hostedzone/HOSTED_ZONE/ipv6.example.com/AAAA", "2001:db8::2"),
    }, "DNS records don't point to IP addresses"


@patch.object(
    cartography.intel.aws.route53,
    "get_zones",
    return_value=GET_ZONES_SAMPLE_RESPONSE,
)
def test_sync_route53_with_existing_resources(mock_get_zones, neo4j_session):
    """
    Test that Route53 sync correctly links DNS records to existing AWS resources
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Pre-create some AWS resources that DNS records might point to
    neo4j_session.run(
        """
        MERGE (lb:LoadBalancerV2 {id: "myawesomeloadbalancer.amazonaws.com", dnsname: "myawesomeloadbalancer.amazonaws.com"})
        SET lb.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (ec2:EC2Instance {id: "i-1234567890abcdef0", publicdnsname: "hello.what.example.com"})
        SET ec2.lastupdated = $update_tag
        """,
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

    # Assert
    # DNS records -- LoadBalancerV2
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "LoadBalancerV2",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (
            "/hostedzone/HOSTED_ZONE/elbv2.example.com/ALIAS",
            "myawesomeloadbalancer.amazonaws.com",
        ),
    }, "DNS records don't point to LoadBalancerV2"

    # DNS records -- EC2 instances
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "EC2Instance",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (
            "/hostedzone/HOSTED_ZONE/www.example.com/WEIGHTED_CNAME",
            "i-1234567890abcdef0",
        ),
    }, "DNS records don't point to EC2 instances"


@patch.object(
    cartography.intel.aws.route53,
    "get_zones",
    return_value=GET_ZONES_SAMPLE_RESPONSE,
)
def test_sync_route53_cleanup(mock_get_zones, neo4j_session):
    """
    Test that Route53 sync properly cleans up stale data
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Pre-create some stale DNS records with old update tag
    neo4j_session.run(
        """
        MERGE (record:AWSDNSRecord {id: "stale-record", name: "stale.example.com", lastupdated: 999999})
        MERGE (zone:AWSDNSZone {zoneid: "/hostedzone/HOSTED_ZONE", lastupdated: 999999})
        MERGE (account:AWSAccount {id: $account_id, lastupdated: $update_tag})
        MERGE (record)-[:MEMBER_OF_DNS_ZONE]->(zone)
        MERGE (record)<-[:RESOURCE]-(account)
        MERGE (account)-[:RESOURCE]->(zone)
        """,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - Run sync with new update tag
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Stale record should be cleaned up (not present)
    assert check_nodes(neo4j_session, "AWSDNSRecord", ["id"]) == {
        ("/hostedzone/HOSTED_ZONE/example.com/A",),
        ("/hostedzone/HOSTED_ZONE/ipv6.example.com/AAAA",),
        ("/hostedzone/HOSTED_ZONE/example.com/NS",),
        ("/hostedzone/HOSTED_ZONE/_b6e76e6a1b6853211abcdef123454.example.com/CNAME",),
        ("/hostedzone/HOSTED_ZONE/elbv2.example.com/ALIAS",),
        ("/hostedzone/HOSTED_ZONE/aliasv6.example.com/ALIAS_AAAA",),
        ("/hostedzone/HOSTED_ZONE/www.example.com/WEIGHTED_CNAME",),
        (
            "/hostedzone/HOSTED_ZONE/_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws/A",
        ),
        ("/hostedzone/HOSTED_ZONE/hello.what.example.com/A",),
    }


@patch.object(
    cartography.intel.aws.route53,
    "get_zones",
    return_value=GET_ZONES_WITH_SUBZONE,
)
def test_sync_route53_sub_zones(mock_get_zones, neo4j_session):
    """
    Test that Route53 sync correctly creates sub-zone relationships
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Sub-zone relationship should be created
    expected_rels = {
        ("/hostedzone/PARENT_ZONE", "/hostedzone/SUB_ZONE"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AWSDNSZone",
        "zoneid",
        "AWSDNSZone",
        "zoneid",
        "SUBZONE",
        rel_direction_right=True,
    )
    assert actual_rels == expected_rels, "Sub-zone relationship should be created"
