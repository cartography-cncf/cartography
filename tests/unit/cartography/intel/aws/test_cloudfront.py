"""
Unit tests for AWS CloudFront intel module.
"""

from cartography.intel.aws import cloudfront
from tests.data.aws import cloudfront as test_data


def test_extract_s3_bucket_name_standard():
    """Test extracting S3 bucket name from standard S3 domain."""
    assert (
        cloudfront._extract_s3_bucket_name("my-bucket.s3.amazonaws.com") == "my-bucket"
    )


def test_extract_s3_bucket_name_regional():
    """Test extracting S3 bucket name from regional S3 domain."""
    assert (
        cloudfront._extract_s3_bucket_name("my-bucket.s3.us-east-1.amazonaws.com")
        == "my-bucket"
    )


def test_extract_s3_bucket_name_website():
    """Test extracting S3 bucket name from S3 website domain."""
    assert (
        cloudfront._extract_s3_bucket_name(
            "my-bucket.s3-website-us-east-1.amazonaws.com"
        )
        == "my-bucket"
    )


def test_extract_s3_bucket_name_non_s3():
    """Test that non-S3 domains return None."""
    assert cloudfront._extract_s3_bucket_name("origin.backend.example.com") is None
    assert cloudfront._extract_s3_bucket_name("api.example.com") is None


def test_transform_cloudfront_distributions_basic():
    """Test basic transformation of CloudFront distributions."""
    result = cloudfront.transform_cloudfront_distributions(
        test_data.CLOUDFRONT_DISTRIBUTIONS,
    )

    assert len(result) == 1
    dist = result[0]

    # Verify core identifiers
    assert dist["Id"] == "E1A2B3C4D5E6F7"
    assert (
        dist["ARN"]
        == f"arn:aws:cloudfront::{test_data.TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7"
    )
    assert dist["ETag"] == "ABCDEF123456"

    # Verify domain and naming
    assert dist["DomainName"] == "d1234567890abc.cloudfront.net"
    assert dist["Aliases"] == ["www.example.com", "example.com"]
    assert dist["Comment"] == "Test distribution with S3 origin"

    # Verify status and configuration
    assert dist["Status"] == "Deployed"
    assert dist["Enabled"] is True
    assert dist["PriceClass"] == "PriceClass_100"
    assert dist["HttpVersion"] == "http2"
    assert dist["IsIPV6Enabled"] is True
    assert dist["Staging"] is False

    # Verify cache behavior
    assert dist["ViewerProtocolPolicy"] == "redirect-to-https"

    # Verify SSL/TLS configuration
    assert (
        dist["ACMCertificateArn"]
        == f"arn:aws:acm:us-east-1:{test_data.TEST_ACCOUNT_ID}:certificate/test-cert-1"
    )
    assert dist["CloudFrontDefaultCertificate"] is False
    assert dist["MinimumProtocolVersion"] == "TLSv1.2_2021"
    assert dist["SSLSupportMethod"] == "sni-only"

    # Verify geo restrictions
    assert dist["GeoRestrictionType"] == "whitelist"
    assert dist["GeoRestrictionLocations"] == ["US", "CA"]

    # Verify S3 origin extraction
    assert dist["s3_origin_bucket_names"] == ["my-test-bucket"]

    # Verify no Lambda associations
    assert "lambda_function_arns" not in dist


def test_transform_cloudfront_distributions_with_lambda():
    """Test transformation of CloudFront distributions with Lambda@Edge."""
    result = cloudfront.transform_cloudfront_distributions(
        test_data.CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA,
    )

    assert len(result) == 1
    dist = result[0]

    # Verify Lambda function ARNs extracted
    assert "lambda_function_arns" in dist
    lambda_arns = dist["lambda_function_arns"]
    assert len(lambda_arns) == 2
    assert (
        f"arn:aws:lambda:us-east-1:{test_data.TEST_ACCOUNT_ID}:function:auth-at-edge:1"
        in lambda_arns
    )
    assert (
        f"arn:aws:lambda:us-east-1:{test_data.TEST_ACCOUNT_ID}:function:response-headers:2"
        in lambda_arns
    )

    # Verify S3 origin extracted (regional domain format)
    assert dist["s3_origin_bucket_names"] == ["api-bucket"]

    # Verify WebACL is captured
    assert (
        dist["WebACLId"]
        == f"arn:aws:wafv2:us-east-1:{test_data.TEST_ACCOUNT_ID}:global/webacl/test-acl/abc123"
    )


