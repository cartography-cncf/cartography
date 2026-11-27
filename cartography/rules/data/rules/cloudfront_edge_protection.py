"""
AWS CloudFront WAF association and geographic restrictions

Distributions with no WAF web ACL and distributions with no geographic
restriction. Enabled distributions only.

The WAF check tests the presence of web_acl_id only. It cannot confirm the
ACL's rules do anything useful, and a CloudFront-scoped web ACL is a separate
WAFv2 object rather than a per-distribution association, so an empty id is
the only signal available.

No collector change is required: every property and relationship used
here is synced by the existing CloudFront module. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsCloudfrontGeoRestrictionsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    distribution_id: str | None = None
    domain_name: str | None = None
    geo_restriction_type: str | None = None
    geo_restriction_locations: str | None = None


_aws_cloudfront_geo_restrictions_fact = Fact(
    id="aws_cloudfront_geo_restrictions_fact",
    name="Distribution without geo restriction",
    description="Distributions whose geo_restriction_type is 'none' or null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.geo_restriction_type IS NULL OR d.geo_restriction_type = 'none')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.geo_restriction_type AS geo_restriction_type,
               d.geo_restriction_locations AS geo_restriction_locations

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.geo_restriction_type IS NULL OR d.geo_restriction_type = 'none')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.geo_restriction_type AS geo_restriction_type,
               d.geo_restriction_locations AS geo_restriction_locations

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.geo_restriction_type IS NULL OR d.geo_restriction_type = 'none')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.geo_restriction_type AS geo_restriction_type,
               d.geo_restriction_locations AS geo_restriction_locations

    """,
    asset_label="AWSCloudFrontDistribution",
    asset_id_field="distribution_id",
    identity_fields=("account_id", "account", "distribution_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudfront_geo_restrictions = Rule(
    id="aws_cloudfront_geo_restrictions",
    name="CloudFront Geo Restriction Disabled",
    description="CloudFront distribution with geo_restriction_type 'none' or null: no geographic allowlist/blocklist configured. Geo restrictions help limit content distribution to intended jurisdictions. Enabled distributions only.",
    output_model=AwsCloudfrontGeoRestrictionsOutput,
    facts=(_aws_cloudfront_geo_restrictions_fact,),
    tags=("cloudfront", "hygiene", "cspm", "low"),
    version="0.1.0",
)


class AwsCloudfrontWafAttachedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    distribution_id: str | None = None
    distribution_arn: str | None = None
    web_acl_id: str | None = None


_aws_cloudfront_waf_attached_fact = Fact(
    id="aws_cloudfront_waf_attached_fact",
    name="CloudFront no WAF ACL",
    description="Distributions with web_acl_id null/empty.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true AND (d.web_acl_id IS NULL OR d.web_acl_id = '')
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn, d.web_acl_id AS web_acl_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true AND (d.web_acl_id IS NULL OR d.web_acl_id = '')
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn, d.web_acl_id AS web_acl_id

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true AND (d.web_acl_id IS NULL OR d.web_acl_id = '')
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn, d.web_acl_id AS web_acl_id

    """,
    asset_label="AWSCloudFrontDistribution",
    asset_id_field="distribution_id",
    identity_fields=("account_id", "account", "distribution_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudfront_waf_attached = Rule(
    id="aws_cloudfront_waf_attached",
    name="CloudFront WAF Web ACL Attached",
    description="CloudFront distribution has no AWS WAF web ACL associated (web_acl_id null or empty). Presence/absence of the association id only; the WAF web ACL itself is not a synced module. Enabled distributions only.",
    output_model=AwsCloudfrontWafAttachedOutput,
    facts=(_aws_cloudfront_waf_attached_fact,),
    tags=("security", "cloudfront", "attack_surface", "cspm"),
    version="0.1.0",
)
