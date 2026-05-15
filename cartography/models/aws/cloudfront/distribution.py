"""
CloudFront Distribution data model.

CloudFront is AWS's content delivery network (CDN) service that delivers
data, videos, applications, and APIs globally with low latency.

Based on AWS CloudFront list_distributions API response.
See: https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_ListDistributions.html
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CloudFrontDistributionNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS CloudFront Distribution nodes.

    Based on AWS CloudFront list_distributions API DistributionSummary response.
    """

    # Core identifiers
    id: PropertyRef = PropertyRef("ARN")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    distribution_id: PropertyRef = PropertyRef("Id", extra_index=True)
    etag: PropertyRef = PropertyRef("ETag")

    # Domain and naming
    domain_name: PropertyRef = PropertyRef("DomainName")
    aliases: PropertyRef = PropertyRef("Aliases")
    comment: PropertyRef = PropertyRef("Comment")

    # Status and configuration
    status: PropertyRef = PropertyRef("Status")
    enabled: PropertyRef = PropertyRef("Enabled")
    price_class: PropertyRef = PropertyRef("PriceClass")
    http_version: PropertyRef = PropertyRef("HttpVersion")
    is_ipv6_enabled: PropertyRef = PropertyRef("IsIPV6Enabled")
    staging: PropertyRef = PropertyRef("Staging")
    last_modified_time: PropertyRef = PropertyRef("LastModifiedTime")

    # Cache behavior configuration
    viewer_protocol_policy: PropertyRef = PropertyRef("ViewerProtocolPolicy")

    # SSL/TLS configuration (from ViewerCertificate)
    acm_certificate_arn: PropertyRef = PropertyRef("ACMCertificateArn")
    cloudfront_default_certificate: PropertyRef = PropertyRef(
        "CloudFrontDefaultCertificate",
    )
    minimum_protocol_version: PropertyRef = PropertyRef("MinimumProtocolVersion")
    ssl_support_method: PropertyRef = PropertyRef("SSLSupportMethod")
    iam_certificate_id: PropertyRef = PropertyRef("IAMCertificateId")

    # Geographic restrictions (from Restrictions.GeoRestriction)
    geo_restriction_type: PropertyRef = PropertyRef("GeoRestrictionType")
    geo_restriction_locations: PropertyRef = PropertyRef("GeoRestrictionLocations")

    # WAF integration
    web_acl_id: PropertyRef = PropertyRef("WebACLId")

    # Cartography standard fields
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFrontDistributionToAWSAccountRelProperties(CartographyRelProperties):
    """Properties for the relationship between CloudFrontDistribution and AWSAccount."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFrontDistributionToAWSAccountRel(CartographyRelSchema):
    """
    Defines the relationship from CloudFrontDistribution to AWSAccount.

    (:AWSAccount)-[:RESOURCE]->(:CloudFrontDistribution)
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudFrontDistributionToAWSAccountRelProperties = (
        CloudFrontDistributionToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudFrontDistributionToS3BucketRelProperties(CartographyRelProperties):
    """Properties for the relationship between CloudFrontDistribution and S3Bucket."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFrontDistributionToS3BucketRel(CartographyRelSchema):
    """
    Defines the relationship from CloudFrontDistribution to S3Bucket.

    Created when a CloudFront distribution has S3 bucket origins.
    (:CloudFrontDistribution)-[:SERVES_FROM]->(:S3Bucket)
    """

    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("s3_origin_bucket_names", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SERVES_FROM"
    properties: CloudFrontDistributionToS3BucketRelProperties = (
        CloudFrontDistributionToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class CloudFrontDistributionToACMCertificateRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between CloudFrontDistribution and ACMCertificate.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFrontDistributionToACMCertificateRel(CartographyRelSchema):
    """
    Defines the relationship from CloudFrontDistribution to ACMCertificate.

    Created when a CloudFront distribution uses an ACM certificate for HTTPS.
    (:CloudFrontDistribution)-[:USES_CERTIFICATE]->(:ACMCertificate)
    """

    target_node_label: str = "ACMCertificate"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("ACMCertificateArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CERTIFICATE"
    properties: CloudFrontDistributionToACMCertificateRelProperties = (
        CloudFrontDistributionToACMCertificateRelProperties()
    )


@dataclass(frozen=True)
class CloudFrontDistributionToLambdaRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between CloudFrontDistribution and AWSLambda.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFrontDistributionToLambdaRel(CartographyRelSchema):
    """
    Defines the relationship from CloudFrontDistribution to AWSLambda.

    Created when a CloudFront distribution has Lambda@Edge function associations.
    (:CloudFrontDistribution)-[:USES_LAMBDA_EDGE]->(:AWSLambda)
    """

    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("lambda_function_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LAMBDA_EDGE"
    properties: CloudFrontDistributionToLambdaRelProperties = (
        CloudFrontDistributionToLambdaRelProperties()
    )


@dataclass(frozen=True)
class CloudFrontDistributionSchema(CartographyNodeSchema):
    """Schema for AWS CloudFront Distribution nodes."""

    label: str = "CloudFrontDistribution"
    properties: CloudFrontDistributionNodeProperties = (
        CloudFrontDistributionNodeProperties()
    )
    sub_resource_relationship: CloudFrontDistributionToAWSAccountRel = (
        CloudFrontDistributionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudFrontDistributionToS3BucketRel(),
            CloudFrontDistributionToACMCertificateRel(),
            CloudFrontDistributionToLambdaRel(),
        ],
    )