def test_transform_cloudfront_distributions_custom_origin():
    """Test transformation of CloudFront distributions with custom (non-S3) origin."""
    result = cloudfront.transform_cloudfront_distributions(
        test_data.CLOUDFRONT_DISTRIBUTIONS_CUSTOM_ORIGIN,
    )

    assert len(result) == 1
    dist = result[0]

    # Verify no S3 origins extracted (custom origin)
    assert "s3_origin_bucket_names" not in dist

    # Verify CloudFront default certificate
    assert dist["CloudFrontDefaultCertificate"] is True
    assert dist["ACMCertificateArn"] is None

    # Verify geo restriction
    assert dist["GeoRestrictionType"] == "blacklist"
    assert dist["GeoRestrictionLocations"] == ["RU"]

    # Verify empty aliases
    assert dist["Aliases"] is None


def test_transform_cloudfront_distributions_multi_origin():
    """Test transformation of CloudFront distributions with multiple S3 origins."""
    result = cloudfront.transform_cloudfront_distributions(
        test_data.CLOUDFRONT_DISTRIBUTIONS_MULTI_ORIGIN,
    )

    assert len(result) == 1
    dist = result[0]

    # Verify multiple S3 origins extracted
    assert "s3_origin_bucket_names" in dist
    bucket_names = dist["s3_origin_bucket_names"]
    assert len(bucket_names) == 2
    assert "primary-bucket" in bucket_names
    assert "backup-bucket" in bucket_names

    # Verify Lambda from cache behaviors extracted
    assert "lambda_function_arns" in dist
    lambda_arns = dist["lambda_function_arns"]
    assert len(lambda_arns) == 1
    assert (
        f"arn:aws:lambda:us-east-1:{test_data.TEST_ACCOUNT_ID}:function:backup-handler:1"
        in lambda_arns
    )


def test_transform_cloudfront_distributions_empty():
    """Test transformation with empty input."""
    result = cloudfront.transform_cloudfront_distributions([])
    assert result == []


def test_extract_lambda_arns_from_cache_behavior():
    """Test extracting Lambda ARNs from cache behavior."""
    cache_behavior = {
        "LambdaFunctionAssociations": {
            "Quantity": 2,
            "Items": [
                {
                    "LambdaFunctionARN": "arn:aws:lambda:us-east-1:123456789012:function:test1:1",
                    "EventType": "viewer-request",
                },
                {
                    "LambdaFunctionARN": "arn:aws:lambda:us-east-1:123456789012:function:test2:2",
                    "EventType": "origin-response",
                },
            ],
        },
    }

    arns = cloudfront._extract_lambda_arns_from_cache_behavior(cache_behavior)
    assert len(arns) == 2
    assert "arn:aws:lambda:us-east-1:123456789012:function:test1:1" in arns
    assert "arn:aws:lambda:us-east-1:123456789012:function:test2:2" in arns


def test_extract_lambda_arns_from_cache_behavior_empty():
    """Test extracting Lambda ARNs when there are none."""
    cache_behavior = {
        "LambdaFunctionAssociations": {"Quantity": 0},
    }

    arns = cloudfront._extract_lambda_arns_from_cache_behavior(cache_behavior)
    assert arns == []


def test_extract_lambda_arns_from_cache_behavior_missing():
    """Test extracting Lambda ARNs when key is missing."""
    cache_behavior = {}

    arns = cloudfront._extract_lambda_arns_from_cache_behavior(cache_behavior)
    assert arns == []
