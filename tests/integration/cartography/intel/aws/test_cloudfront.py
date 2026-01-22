"""
Integration tests for AWS CloudFront intel module.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudfront
from cartography.intel.aws.cloudfront import sync
from tests.data.aws import cloudfront as test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789


def _cleanup_cloudfront(neo4j_session):
    """Remove CloudFront nodes from previous tests."""
    neo4j_session.run("MATCH (n:CloudFrontDistribution) DETACH DELETE n")


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
        "MERGE (:S3Bucket {name: $name})",
        name="my-test-bucket",
    )

    # Pre-create ACM certificate node to test relationship
    neo4j_session.run(
        "MERGE (:ACMCertificate {arn: $arn})",
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
        "CloudFrontDistribution",
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
        "CloudFrontDistribution",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7",
        ),
    }

    # Verify relationship to S3Bucket
    assert check_rels(
        neo4j_session,
        "CloudFrontDistribution",
        "arn",
        "S3Bucket",
        "name",
        "SERVES_FROM",
        rel_direction_right=True,
    ) == {
        (
            f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7",
            "my-test-bucket",
        ),
    }

    # Verify relationship to ACMCertificate
    assert check_rels(
        neo4j_session,
        "CloudFrontDistribution",
        "arn",
        "ACMCertificate",
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
        "CloudFrontDistribution",
        ["distribution_id"],
    ) == {("E7F8G9H0I1J2K3",)}

    # Verify relationships to Lambda functions
    rels = check_rels(
        neo4j_session,
        "CloudFrontDistribution",
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
        "CloudFrontDistribution",
        ["distribution_id", "cloudfront_default_certificate", "geo_restriction_type"],
    ) == {("E9Z8Y7X6W5V4U3", True, "blacklist")}

    # Verify no S3 relationships (custom origin)
    assert (
        check_rels(
            neo4j_session,
            "CloudFrontDistribution",
            "arn",
            "S3Bucket",
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
    neo4j_session.run("MERGE (:S3Bucket {name: $name})", name="primary-bucket")
    neo4j_session.run("MERGE (:S3Bucket {name: $name})", name="backup-bucket")

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
        "CloudFrontDistribution",
        "arn",
        "S3Bucket",
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
        "CloudFrontDistribution",
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
        check_nodes(neo4j_session, "CloudFrontDistribution", ["distribution_id"])
        == set()
    )
