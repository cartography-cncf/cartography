"""
AWS CloudFront viewer protocol policy

Distributions whose default cache behavior allows plaintext HTTP viewers.

viewer_protocol_policy is extracted from DefaultCacheBehavior only, so
per-behavior overrides are invisible: a distribution whose default allows
HTTP but whose other behaviors redirect is reported, and the reverse is not.
Origin-side protocol policy is not synced at all, so this says nothing about
the CloudFront-to-origin hop.

No collector change is required: every property and relationship used
here is synced by the existing CloudFront module. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsCloudfrontHttpsViewerPolicyOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    distribution_id: str | None = None
    distribution_arn: str | None = None
    viewer_protocol_policy: str | None = None


_aws_cloudfront_https_viewer_policy_fact = Fact(
    id="aws_cloudfront_https_viewer_policy_fact",
    name="CloudFront allow-all viewer policy",
    description="Distributions with viewer_protocol_policy allow-all/null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.viewer_protocol_policy IS NULL OR d.viewer_protocol_policy = 'allow-all')
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn,
               d.viewer_protocol_policy AS viewer_protocol_policy

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.viewer_protocol_policy IS NULL OR d.viewer_protocol_policy = 'allow-all')
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn,
               d.viewer_protocol_policy AS viewer_protocol_policy

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.viewer_protocol_policy IS NULL OR d.viewer_protocol_policy = 'allow-all')
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn,
               d.viewer_protocol_policy AS viewer_protocol_policy

    """,
    asset_label="AWSCloudFrontDistribution",
    asset_id_field="distribution_id",
    identity_fields=("account_id", "account", "distribution_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudfront_https_viewer_policy = Rule(
    id="aws_cloudfront_https_viewer_policy",
    name="CloudFront HTTPS Viewer Policy",
    description="CloudFront distribution default cache behavior has viewer_protocol_policy 'allow-all' (or unset), permitting plaintext HTTP viewer connections instead of HTTPS-only or redirect-to-HTTPS. Enabled distributions only.",
    output_model=AwsCloudfrontHttpsViewerPolicyOutput,
    facts=(_aws_cloudfront_https_viewer_policy_fact,),
    tags=("security", "cloudfront", "encryption", "cspm"),
    version="0.1.0",
)
