"""
Integration tests for AWS CloudFront intel module.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudfront
import cartography.intel.aws.ec2.load_balancer_v2s
import tests.data.aws.ec2.load_balancers
from cartography.intel.aws.cloudfront import sync
from tests.data.aws import cloudfront as test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"


def _cleanup_cloudfront(neo4j_session):
    """Remove CloudFront nodes from previous tests."""
    neo4j_session.run("MATCH (n:AWSCloudFrontDistribution) DETACH DELETE n")


@patch.object(
    cartography.intel.aws.cloudfront,
    "get_cloudfront_distributions",
    return_value=test_data.CLOUDFRONT_DISTRIBUTIONS,
)
def test_sync_cloudfront_basic(mock_get_distributions, neo4j_session):
    """Test syncing a basic CloudFront distribution with S3 origin."""
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Pre-create S3 bucket node to test relationship
    neo4j_session.run(
        "MERGE (:AWSS3Bucket {name: $name})",
        name="my-test-bucket",
    )

    # Pre-create ACM certificate node to test relationship
    neo4j_session.run(
        "MERGE (:AWSACMCertificate {arn: $arn})",
        arn=f"arn:aws:acm:us-east-1:{TEST_ACCOUNT_ID}:certificate/test-cert-1",
    )

    sync(
        neo4j_session,
        boto3_session,
        [
            "us-east-1"
        ],  # Note: CloudFront is global, but we pass regions for interface consistency
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Verify CloudFront distribution node was created
    assert check_nodes(
        neo4j_session,
        "AWSCloudFrontDistribution",
        ["arn", "distribution_id", "domain_name", "enabled"],
    ) == {
        (
            f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7",
            "E1A2B3C4D5E6F7",
            "d1234567890abc.cloudfront.net",
            True,
        ),
    }

    # Verify relationship to AWSAccount
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSCloudFrontDistribution",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7",
        ),
    }

    # Verify relationship to AWSS3Bucket
    assert check_rels(
        neo4j_session,
        "AWSCloudFrontDistribution",
        "arn",
        "AWSS3Bucket",
        "name",
        "SERVES_FROM",
        rel_direction_right=True,
    ) == {
        (
            f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7",
            "my-test-bucket",
        ),
    }

    # Verify relationship to AWSACMCertificate
    assert check_rels(
        neo4j_session,
        "AWSCloudFrontDistribution",
        "arn",
        "AWSACMCertificate",
        "arn",
        "USES_CERTIFICATE",
        rel_direction_right=True,
    ) == {
        (
            f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7",
            f"arn:aws:acm:us-east-1:{TEST_ACCOUNT_ID}:certificate/test-cert-1",
        ),
    }


@patch.object(
    cartography.intel.aws.cloudfront,
    "get_cloudfront_distributions",
    return_value=test_data.CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA,
)
def test_sync_cloudfront_with_lambda(mock_get_distributions, neo4j_session):
    """Test syncing a CloudFront distribution with Lambda@Edge."""
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Pre-create Lambda function nodes to test relationships
    neo4j_session.run(
        "MERGE (:AWSLambda {arn: $arn})",
        arn=f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:auth-at-edge:1",
    )
    neo4j_session.run(
        "MERGE (:AWSLambda {arn: $arn})",
        arn=f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:response-headers:2",
    )

    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Verify CloudFront distribution node was created
    assert check_nodes(
        neo4j_session,
        "AWSCloudFrontDistribution",
        ["distribution_id"],
    ) == {("E7F8G9H0I1J2K3",)}

    # Verify relationships to Lambda functions
    rels = check_rels(
        neo4j_session,
        "AWSCloudFrontDistribution",
        "arn",
        "AWSLambda",
        "arn",
        "USES_LAMBDA_EDGE",
        rel_direction_right=True,
    )

    assert len(rels) == 2
    assert (
        f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E7F8G9H0I1J2K3",
        f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:auth-at-edge:1",
    ) in rels
    assert (
        f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E7F8G9H0I1J2K3",
        f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:response-headers:2",
    ) in rels


@patch.object(
    cartography.intel.aws.cloudfront,
    "get_cloudfront_distributions",
    return_value=test_data.CLOUDFRONT_DISTRIBUTIONS_CUSTOM_ORIGIN,
)
def test_sync_cloudfront_custom_origin(mock_get_distributions, neo4j_session):
    """Test syncing a CloudFront distribution with custom (non-S3) origin."""
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Verify CloudFront distribution node was created with expected properties
    assert check_nodes(
        neo4j_session,
        "AWSCloudFrontDistribution",
        ["distribution_id", "cloudfront_default_certificate", "geo_restriction_type"],
    ) == {("E9Z8Y7X6W5V4U3", True, "blacklist")}

    # Verify no S3 relationships (custom origin)
    assert (
        check_rels(
            neo4j_session,
            "AWSCloudFrontDistribution",
            "arn",
            "AWSS3Bucket",
            "name",
            "SERVES_FROM",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.aws.cloudfront,
    "get_cloudfront_distributions",
    return_value=test_data.CLOUDFRONT_DISTRIBUTIONS_MULTI_ORIGIN,
)
def test_sync_cloudfront_multi_origin(mock_get_distributions, neo4j_session):
    """Test syncing a CloudFront distribution with multiple S3 origins."""
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Pre-create S3 bucket nodes
    neo4j_session.run("MERGE (:AWSS3Bucket {name: $name})", name="primary-bucket")
    neo4j_session.run("MERGE (:AWSS3Bucket {name: $name})", name="backup-bucket")

    # Pre-create Lambda function node (from cache behaviors)
    neo4j_session.run(
        "MERGE (:AWSLambda {arn: $arn})",
        arn=f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:backup-handler:1",
    )

    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Verify relationships to multiple S3 buckets
    s3_rels = check_rels(
        neo4j_session,
        "AWSCloudFrontDistribution",
        "arn",
        "AWSS3Bucket",
        "name",
        "SERVES_FROM",
        rel_direction_right=True,
    )

    assert len(s3_rels) == 2
    assert (
        f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E3T2R1Q0P9O8N7",
        "primary-bucket",
    ) in s3_rels
    assert (
        f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E3T2R1Q0P9O8N7",
        "backup-bucket",
    ) in s3_rels

    # Verify relationship to Lambda from cache behaviors
    assert check_rels(
        neo4j_session,
        "AWSCloudFrontDistribution",
        "arn",
        "AWSLambda",
        "arn",
        "USES_LAMBDA_EDGE",
        rel_direction_right=True,
    ) == {
        (
            f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E3T2R1Q0P9O8N7",
            f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:backup-handler:1",
        ),
    }


@patch.object(cartography.intel.aws.cloudfront, "get_cloudfront_distributions")
def test_sync_cloudfront_skips_govcloud(mock_get_distributions, neo4j_session):
    """
    CloudFront has no endpoint in AWS GovCloud (US), so a GovCloud account skips the
    module. The skip happens before cleanup, so it leaves existing data in place.
    """
    # Arrange
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    mock_get_distributions.return_value = test_data.CLOUDFRONT_DISTRIBUTIONS
    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )
    seeded = check_nodes(
        neo4j_session, "AWSCloudFrontDistribution", ["distribution_id", "lastupdated"]
    )
    new_update_tag = TEST_UPDATE_TAG + 1
    # A GovCloud sync that still fetched would load this distribution again with the new
    # update tag, which the assertion below would see.
    mock_get_distributions.return_value = test_data.CLOUDFRONT_DISTRIBUTIONS

    # Act
    sync(
        neo4j_session,
        boto3_session,
        ["us-gov-west-1", "us-gov-east-1"],
        TEST_ACCOUNT_ID,
        new_update_tag,
        {"UPDATE_TAG": new_update_tag, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert seeded
    assert (
        check_nodes(
            neo4j_session,
            "AWSCloudFrontDistribution",
            ["distribution_id", "lastupdated"],
        )
        == seeded
    )


@patch.object(
    cartography.intel.aws.cloudfront,
    "get_cloudfront_distributions",
    return_value=[],
)
def test_sync_cloudfront_empty(mock_get_distributions, neo4j_session):
    """Test syncing when there are no CloudFront distributions."""
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Verify no CloudFront distribution nodes created
    assert (
        check_nodes(neo4j_session, "AWSCloudFrontDistribution", ["distribution_id"])
        == set()
    )


@patch.object(
    cartography.intel.aws.cloudfront,
    "get_cloudfront_distributions",
    return_value=test_data.CLOUDFRONT_DISTRIBUTIONS_MULTI_ORIGIN,
)
def test_sync_cloudfront_persists_origin_endpoints_and_behavior_routing(
    mock_get_distributions, neo4j_session
):
    """origin_endpoints and the behavior lists must survive the schema loader.

    These are declared only in the property schema; anything not declared there is
    silently dropped on write, so a transform-level assertion cannot catch it.
    """
    # Arrange
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    node = neo4j_session.run(
        """
        MATCH (n:AWSCloudFrontDistribution {distribution_id: $id})
        RETURN n.origin_endpoints AS endpoints,
               n.behavior_path_patterns AS patterns,
               n.behavior_path_regexes AS path_regexes,
               n.behavior_target_origin_ids AS target_origin_ids,
               n.origin_id_domain_pairs AS id_domain_pairs,
               n.default_target_origin_id AS default_origin
        """,
        id="E3T2R1Q0P9O8N7",
    ).single()
    assert node is not None
    assert node["endpoints"] == [
        "backup-bucket.s3-website-us-west-2.amazonaws.com|/backup",
        "primary-bucket.s3.amazonaws.com|",
    ]
    assert node["patterns"] == ["/backup/*"]
    assert node["path_regexes"] == [
        cartography.intel.aws.cloudfront._path_pattern_to_regex("/backup/*")
    ]
    assert node["target_origin_ids"] == ["S3-backup"]
    assert node["id_domain_pairs"] == [
        "S3-backup|backup-bucket.s3-website-us-west-2.amazonaws.com",
        "S3-primary|primary-bucket.s3.amazonaws.com",
    ]
    assert node["default_origin"] == "S3-primary"


@patch.object(
    cartography.intel.aws.cloudfront,
    "get_cloudfront_distributions",
    return_value=test_data.CLOUDFRONT_DISTRIBUTIONS_ALB_ORIGIN,
)
def test_sync_cloudfront_alb_origin(mock_get_distributions, neo4j_session):
    """Test that a distribution with an ALB custom origin links to the load balancer."""
    # Arrange
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    alb_dns_name = tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA[0]["DNSName"]

    # Act
    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSCloudFrontDistribution",
        ["distribution_id"],
    ) == {("E9Z8Y7X6W5V4U3",)}
    # check_nodes() cannot return list-valued properties, so read the origin domain
    # names directly.
    records = neo4j_session.run(
        "MATCH (n:AWSCloudFrontDistribution) RETURN n.origin_domain_names AS names",
    )
    assert [record["names"] for record in records] == [
        sorted([alb_dns_name, "origin.backend.example.com"]),
    ]
    # Only the ALB origin gets a SERVES_FROM edge; the second custom origin has no
    # matching load balancer.
    assert check_rels(
        neo4j_session,
        "AWSCloudFrontDistribution",
        "distribution_id",
        "AWSLoadBalancerV2",
        "dnsname",
        "SERVES_FROM",
        rel_direction_right=True,
    ) == {("E9Z8Y7X6W5V4U3", alb_dns_name)}
    # This distribution has no S3 origins.
    assert (
        check_rels(
            neo4j_session,
            "AWSCloudFrontDistribution",
            "arn",
            "AWSS3Bucket",
            "name",
            "SERVES_FROM",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.aws.cloudfront,
    "get_cloudfront_distributions",
    return_value=test_data.CLOUDFRONT_DISTRIBUTIONS,
)
def test_sync_cloudfront_s3_origin_no_load_balancer_edge(
    mock_get_distributions, neo4j_session
):
    """Test that an S3-only distribution gets no SERVES_FROM edge to a load balancer."""
    # Arrange
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (:AWSS3Bucket {name: $name})",
        name="my-test-bucket",
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSCloudFrontDistribution",
        "arn",
        "AWSS3Bucket",
        "name",
        "SERVES_FROM",
        rel_direction_right=True,
    ) == {
        (
            f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7",
            "my-test-bucket",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSCloudFrontDistribution",
            "distribution_id",
            "AWSLoadBalancerV2",
            "dnsname",
            "SERVES_FROM",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(cartography.intel.aws.cloudfront, "get_cloudfront_distributions")
def test_sync_cloudfront_alb_origin_removed_cleans_stale_edge(
    mock_get_distributions, neo4j_session
):
    """Test that removing an ALB origin cleans up the stale SERVES_FROM edge."""
    # Arrange
    _cleanup_cloudfront(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    alb_dns_name = tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA[0]["DNSName"]
    mock_get_distributions.return_value = test_data.CLOUDFRONT_DISTRIBUTIONS_ALB_ORIGIN

    # Act
    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSCloudFrontDistribution",
        "distribution_id",
        "AWSLoadBalancerV2",
        "dnsname",
        "SERVES_FROM",
        rel_direction_right=True,
    ) == {("E9Z8Y7X6W5V4U3", alb_dns_name)}

    # Arrange: re-sync with the ALB origin removed under a new update tag.
    new_update_tag = TEST_UPDATE_TAG + 1
    mock_get_distributions.return_value = (
        test_data.CLOUDFRONT_DISTRIBUTIONS_ALB_ORIGIN_REMOVED
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        new_update_tag,
        {"UPDATE_TAG": new_update_tag, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "AWSCloudFrontDistribution",
            "distribution_id",
            "AWSLoadBalancerV2",
            "dnsname",
            "SERVES_FROM",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_nodes(
        neo4j_session,
        "AWSCloudFrontDistribution",
        ["distribution_id"],
    ) == {("E9Z8Y7X6W5V4U3",)}
    records = neo4j_session.run(
        "MATCH (n:AWSCloudFrontDistribution) RETURN n.origin_domain_names AS names",
    )
    assert [record["names"] for record in records] == [["origin.backend.example.com"]]
